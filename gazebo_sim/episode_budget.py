"""Explicitly separate simulator time from wall-clock navigation ticks."""


def timeout_reason(ticks, sim_s, wall_s, max_ticks=0, max_sim_s=0, max_wall_s=0):
    if max_sim_s > 0 and sim_s >= max_sim_s:
        return "max_sim_seconds"
    if max_wall_s > 0 and wall_s >= max_wall_s:
        return "max_wall_seconds"
    if max_ticks > 0 and ticks >= max_ticks:
        return "max_ticks"
    return ""
