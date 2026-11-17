"""Odometry-assisted turn/exit diagnostic; deliberately uses teacher poses.

Coordinates must share the teacher's odom frame (translation is allowed).
No ROS or model dependencies, so the state machine can be replayed offline.
"""

from __future__ import annotations

import math


def wrap_angle(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


class TeachTurnAssist:
    def __init__(self, positions, yaws, yaw_deg=3.0, exit_m=0.35):
        self.positions = positions
        self.yaws = yaws
        self.tolerance = math.radians(yaw_deg)
        self.exit_m = exit_m
        self.turns = []
        i = 0
        while i + 1 < len(yaws):
            start = i
            while i + 1 < len(yaws):
                p, q = positions[i], positions[i + 1]
                if (math.hypot(q[0] - p[0], q[1] - p[1]) > 0.05
                        or abs(wrap_angle(yaws[i + 1] - yaws[i])) < math.radians(4)):
                    break
                i += 1
            if i > start:
                self.turns.append((start, i))
            else:
                i += 1
        self.completed = set()
        self.active = None
        self.phase = "model"
        self.forward_goal = None

    def update(self, node, xy, yaw, step_m):
        """Return an override waypoint and optional first translating goal index."""
        if xy is None or yaw is None:
            return None, None
        if self.active is None:
            for start, end in self.turns:
                p = self.positions[start]
                # Visual match alone may be stale or jump across the route.
                if (end not in self.completed and start <= node <= end
                        and math.hypot(xy[0] - p[0], xy[1] - p[1]) <= 0.18):
                    self.active = (start, end)
                    self.phase = "spin"
                    break
        if self.active is None:
            # Keep conditioning on translation if localization falls back to
            # images from an already completed in-place turn.
            goal = self.forward_goal if self.forward_goal is not None and node < self.forward_goal else None
            return None, goal
        start, end = self.active
        p = self.positions[end]
        # Skip the images taken in place: choose a goal showing translation.
        goal = end + 1 if end + 1 < len(self.positions) else end
        if self.phase == "spin":
            err = wrap_angle(self.yaws[end] - yaw)
            if abs(err) > self.tolerance:
                return [0.0, 0.0, math.cos(err), math.sin(err)], goal
            self.completed.add(end)
            self.forward_goal = goal
            self.phase = "exit"
        if goal == end or self.exit_m <= 0:
            self.active = None
            self.phase = "model"
            return None, goal
        q = self.positions[goal]
        heading = math.atan2(q[1] - p[1], q[0] - p[0])
        ux, uy = math.cos(heading), math.sin(heading)
        along = (xy[0] - p[0]) * ux + (xy[1] - p[1]) * uy
        # Never carry the exit assist through the next corner.
        next_start = next((a for a, _ in self.turns if a > end), len(self.positions) - 1)
        limit = min(self.exit_m, math.hypot(
            self.positions[next_start][0] - p[0], self.positions[next_start][1] - p[1]))
        if along >= limit:
            self.active = None
            self.phase = "model"
            return None, goal
        # Short lookahead along the outgoing line also corrects entry offset.
        lookahead = min(max(0.0, along) + 0.25, limit)
        dx = p[0] + ux * lookahead - xy[0]
        dy = p[1] + uy * lookahead - xy[1]
        err = wrap_angle(math.atan2(dy, dx) - yaw)
        if abs(err) > math.radians(8):
            return [0.0, 0.0, math.cos(err), math.sin(err)], goal
        return [step_m * math.cos(err), step_m * math.sin(err)], goal
