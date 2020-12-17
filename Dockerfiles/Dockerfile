FROM python:3.7.6-slim

ARG VCS_REF
ARG BUILD_DATE
ARG JINAD_PORT=8000
ARG JINAD_CONTEXT=all

ENV JINAD_PORT ${JINAD_PORT}
ENV JINAD_CONTEXT ${JINAD_CONTEXT}

LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.authors="dev-team@jina.ai" \
      org.opencontainers.image.url="https://jina.ai" \
      org.opencontainers.image.documentation="https://docs.jina.ai" \
      org.opencontainers.image.source="https://github.com/jina-ai/jinad/commit/$VCS_REF" \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Jina AI Limited" \
      org.opencontainers.image.licenses="Apache 2.0" \
      org.opencontainers.image.title="JinaD" \
      org.opencontainers.image.description="JinaD manages Jina remotely"

WORKDIR /jinad/

ADD setup.py README.md requirements.txt Dockerfiles/entrypoint.sh ./
ADD jinad ./jinad

RUN apt-get update && \
      apt-get install -y git ruby-dev build-essential && \
      gem install fluentd --no-doc
RUN chmod +x entrypoint.sh
RUN pip install . --no-cache-dir

ENTRYPOINT ["bash", "-c", "./entrypoint.sh"]
