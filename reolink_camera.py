import logging
from typing import List, Tuple

from shapely.geometry import Polygon


class ReolinkCamera:
    def __init__(
        self,
        name: str,
        min_confidence: float = 0.5,
        roi: List[Tuple[int, int]] = None,
    ):
        self.name = name
        self.min_confidence = min_confidence
        self.roi = None if roi is None else Polygon(roi)

        logging.info(
            ", ".join(
                [
                    f"Initalised Camera \"{name}\"",
                    f"Minimum Confidence = {min_confidence}",
                    f"ROI = {roi}",
                ]
            )
        )
