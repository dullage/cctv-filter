import logging

import os
import time

import cv2
from deepstack_sdk import Detection, ServerConfig
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Environment Variables
DEEPSTACK_URL = os.environ["DEEPSTACK_URL"]
INCOMING_DIR_PATH = os.environ["INCOMING_DIR_PATH"]
ACCEPTED_DIR_PATH = os.environ["ACCEPTED_DIR_PATH"]
REJECTED_DIR_PATH = os.environ["REJECTED_DIR_PATH"]

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Deepstack Init
config = ServerConfig(DEEPSTACK_URL)
deepstack = Detection(config)


def frame_to_bytes(image):
    success, im_buffer = cv2.imencode(".jpg", image)
    if not success:
        raise Exception("Failed to convert numpy array to image.")
    return im_buffer.tobytes()


def first_detected_frame(path, filename):
    logging.info(f"ANALYSING {filename}")
    video = cv2.VideoCapture(os.path.join(path, filename))
    current_frame = target_frame = 1
    read_ok, frame = video.read()

    while read_ok is True:
        if current_frame == target_frame:
            response = deepstack.detectObject(
                frame_to_bytes(frame), min_confidence=0.5
            )
            for detection in response.detections:
                if detection.label in ("person", "cat", "bear", "backpack"):
                    logging.info(
                        f"ACCEPTED {filename} {detection.label} detected"
                    )
                    video.release()
                    return frame
            target_frame += 15  # Skip 15 frames (roughly 0.5s)
        read_ok, frame = video.read()
        current_frame += 1

    logging.info(f"REJECTED {filename}")
    video.release()
    return None


def get_videos():
    file_paths = []
    for path, _, files in os.walk(INCOMING_DIR_PATH):
        for name in files:
            if name.endswith(".mp4"):
                file_paths.append((path, name))
    return file_paths


def format_timestamp(timestamp):
    return " ".join(
        [
            "-".join(
                [
                    timestamp[0:4],
                    timestamp[4:6],
                    timestamp[6:8],
                ]
            ),
            "-".join(
                [
                    timestamp[8:10],
                    timestamp[10:12],
                    timestamp[12:14],
                ]
            ),
        ]
    )


def get_new_name(filename):
    parts = filename.split("_")
    parts.extend(parts.pop().split("."))
    return format_timestamp(parts[2]) + " (" + parts[0] + ")" + "." + parts[3]


def move_video(path, filename, first_detected_frame):
    try:
        new_filename = get_new_name(filename)
    except:
        new_filename = filename

    # Debug
    if first_detected_frame is not None:
        deepstack.detectObject(
            frame_to_bytes(first_detected_frame),
            min_confidence=0.5,
            output=os.path.join(
                ACCEPTED_DIR_PATH, new_filename.replace("mp4", "jpg")
            ),
        )

    source = os.path.join(path, filename)
    destination = os.path.join(
        ACCEPTED_DIR_PATH
        if first_detected_frame is not None
        else REJECTED_DIR_PATH,
        new_filename,
    )

    os.rename(source, destination)


class NewVideoHandler(FileSystemEventHandler):
    queue = []

    def on_created(self, event):
        if event.src_path.endswith(".mp4"):
            logging.info(f"VIDEO CREATED {event.src_path}")
            self.queue.append(event.src_path)

    def on_closed(self, event):
        try:
            self.queue.remove(event.src_path)
            logging.info(f"VIDEO CLOSED {event.src_path}")
            path, filename = os.path.split(event.src_path)
            move_video(path, filename, first_detected_frame(path, filename))
        except ValueError:
            pass  # Not for us


def bulk_process(videos):
    for path, filename in videos:
        move_video(path, filename, first_detected_frame(path, filename))


if __name__ == "__main__":
    logging.info("Catching up...")
    videos = get_videos()
    while len(videos) > 0:
        bulk_process(videos)
        videos = get_videos()

    handler = NewVideoHandler()
    observer = Observer()
    observer.schedule(handler, INCOMING_DIR_PATH, recursive=True)

    logging.info("Watching for new videos...")
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
