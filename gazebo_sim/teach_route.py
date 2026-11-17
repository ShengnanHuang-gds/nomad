"""Explicit teacher-pose route diagnostic. No visual localization is required."""

import math

from teach_turn import TeachTurnAssist, wrap_angle


class TeachRouteAssist:
    def __init__(self, positions, yaws, yaw_deg=3.0):
        self.positions = positions
        self.yaws = yaws
        self.yaw_tolerance = math.radians(yaw_deg)
        turns = TeachTurnAssist(positions, yaws).turns
        self.legs = []
        start = 0
        for a, b in turns:
            if a > start:
                self.legs.append(("drive", start, a))
            self.legs.append(("spin", a, b))
            start = b
        if start < len(positions) - 1:
            self.legs.append(("drive", start, len(positions) - 1))
        self.leg = 0
        self.phase = "waiting_odom"
        self.goal = 0
        self.reached = False
        self.endpoint_error_m = None
        self.turn_entry_error_m = None
        self.turn_entry_reason = ""

    def update(self, xy, yaw, step_m, proximity_m=None):
        if xy is None or yaw is None:
            return [0.0, 0.0, 1.0, 0.0], self.goal
        last = self.positions[-1]
        self.endpoint_error_m = math.hypot(xy[0] - last[0], xy[1] - last[1])
        while self.leg < len(self.legs):
            kind, start, end = self.legs[self.leg]
            self.phase = kind
            self.goal = end
            if kind == "spin":
                err = wrap_angle(self.yaws[end] - yaw)
                if abs(err) > self.yaw_tolerance:
                    return [0.0, 0.0, math.cos(err), math.sin(err)], end
                self.leg += 1
                continue
            target = self.positions[end]
            endpoint_distance = math.hypot(xy[0] - target[0], xy[1] - target[1])
            next_is_spin = self.leg + 1 < len(self.legs) and self.legs[self.leg + 1][0] == "spin"
            # At an obstacle-constrained corner, do not insist on driving to
            # the exact teaching point before starting its known turn. This
            # does not relax the navigator's independent proximity stop.
            capture_corner = (next_is_spin and endpoint_distance <= 0.12
                              and proximity_m is not None
                              and math.isfinite(proximity_m) and 0 < proximity_m < 0.25)
            # Advance only by physically reaching this leg's endpoint. A
            # distant projection or a visual node jump cannot complete it.
            if endpoint_distance <= 0.04 or capture_corner:
                if next_is_spin:
                    self.turn_entry_error_m = endpoint_distance
                    self.turn_entry_reason = "near_obstacle" if capture_corner else "endpoint"
                self.leg += 1
                continue
            points = self.positions[start:end + 1]
            cumulative = [0.0]
            best = (float("inf"), 0.0)
            for p, q in zip(points, points[1:]):
                dx, dy = q[0] - p[0], q[1] - p[1]
                length = math.hypot(dx, dy)
                if length <= 1e-9:
                    cumulative.append(cumulative[-1])
                    continue
                fraction = max(0.0, min(1.0, ((xy[0]-p[0])*dx + (xy[1]-p[1])*dy) / length**2))
                distance = math.hypot(xy[0]-p[0]-fraction*dx, xy[1]-p[1]-fraction*dy)
                best = min(best, (distance, cumulative[-1] + fraction * length))
                cumulative.append(cumulative[-1] + length)
            ahead = min(best[1] + 0.25, cumulative[-1])
            for i, (a, b) in enumerate(zip(cumulative, cumulative[1:])):
                if b >= ahead and b > a:
                    f = (ahead - a) / (b - a)
                    p, q = points[i], points[i + 1]
                    target = (p[0] + f * (q[0]-p[0]), p[1] + f * (q[1]-p[1]))
                    self.goal = start + i + 1
                    break
            dx, dy = target[0] - xy[0], target[1] - xy[1]
            err = wrap_angle(math.atan2(dy, dx) - yaw)
            if abs(err) > math.radians(8):
                return [0.0, 0.0, math.cos(err), math.sin(err)], self.goal
            # Reduce approach speed from 0.2 to 0.08 m/s with the standard
            # 4 Hz / DT=0.25 controller, covering scan and command latency.
            step = min(step_m * (0.4 if endpoint_distance < 0.25 else 1.0), math.hypot(dx, dy))
            return [step * math.cos(err), step * math.sin(err)], self.goal
        self.reached = True
        self.phase = "done"
        self.goal = len(self.positions) - 1
        return [0.0, 0.0, 1.0, 0.0], self.goal
