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
    ):
        super().__init__()
        self.n_sectors = int(n_sectors)
        self.aux_horizons = tuple(int(h) for h in aux_horizons)
        self.yaw_aux_steps = int(yaw_aux_steps)
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

    def forward(self, curr, goal, ctx=None):
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
        if self.out_aux is not None:
            aux = [head(feat) for head in self.out_aux]
            if self.sector is None:
                if yaw_pred is not None:
                    return direction, kappa, aux, yaw_pred
                return direction, kappa, aux
            return direction, kappa, aux, self.sector(feat)
        if self.sector is not None:
            return direction, kappa, self.sector(feat)
        if yaw_pred is not None:
            return direction, kappa, yaw_pred
        return direction, kappa
