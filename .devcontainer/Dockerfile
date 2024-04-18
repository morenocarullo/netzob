FROM debian:bullseye AS base

ARG DEBIAN_FRONTEND=noninteractive

RUN --mount=type=cache,target=/var/cache/apt apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-dev python3-pip python3-setuptools virtualenv build-essential libpcap-dev libgraph-easy-perl libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
