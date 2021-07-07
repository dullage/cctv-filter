import json
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
    DEEPSTACK_URL = os.environ["DEEPSTACK_URL"]
    INCOMING_DIR_PATH = os.environ["INCOMING_DIR_PATH"]
    ACCEPTED_DIR_PATH = os.environ["ACCEPTED_DIR_PATH"]
    LATEST_DETECTION_PATH = os.environ["LATEST_DETECTION_PATH"]
    REJECTED_DIR_PATH = os.environ["REJECTED_DIR_PATH"]
    DRAW_ROI = os.environ.get("DRAW_ROI", "False").lower() == "true"

    cameras = []
    camera_num = 1
    while True:
        try:
            name = os.environ[f"CAMERA_{camera_num}"]
        except KeyError:
            break
        min_confidence = float(
            os.environ.get(f"CAMERA_{camera_num}_MIN_CONFIDENCE", 0.5)
        )
        roi_json = os.environ.get(f"CAMERA_{camera_num}_ROI", None)
        if roi_json is not None:
            roi = json.loads(roi_json)
        else:
            roi = None
        cameras.append(ReolinkCamera(name, min_confidence, roi))

        camera_num += 1

    cctv_filter = CCTVFilter(
        cameras,
        DEEPSTACK_URL,
        INCOMING_DIR_PATH,
        ACCEPTED_DIR_PATH,
        LATEST_DETECTION_PATH,
        REJECTED_DIR_PATH,
        draw_roi=DRAW_ROI,
    )

    cctv_filter.run()
