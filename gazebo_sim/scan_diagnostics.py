"""Laser-frame range summaries; proximity readings do not prove contact."""

import math


def summarize_scan(msg):
    hits = []
    for i, raw in enumerate(msg.ranges):
        distance = float(raw)
        if math.isfinite(distance) and msg.range_min < distance < msg.range_max:
            angle = (msg.angle_min + i * msg.angle_increment + math.pi) % (2 * math.pi) - math.pi
            hits.append((distance, angle))
    closest = min(hits) if hits else (None, None)
    result = {"scan_min": closest[0],
              "scan_min_angle_deg": math.degrees(closest[1]) if closest[1] is not None else None,
              "scan_valid_rays": len(hits), "scan_frame_id": msg.header.frame_id}
    # Sectors are in the LaserScan frame, not assumed to be base_link.
    for name, center in (("front", 0), ("left", math.pi/2),
                         ("right", -math.pi/2), ("rear", math.pi)):
        values = [r for r, a in hits
                  if abs((a-center+math.pi) % (2*math.pi)-math.pi) <= math.pi/4 + 1e-9]
        result[f"scan_{name}_min"] = min(values) if values else None
    return result
