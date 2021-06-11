import logging
import os

from cctv_filter import CCTVFilter
from reolink_camera import ReolinkCamera

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    # TODO: Move to env vars
    front_door_camera = ReolinkCamera(
        "Front Door",
        roi=[
            (1, 1180),
            (1235, 865),
            (1199, 285),
            (1515, 1),
            (2560, 1),
            (2560, 1920),
            (1, 1920),
        ]
    )
    side_camera = ReolinkCamera(
        "Side",
        roi=[(1, 500), (491, 483), (2560, 1037), (2560, 1920), (1, 1920)],
        min_confidence=0.55
    )
    garden_camera = ReolinkCamera("Garden", min_confidence=0.55)

    cctv_filter = CCTVFilter(
        [front_door_camera, side_camera, garden_camera],
        os.environ["DEEPSTACK_URL"],
        os.environ["INCOMING_DIR_PATH"],
        os.environ["ACCEPTED_DIR_PATH"],
        os.environ["LATEST_DETECTION_PATH"],
        os.environ["REJECTED_DIR_PATH"],
    )

    cctv_filter.run()
