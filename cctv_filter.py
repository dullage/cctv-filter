import logging
import os
import signal
import sys
import time
from typing import List

from deepstack_sdk import Detection, ServerConfig
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from reolink_camera import ReolinkCamera
from reolink_video import ReolinkVideo

REOLINK_VIDEO_EXTENSION = "mp4"


class NewVideoHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue
        super().__init__()

    @classmethod
    def _split_src_path(cls, src_path):
        path, filename_with_extension = os.path.split(src_path)
        filename, extension_with_dot = os.path.splitext(
            filename_with_extension
        )
        extension = extension_with_dot[1:]
        return path, filename, extension

    def on_created(self, event):
        _, _, extension = self._split_src_path(event.src_path)
        if extension.lower() == REOLINK_VIDEO_EXTENSION:
            logging.debug(f"VIDEO CREATED {event.src_path}")

    def on_closed(self, event):
        path, filename, extension = self._split_src_path(event.src_path)
        if extension.lower() == REOLINK_VIDEO_EXTENSION:
            logging.debug(f"VIDEO CLOSED {event.src_path}")
            self.queue.append((path, filename, extension))


class CCTVFilter(FileSystemEventHandler):
    def __init__(
        self,
        cameras: List[ReolinkCamera],
        deepstack_url: str,
        incoming_path: str,
        accepted_path: str,
        latest_detections_path: str,
        rejected_path: str,
        draw_roi: bool = False,
    ):
        self.cameras = cameras
        self.deepstack = Detection(ServerConfig(deepstack_url))
        self.incoming_path = incoming_path
        self.accepted_path = accepted_path
        self.latest_detections_path = latest_detections_path
        self.rejected_path = rejected_path
        self.draw_roi = draw_roi

        self.queue = []

    def _add_existing_videos(self):
        for path, _, files in os.walk(self.incoming_path):
            for filename_with_extension in files:
                filename, extension_with_dot = os.path.splitext(
                    filename_with_extension
                )
                extension = extension_with_dot[1:]
                if extension.lower() == REOLINK_VIDEO_EXTENSION:
                    self.queue.append((path, filename, extension))

    def _lookup_camera(self, camera_name):
        if camera_name is None:
            return None
        for camera in self.cameras:
            if camera.name == camera_name:
                return camera
        return None

    def _process_video(self, path, filename, extension):
        video = ReolinkVideo(path, filename, extension)
        camera = self._lookup_camera(video.camera_name)
        (
            video_is_accepted,
            accepted_frame,
            deepstack_response,
        ) = video.is_accepted(
            self.deepstack, camera.min_confidence, camera.roi
        )

        if video_is_accepted:
            video.move(self.accepted_path)
            image_ext = "jpg"
            video.save_images_from_frame(
                accepted_frame,
                deepstack_response,
                [
                    os.path.join(
                        self.accepted_path, video.friendly_filename(image_ext)
                    ),
                    os.path.join(
                        self.latest_detections_path,
                        f"{camera.name.lower().replace(' ', '_')}.{image_ext}",
                    ),
                ],
                self.draw_roi,
                camera.roi,
            )
        else:
            video.move(self.rejected_path)

    def _loop(self):
        while True:
            if len(self.queue) > 0:
                self._process_video(*self.queue.pop(0))
            else:
                time.sleep(1)

    def run(self):
        logging.info("Running...")
        handler = NewVideoHandler(self.queue)
        observer = Observer()
        observer.schedule(handler, self.incoming_path, recursive=True)

        # If there are any videos already in the incoming path, add them to the queue.
        self._add_existing_videos()

        # Start to watch for new videos
        observer.start()

        # Loop until exit
        def on_exit(*_):
            logging.info("Exiting")
            observer.stop()
            observer.join()
            sys.exit()

        signal.signal(signal.SIGINT, on_exit)
        signal.signal(signal.SIGTERM, on_exit)

        self._loop()
