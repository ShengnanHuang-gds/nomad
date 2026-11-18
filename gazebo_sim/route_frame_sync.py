"""Pair recorded camera frames with planar odometry in simulation time."""

from collections import deque
from dataclasses import dataclass
import math

MAX_BRACKET_NS = 50_000_000
QUEUE_AGE_NS = 1_000_000_000


def stamp_ns(stamp):
    return stamp.sec * 10**9 + stamp.nanosec


def wrapped_delta(start, end):
    return math.remainder(end - start, 2 * math.pi)


@dataclass(frozen=True)
class RouteFrame:
    image: object
    stamp: int
    pose: tuple[float, float, float]
    odom_before: int
    odom_after: int


class RouteFrameSync:
    def __init__(self):
        self.images = deque()
        self.odom = deque()
        self.last_image_stamp = 0
        self.last_odom_stamp = 0

    def add_image(self, stamp, image):
        if stamp <= 0 or stamp == self.last_image_stamp:
            return
        if stamp < self.last_image_stamp:
            raise RuntimeError("camera time went backwards; start a new recording")
        self.images.append((stamp, image))
        self.last_image_stamp = stamp

    def add_odom(self, stamp, pose):
        if stamp <= 0 or stamp == self.last_odom_stamp:
            return False
        if stamp < self.last_odom_stamp:
            raise RuntimeError("odometry time went backwards; start a new recording")
        self.odom.append((stamp, pose))
        self.last_odom_stamp = stamp
        return True

    def paired(self):
        expiry = max(self.last_image_stamp, self.last_odom_stamp) - QUEUE_AGE_NS
        while self.images and self.images[0][0] <= self.last_odom_stamp:
            stamp, image = self.images.popleft()
            while len(self.odom) > 1 and self.odom[1][0] <= stamp:
                self.odom.popleft()
            before, earlier = self.odom[0]
            if before == stamp:
                yield RouteFrame(image, stamp, earlier, before, before)
            elif len(self.odom) > 1:
                after, later = self.odom[1]
                if 0 < stamp - before <= MAX_BRACKET_NS and after - stamp <= MAX_BRACKET_NS:
                    fraction = (stamp - before) / (after - before)
                    x, y, yaw = earlier
                    new_x, new_y, new_yaw = later
                    pose = (x + fraction * (new_x - x), y + fraction * (new_y - y),
                            wrapped_delta(0, yaw + fraction * wrapped_delta(yaw, new_yaw)))
                    yield RouteFrame(image, stamp, pose, before, after)
        # Keep the predecessor of the oldest pending image. Drop stale unsynchronizable
        # images so a paused or disconnected topic cannot grow either queue indefinitely.
        while self.images and self.images[0][0] < expiry:
            self.images.popleft()
        oldest_needed = self.images[0][0] if self.images else expiry
        while len(self.odom) > 1 and self.odom[1][0] <= oldest_needed:
            self.odom.popleft()
