"""Read measured wheel motion from Harmonic's post-physics ECS state."""

import csv
import math
import queue
from statistics import median
from multiprocessing import get_context

WHEELS = ("wheel_left_joint", "wheel_right_joint")
VECTORS = {"post_step_velocity_cmd_rad_s": "JointVelocityCmd", "velocity_rad_s": "JointVelocity",
           "position_rad": "JointPosition"}


def component_id(name):
    """gz-common5 hash64; SerializedEntityMap uses signed int64 map keys."""
    key = ("gz_sim_components." + name).encode("ascii")
    value = 0xcbf29ce484222325
    for byte in key:
        value = ((value ^ byte) * 0x100000001b3) & (2**64 - 1)
    return value if value < 2**63 else value - 2**64


def read_wheels(reply, entity_id, model, vector_type):
    entities = reply.state.entities
    name_key = component_id("Name")
    parent_key = component_id("ParentEntity")
    joint_key = component_id("Joint")
    model_key = component_id("Model")
    current = entities.get(entity_id)
    if (current is None or current.remove or model_key not in current.components
            or name_key not in current.components or current.components[name_key].component != model.encode()):
        raise ValueError(f"ECS state has no model {model!r} with ID {entity_id}")
    wheels = {}
    for joint_id, entity in entities.items():
        components = entity.components
        if entity.remove or joint_key not in components or parent_key not in components or name_key not in components:
            continue
        if int(components[parent_key].component) != entity_id:
            continue
        name = components[name_key].component.decode()
        if name not in WHEELS:
            continue
        if name in wheels:
            raise ValueError(f"duplicate joint {name!r} for model {entity_id}")
        wheel = {"entity_id": joint_id}
        for key, component in VECTORS.items():
            entry = components.get(component_id(component))
            value = None
            if entry is not None and not entry.remove:
                numbers = vector_type.FromString(entry.component).data
                if len(numbers) == 1 and math.isfinite(numbers[0]):
                    value = numbers[0]
            wheel[key] = value
        wheels[name] = wheel
    if set(wheels) != set(WHEELS):
        raise ValueError(f"missing wheel joints for model {entity_id}: {sorted(set(WHEELS) - wheels.keys())}")
    stamp = reply.stats.sim_time
    return {"sim_stamp_ns": stamp.sec * 10**9 + stamp.nsec, "paused": reply.stats.paused, "wheels": wheels}


def summarize(rows, start, stop, angular):
    if stop is None or start is None:
        return "turn did not start"
    active = [row for row in rows if not row["paused"] and start + 150_000_000 <= row["sim_stamp_ns"] < stop]
    if len(active) < 2:
        return "fewer than two ECS snapshots during nonzero command"
    # Physics::Update clears JointVelocityCmd before SceneBroadcaster::PostUpdate
    # serializes this state. Only measured velocities can characterize the response.
    differences = []
    for row in active:
        left, right = (row["wheels"][wheel]["velocity_rad_s"] for wheel in WHEELS)
        if left is not None and right is not None:
            differences.append(right - left)
    if len(differences) < 2:
        return "measured wheel velocity unavailable during command"
    observed = median(differences)
    expected = angular * 0.160 / 0.033
    response = observed / expected
    level = f"measured right-minus-left={observed:+.4f} rad/s; request implies {expected:+.4f} rad/s"
    if response < -0.2:
        return f"wheel response has the opposite sign ({level})"
    if response < 0.2:
        return f"little measured turning response ({level})"
    return f"measured wheels responded in the requested direction ({level})"


def _collect_wheels(world, model, entity_id, stop, ready, out):
    """A pose subscription in this process makes /world/<world>/state stop replying."""
    try:
        from gz.msgs10.double_v_pb2 import Double_V
        from gz.msgs10.empty_pb2 import Empty
        from gz.msgs10.serialized_map_pb2 import SerializedStepMap
        from gz.transport13 import Node

        node = Node()
        service = f"/world/{world}/state"
        last = None
        while not stop.is_set():
            received, reply = node.request(service, Empty(), Empty, SerializedStepMap, 2500)
            if received:
                row = read_wheels(reply, entity_id, model, Double_V)
                if last is None or row["sim_stamp_ns"] > last:
                    last = row["sim_stamp_ns"]
                    out.put(row)
                    ready.set()
            else:
                out.put(("error", f"no reply from {service}"))
            stop.wait(0.3)
    except Exception as exc:
        out.put(("error", f"{type(exc).__name__}: {exc}"))


class WheelStateTrace:
    def __init__(self, world, model, entity_id):
        self.world, self.model, self.entity_id = world, model, entity_id
        self.rows = []
        self.errors = set()
        context = get_context("spawn")
        self.stop = context.Event()
        self.ready = context.Event()
        self.out = context.Queue()
        self.worker = context.Process(
            target=_collect_wheels,
            args=(world, model, entity_id, self.stop, self.ready, self.out),
            daemon=True,
        )

    def finish(self, file, start, stop, angular):
        self.stop.set()
        self.worker.join(8)
        if self.worker.is_alive():
            self.worker.terminate()
            self.worker.join(2)
        while True:
            try:
                item = self.out.get(timeout=0.2)
            except queue.Empty:
                break
            if isinstance(item, tuple) and item and item[0] == "error":
                self.errors.add(item[1])
            else:
                self.rows.append(item)
        self.rows.sort(key=lambda row: row["sim_stamp_ns"])
        fields = ["sim_stamp_ns", "phase", "paused"]
        fields += [f"{w}_{field}" for w in WHEELS for field in ("entity_id", *VECTORS)]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in self.rows:
            stamp = row["sim_stamp_ns"]
            phase = "before" if start is None or stamp < start else "after" if stop is not None and stamp >= stop else "turn"
            values = {"sim_stamp_ns": stamp, "phase": phase, "paused": row["paused"]}
            for wheel in WHEELS:
                values.update({f"{wheel}_{k}": v for k, v in row["wheels"][wheel].items()})
            writer.writerow(values)
        print(f"wheel_state_samples={len(self.rows)}: {summarize(self.rows, start, stop, angular)}", flush=True)
        for error in sorted(self.errors):
            print(f"wheel_state_error={error}", flush=True)
