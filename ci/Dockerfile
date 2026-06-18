FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        gzip \
        tar \
        unzip \
        zip \
    && rm -rf /var/lib/apt/lists/*

COPY packaging/requirements.txt /tmp/requirements.txt
RUN pip install --root-user-action=ignore -r /tmp/requirements.txt

WORKDIR /workspace

ENTRYPOINT ["/bin/bash", "-lc"]
