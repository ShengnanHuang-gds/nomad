import torch
import torch.nn as nn

from vint_train.models.nomad.nomad import GoalDirectionHead


class PairTokenHead(nn.Module):
    """Current/goal (and optional context) DINO tokens read jointly.

    When n_sectors > 0, also predicts a discrete bearing sector from CLS
    (e.g. 3 = left / center / right). Callers that only need bearing can
    take outputs[:2].
    """

    def __init__(
        self,
        dim_in,
        n_tokens,
        width=256,
        layers=4,
        heads=8,
        dropout=0.1,
        context=0,
        n_sectors=0,
        aux_horizons=(),
        yaw_aux_steps=0,
        path_steps=0,
        path_mlp=0,
        path_residual=0,
        path_spatial="",
        odom_dim=0,
        path_rot=False,
    ):
        super().__init__()
        self.n_sectors = int(n_sectors)
        self.aux_horizons = tuple(int(h) for h in aux_horizons)
        self.yaw_aux_steps = int(yaw_aux_steps)
        self.path_steps = int(path_steps)
        self.path_mlp = int(path_mlp)
        self.path_residual = int(path_residual)
        self.path_spatial = (path_spatial or "").strip().lower()
        self.odom_dim = int(odom_dim)
        self.path_rot_on = bool(path_rot) and self.odom_dim > 0
        self.proj = nn.Sequential(nn.LayerNorm(dim_in), nn.Linear(dim_in, width))
        self.pos = nn.Parameter(torch.zeros(1, n_tokens, width))
        self.kind = nn.Parameter(torch.zeros(2 + context, width))
        self.cls = nn.Parameter(torch.zeros(1, 1, width))
        for p in (self.pos, self.kind, self.cls):
            nn.init.trunc_normal_(p, std=0.02)
        layer = nn.TransformerEncoderLayer(
            width, heads, 4 * width, dropout, activation="gelu", batch_first=True, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(width)
        self.out = GoalDirectionHead(width)
        self.out_aux = (
            nn.ModuleList([GoalDirectionHead(width) for _ in self.aux_horizons])
            if self.aux_horizons
            else None
        )
        self.sector = nn.Linear(width, self.n_sectors) if self.n_sectors > 0 else None
        self.yaw_aux = nn.Linear(width, self.yaw_aux_steps) if self.yaw_aux_steps > 0 else None
        self.path_res = None
        self.path_rot = (
            nn.Linear(self.odom_dim, 1) if self.path_rot_on else None
        )
        if self.path_rot is not None:
            nn.init.zeros_(self.path_rot.weight)
            nn.init.zeros_(self.path_rot.bias)
        odom_in = 0 if self.path_rot_on else self.odom_dim
        path_in = width * (3 if self.path_spatial == "lcr" else 1) + odom_in
        if self.path_steps > 0:
            out_dim = self.path_steps * 2
            if self.path_mlp > 0:
                h = self.path_mlp
                self.path_head = nn.Sequential(
                    nn.LayerNorm(path_in),
                    nn.Linear(path_in, h),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(h, h),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(h, out_dim),
                )
            else:
                self.path_head = nn.Linear(path_in, out_dim)
            if self.path_residual > 0:
                h = self.path_residual
                self.path_res = nn.Sequential(
                    nn.LayerNorm(width),
                    nn.Linear(width, h),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(h, h),
                    nn.GELU(),
                    nn.Dropout(dropout),
                    nn.Linear(h, out_dim),
                )
                nn.init.zeros_(self.path_res[-1].weight)
                nn.init.zeros_(self.path_res[-1].bias)
        else:
            self.path_head = None

    def forward(self, curr, goal, ctx=None, odom=None):
        parts = [self.cls.expand(len(curr), -1, -1)]
        parts.append(self.proj(curr) + self.pos + self.kind[0])
        parts.append(self.proj(goal) + self.pos + self.kind[1])
        if ctx is not None:
            for j in range(ctx.shape[1]):
                parts.append(self.proj(ctx[:, j]) + self.pos + self.kind[2 + j])
        x = self.encoder(torch.cat(parts, dim=1))
        feat = self.norm(x[:, 0])
        direction, kappa = self.out(feat)
        yaw_pred = self.yaw_aux(feat) if self.yaw_aux is not None else None
        extras = []
        if self.out_aux is not None:
            extras.append([h(feat) for h in self.out_aux])
        if self.sector is not None:
            extras.append(self.sector(feat))
        if yaw_pred is not None:
            extras.append(yaw_pred)
        if self.path_head is not None:
            path_xy = self.path_head(self._path_feat(x, feat, odom))
            if self.path_res is not None:
                path_xy = path_xy + self.path_res(feat)
            path_xy = path_xy.view(-1, self.path_steps, 2)
            path_xy = self._rotate_path(path_xy, odom)
            extras.append(path_xy)
        if extras:
            return (direction, kappa, *extras)
        return direction, kappa

    def _path_feat(self, x, feat, odom=None):
        vis = feat
        if self.path_spatial == "lcr":
            n_tok = int(self.pos.shape[1])
            patches = x[:, 2 : 1 + n_tok]
            b, n_patch, width = patches.shape
            gw = 8
            if n_patch % gw != 0:
                raise RuntimeError(f"lcr readout needs 8-wide patch grid, got {n_patch} tokens")
            gh = n_patch // gw
            grid = patches.reshape(b, gh, gw, width)
            left = self.norm(grid[:, :, :3].mean(dim=(1, 2)))
            mid = self.norm(grid[:, :, 3:5].mean(dim=(1, 2)))
            right = self.norm(grid[:, :, 5:].mean(dim=(1, 2)))
            vis = torch.cat([left, mid, right], dim=-1)
        if self.odom_dim <= 0 or self.path_rot_on:
            return vis
        if odom is None:
            odom = vis.new_zeros(vis.shape[0], self.odom_dim)
        else:
            odom = odom.float()
            if odom.shape[-1] != self.odom_dim:
                raise RuntimeError(f"odom width {tuple(odom.shape)} != odom_dim {self.odom_dim}")
        return torch.cat([vis, odom], dim=-1)

    def _rotate_path(self, path_xy, odom):
        if self.path_rot is None:
            return path_xy
        if odom is None:
            odom = path_xy.new_zeros(path_xy.shape[0], self.odom_dim)
        ang = self.path_rot(odom.float()).reshape(-1, 1)
        c, s = torch.cos(ang), torch.sin(ang)
        x, y = path_xy[..., 0], path_xy[..., 1]
        return torch.stack([c * x - s * y, s * x + c * y], dim=-1)
