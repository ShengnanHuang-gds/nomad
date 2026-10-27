import os
import argparse
import time
import pdb

import torch
import torch.nn as nn
import torch.nn.functional as F


class NoMaD(nn.Module):

    def __init__(self, vision_encoder, 
                       noise_pred_net,
                       dist_pred_net):
        super(NoMaD, self).__init__()


        self.vision_encoder = vision_encoder
        self.noise_pred_net = noise_pred_net
        self.dist_pred_net = dist_pred_net
    
    def forward(self, func_name, **kwargs):
        if func_name == "vision_encoder" :
            output = self.vision_encoder(kwargs["obs_img"], kwargs["goal_img"], input_goal_mask=kwargs["input_goal_mask"])
        elif func_name == "noise_pred_net":
            output = self.noise_pred_net(sample=kwargs["sample"], timestep=kwargs["timestep"], global_cond=kwargs["global_cond"])
        elif func_name == "dist_pred_net":
            output = self.dist_pred_net(kwargs["obsgoal_cond"])
        else:
            raise NotImplementedError
        return output


class DenseNetwork(nn.Module):
    def __init__(self, embedding_dim):
        super(DenseNetwork, self).__init__()
        
        self.embedding_dim = embedding_dim 
        self.network = nn.Sequential(
            nn.Linear(self.embedding_dim, self.embedding_dim//4),
            nn.ReLU(),
            nn.Linear(self.embedding_dim//4, self.embedding_dim//16),
            nn.ReLU(),
            nn.Linear(self.embedding_dim//16, 1)
        )
    
    def forward(self, x):
        x = x.reshape((-1, self.embedding_dim))
        output = self.network(x)
        return output


class GoalPosHead(nn.Module):
    """Predict the goal position in the robot frame (meters) and a per-axis std.

    Same shape as DenseNetwork with 4 outputs: mu_x, mu_y, raw_sigma_x, raw_sigma_y.
    """

    def __init__(self, embedding_dim, min_sigma=0.05, init_sigma_bias=0.5):
        super(GoalPosHead, self).__init__()
        self.embedding_dim = embedding_dim
        self.min_sigma = min_sigma
        self.network = nn.Sequential(
            nn.Linear(self.embedding_dim, self.embedding_dim // 4),
            nn.ReLU(),
            nn.Linear(self.embedding_dim // 4, self.embedding_dim // 16),
            nn.ReLU(),
            nn.Linear(self.embedding_dim // 16, 4),
        )
        # softplus(0.5) + 0.05 is about 1 m, so NLL starts from a wide sigma after the MSE warmup.
        nn.init.constant_(self.network[-1].bias[2:], init_sigma_bias)

    def forward(self, x):
        output = self.network(x.reshape((-1, self.embedding_dim)))
        mu = output[:, :2]
        sigma = F.softplus(output[:, 2:]) + self.min_sigma
        return mu, sigma


class GoalDirectionHead(nn.Module):
    """Predict the goal bearing in the robot frame as a von Mises distribution.

    Same shape as DenseNetwork with 3 outputs: c, s, raw_kappa.
    Returns the unit direction (cos, sin) and the concentration kappa.
    """

    def __init__(self, embedding_dim, min_kappa=1e-3, init_kappa_bias=1.0):
        super(GoalDirectionHead, self).__init__()
        self.embedding_dim = embedding_dim
        self.min_kappa = min_kappa
        self.network = nn.Sequential(
            nn.Linear(self.embedding_dim, self.embedding_dim // 4),
            nn.ReLU(),
            nn.Linear(self.embedding_dim // 4, self.embedding_dim // 16),
            nn.ReLU(),
            nn.Linear(self.embedding_dim // 16, 3),
        )
        nn.init.constant_(self.network[-1].bias[2:], init_kappa_bias)

    def forward(self, x):
        output = self.network(x.reshape((-1, self.embedding_dim)))
        direction = F.normalize(output[:, :2], dim=-1, eps=1e-6)
        kappa = F.softplus(output[:, 2]) + self.min_kappa
        return direction, kappa



