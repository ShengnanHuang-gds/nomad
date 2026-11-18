"""Audit a reference image recording against the Gazebo model's stamped pose."""

from bisect import bisect_left
import math
import time

from route_frame_sync import MAX_BRACKET_NS, wrapped_delta

MAX_TILT_RAD = math.radians(5)


def roll_pitch_yaw(q):
    return (
        math.atan2(2 * (q.w * q.x + q.y * q.z), 1 - 2 * (q.x*q.x + q.y*q.y)),
        math.asin(max(-1.0, min(1.0, 2 * (q.w*q.y - q.z*q.x)))),
        math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y*q.y + q.z*q.z)),
    )


def pose_at_images(stamps, samples):
    times = [sample[0] for sample in samples]
    rows = []
    for stamp in stamps:
        index = bisect_left(times, stamp)
        row = {"image_stamp_ns": stamp, "gazebo_pose": None}
        if index < len(times) and times[index] == stamp:
            before = after = samples[index]
        elif (0 < index < len(times) and stamp - times[index - 1] <= MAX_BRACKET_NS
              and times[index] - stamp <= MAX_BRACKET_NS):
            before, after = samples[index - 1], samples[index]
        else:
            rows.append(row)
            continue
        fraction = (stamp - before[0]) / (after[0] - before[0]) if before[0] != after[0] else 0.0
        xyz = [a + fraction * (b - a) for a, b in zip(before[1], after[1], strict=True)]
        rpy = [math.degrees(a + fraction * wrapped_delta(a, b))
               for a, b in zip(before[2], after[2], strict=True)]
        # Check both measured poses as well as the interpolated pitch and roll.
        levels = [*rpy[:2], *(math.degrees(v) for sample in (before, after) for v in sample[2][:2])]
        row.update(gazebo_pose={"position_xyz_m": xyz, "roll_pitch_yaw_deg": rpy,
                                "before_stamp_ns": before[0], "after_stamp_ns": after[0]},
                   tilt_ok=max(map(abs, levels)) <= math.degrees(MAX_TILT_RAD))
        rows.append(row)
    return rows


class ReferenceMapPose:
    def __init__(self, model_id):
        from gz.msgs10.pose_v_pb2 import Pose_V
        from gz.transport13 import Node

        self.model_id = model_id
        self.samples = []
        self.last_wall = 0.0
        self.error = None
        self.topic = "/world/default/dynamic_pose/info"
        self.node = Node()
        if not self.node.subscribe(Pose_V, self.topic, self.on_pose):
            raise RuntimeError(f"could not subscribe to {self.topic}")

    def on_pose(self, message):
        stamp = message.header.stamp
        ns = stamp.sec * 10**9 + stamp.nsec
        if ns <= 0:
            return
        for pose in message.pose:
            if pose.id == self.model_id and pose.name == "burger_cam":
                if self.samples and ns <= self.samples[-1][0]:
                    if ns < self.samples[-1][0]:
                        self.error = "Gazebo pose timestamp went backwards"
                    return
                xyz = (pose.position.x, pose.position.y, pose.position.z)
                q = pose.orientation
                if not all(map(math.isfinite, (*xyz, q.x, q.y, q.z, q.w))):
                    self.error = "Gazebo published a nonfinite pose"
                    return
                self.samples.append((ns, xyz, roll_pitch_yaw(q)))
                self.last_wall = time.monotonic()
                return

    def check_upright(self, odom_stamp):
        if self.error:
            raise RuntimeError(self.error)
        if (not self.samples or time.monotonic() - self.last_wall > 2
                or abs(self.samples[-1][0] - odom_stamp) > 350_000_000):
            raise RuntimeError("Gazebo model pose missing or stale")
        _, _, rpy = self.samples[-1]
        if max(abs(rpy[0]), abs(rpy[1])) > MAX_TILT_RAD:
            raise RuntimeError(f"reference recording stopped on Gazebo tilt: "
                               f"roll={math.degrees(rpy[0]):.2f}°, pitch={math.degrees(rpy[1]):.2f}°")

    def close(self):
        self.node.unsubscribe(self.topic)
