"""Save exact RGB context and model outputs for offline visual-policy replay."""

import json
from pathlib import Path


class VisionDebug:
    def __init__(self, directory):
        self.directory = Path(directory) if directory else None
        self.last_node = None
        self.last_close = None
        self.started = False

    def record(self, tick, images, metadata, goal_image=None):
        if self.directory is None:
            return
        node, close = metadata["closest_node"], metadata["dist_is_close"]
        if node == self.last_node and close == self.last_close and tick % 20:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        names = []
        for i, pil in enumerate(images):
            name = f"tick_{tick:06d}_context_{i}.png"
            pil.save(self.directory / name)
            names.append(name)
        goal_name = None
        if goal_image is not None:
            goal_name = f"tick_{tick:06d}_goal.png"
            goal_image.save(self.directory / goal_name)
        with (self.directory / "predictions.jsonl").open("a" if self.started else "w", encoding="utf-8") as f:
            f.write(json.dumps({**metadata, "tick": tick, "context_images": names,
                                "goal_image": goal_name}) + "\n")
        self.last_node, self.last_close = node, close
        self.started = True
