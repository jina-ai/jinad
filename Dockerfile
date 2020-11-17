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

ADD README.md requirements.txt ./
ADD jinad ./jinad

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "jinad/main.py"]