"""Image-only relative heading predictor, separate from NoMaD XY weights."""

import copy
import math

import torch
from torch import nn
from torch.nn import functional as F


def heading_override(vector, align_deg=8.0):
    """Return a spin/stop waypoint from an image prediction, or retain XY."""
    c, s = float(vector[0]), float(vector[1])
    if not math.isfinite(c) or not math.isfinite(s) or math.hypot(c, s) < 0.5:
        return [0.0, 0.0, 1.0, 0.0], "invalid"
    if abs(math.degrees(math.atan2(s, c))) > align_deg:
        return [0.0, 0.0, c, s], "align"
    return None, "model"


class VisualYaw(nn.Module):
    def __init__(self, encoder, compressor, encoding_size=256):
        super().__init__()
        self.encoder = encoder
        self.compressor = compressor
        self.head = nn.Sequential(nn.LayerNorm(encoding_size), nn.Linear(encoding_size, 128),
                                  nn.SiLU(), nn.Linear(128, 2))
        nn.init.normal_(self.head[-1].weight, std=0.001)
        with torch.no_grad():
            self.head[-1].bias.copy_(torch.tensor([1.0, 0.0]))

    @classmethod
    def from_nomad(cls, model):
        vision = model.vision_encoder
        return cls(copy.deepcopy(vision.goal_encoder), copy.deepcopy(vision.compress_goal_enc),
                   vision.goal_encoding_size)

    def encode(self, current, goal):
        pair = torch.cat([current, goal], dim=1)
        features = self.encoder.extract_features(pair)
        features = self.encoder._avg_pooling(features)
        if self.encoder._global_params.include_top:
            features = self.encoder._dropout(features.flatten(start_dim=1))
        return self.head(self.compressor(features))

    def forward(self, current, goal, return_raw=False):
        # Swapping images must negate heading. At eval this symmetry is exact.
        forward = self.encode(current, goal)
        reverse = self.encode(goal, current)
        raw = torch.stack([(forward[:, 0]+reverse[:, 0])*0.5,
                           (forward[:, 1]-reverse[:, 1])*0.5], dim=1)
        unit = F.normalize(raw, dim=1, eps=1e-6)
        return (unit, raw) if return_raw else unit
