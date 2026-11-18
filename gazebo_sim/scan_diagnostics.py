"""Laser-frame range summaries; proximity readings do not prove contact."""

import math


def scan_timing(scan, odom_stamp_ns, now):
    """Describe the latest scan using separate wall and simulation clocks."""
    if scan is None:
        return {"issues": ["no_scan_received"], "scan_stamp_ns": None,
                "odom_stamp_ns": odom_stamp_ns, "receipt_age_wall_s": None,
                "scan_minus_odom_ns": None, "scan_min_m": None}

    scan_stamp_ns, received_at, distance = scan
    age = now - received_at
    offset = scan_stamp_ns - odom_stamp_ns if scan_stamp_ns > 0 and odom_stamp_ns > 0 else None
    issues = []
    if scan_stamp_ns <= 0:
        issues.append("invalid_scan_stamp")
    if age > 2:
        issues.append("scan_receipt_over_2_wall_s_old")
    if odom_stamp_ns <= 0:
        issues.append("no_valid_odom_stamp")
    if offset is not None and abs(offset) > 350_000_000:
        issues.append("scan_behind_odom" if offset < 0 else "scan_ahead_of_odom")
    return {"issues": issues, "scan_stamp_ns": scan_stamp_ns,
            "odom_stamp_ns": odom_stamp_ns, "receipt_age_wall_s": age,
            "scan_minus_odom_ns": offset, "scan_min_m": distance}


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
