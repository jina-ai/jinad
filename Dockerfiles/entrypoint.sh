#!/bin/bash

apt-get update && \
    apt-get install -y git ruby-dev build-essential && \
    gem install fluentd --no-doc

CONF_PATH=$(python3 -c "import pkg_resources; print(pkg_resources.resource_filename('jina', 'resources/fluent.conf'))")

# Start fluentd in the background
nohup fluentd -c $CONF_PATH &

# Allowing fluentd conf to load by sleeping for 2secs
sleep 2

# Start jinad (uvicorn) server
python jinad/main.py
