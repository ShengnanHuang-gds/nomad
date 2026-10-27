import torch
import torch.nn as nn

GEO_DIM = 3  # appended to the UNet condition: x, y (waypoint units) and the bearing std (radians)
MAX_ANGLE_STD = 2.0  # about a uniform bearing; used for shuffled positions and as the clip


class NoMaDGeo(nn.Module):
    """NoMaD whose diffusion condition also gets an estimated goal position.

    nomad: a NoMaD whose noise_pred_net takes encoding_size + GEO_DIM conditions.
    dir_head: PairTokenHead on DINOv2 tokens of the current and goal frames.
    The distance comes from nomad's own distance head, the bearing from dir_head.
    DINOv2 itself is not a member: training reads cached tokens.
    """

    def __init__(self, nomad, dir_head):
        super().__init__()
        self.nomad = nomad
        self.dir_head = dir_head

    def forward(self, func_name, **kwargs):
        if func_name == "dir_head":
            return self.dir_head(kwargs["curr_tokens"], kwargs["goal_tokens"])
        return self.nomad(func_name, **kwargs)

    @staticmethod
    def angle_std(kappa):
        return kappa.clamp(min=1e-6).rsqrt().clamp(max=MAX_ANGLE_STD)

    def estimate_goal(self, obsgoal_cond, curr_tokens, goal_tokens):
        """Return position [B, 2] in waypoint units, bearing std [B], direction [B, 2], kappa [B], steps [B]."""
        steps = self.nomad("dist_pred_net", obsgoal_cond=obsgoal_cond).squeeze(-1).clamp(min=0.0)
        dir_out = self.dir_head(curr_tokens, goal_tokens)
        direction, kappa = dir_out[0], dir_out[1]
        return direction * steps.unsqueeze(-1), self.angle_std(kappa), direction, kappa, steps

    @staticmethod
    def geo_condition(obsgoal_cond, position, angle_std, goal_mask):
        """[obsgoal_cond, x, y, std]; rows with goal_mask 1 get zeros, as in E-oracle."""
        geo = torch.cat([position, angle_std.unsqueeze(-1)], dim=-1).to(obsgoal_cond.dtype)
        keep = (1.0 - goal_mask.to(obsgoal_cond.dtype)).unsqueeze(-1)
        return torch.cat([obsgoal_cond, geo * keep], dim=-1)
