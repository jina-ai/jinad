FROM python:3.7.6-slim

ARG JINAD_PORT=8000

ENV JINAD_PORT ${JINAD_PORT}

WORKDIR /jinad/

ADD setup.py README.md requirements.txt Dockerfiles/entrypoint.sh ./
ADD jinad ./jinad

RUN apt-get update && \
      apt-get install -y git ruby-dev build-essential && \
      gem install fluentd --no-doc

RUN pip install ".[all]" --no-cache-dir

ENTRYPOINT [ "jinad" ]
