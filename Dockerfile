FROM python:3.8

ARG USERNAME="nonroot"

RUN pip install pipenv
RUN apt-get update && apt-get install -y \
      python3-opencv \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home ${USERNAME} \
 && mkdir /app \
 && chown ${USERNAME}:${USERNAME} /app
WORKDIR /app
USER ${USERNAME}

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy --ignore-pipfile

COPY entrypoint.py cctv_filter.py reolink_camera.py reolink_video.py ./

CMD [ "python", "./entrypoint.py" ]
