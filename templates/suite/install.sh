#!/bin/sh
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v apt-get >/dev/null 2>&1; then
    dpkg -i "$SCRIPT_DIR"/packages/*.deb || apt-get -f install -y
else
    dpkg -i "$SCRIPT_DIR"/packages/*.deb
fi

if command -v systemctl >/dev/null 2>&1; then
    systemctl enable rim-tir-client.service rim-tir-protocol.service >/dev/null || true
    systemctl restart rim-tir-client.service rim-tir-protocol.service
fi
