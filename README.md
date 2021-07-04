# cctv-filter

A Python script to filter Reolink CCTV recordings using Deepstack.

## Example Workflow

1. Cameras detect motion using the inbuilt motion detection.
2. Cameras upload the motion clips to an FTP server.
3. This Python script then uses a file watcher to detect new files uploaded to the FTP server and waits for them to be closed (for the file to be completely written).
4. The script then loops through every 15th frame in the video (roughly one for every half second of video) and asks Deepstack if it detects a person in that frame.
5. If a person is detected, it stops looping through the frames and moves the file to an "Accepted" folder.
6. If the end of the video is reached and no person was detected then it moves the files to a "Rejected" folder.

Videos are also renamed to make them easier to sort (and friendlier to read). As an example, "Front Door_01_20210511082721" would be renamed to "2021-05-11 08-27-21 (Front Door)".

## Environment Variables

| Name                          | Default | Example                        |
| ----------------------------- | ------- | ------------------------------ |
| DEEPSTACK_URL                 | None    | http://localhost               |
| INCOMING_DIR_PATH             | None    | /incoming                      |
| ACCEPTED_DIR_PATH             | None    | /accepted                      |
| LATEST_DETECTION_PATH         | None    | /latest                        |
| REJECTED_DIR_PATH             | None    | /rejected                      |
| CAMERA\_{NUM}                 | None    | Front Door                     |
| CAMERA\_{NUM}\_MIN_CONFIDENCE | 0.5     | 0.6                            |
| CAMERA\_{NUM}\_ROI            | None    | [[1, 1], [1, 300], [300, 150]] |

With the `_ROI` (region of interest) variables you can define a polygon outside of which any detections will be ignored.

Images detailing accepted detections will be saved in the path defined by the `LATEST_DETECTION_PATH` variable.

## Example Docker Compose
```yaml
version: "3"

services:
  cctv-filter:
    container_name: cctv_filter
    build: ./source/cctv-filter/
    image: dullage/cctv-filter:latest
    environment:
      DEEPSTACK_URL: "http://localhost"
      INCOMING_DIR_PATH: "/cctv/staging"
      ACCEPTED_DIR_PATH: "/cctv/accepted"
      LATEST_DETECTION_PATH: "/cctv/latest"
      REJECTED_DIR_PATH: "/cctv/rejected"
      CAMERA_1: "Front Door"
      CAMERA_1_ROI: "[[1, 1180], [1235, 865], [1199, 285], [1515, 1]]"
      CAMERA_2: "Garden"
      CAMERA_2_MIN_CONFIDENCE: "0.6"
    volumes:
      - "/cctv:/cctv"
    restart: unless-stopped
```
