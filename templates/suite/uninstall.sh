#!/bin/sh
set -e

if command -v systemctl >/dev/null 2>&1; then
    systemctl stop rim-tir-client.service rim-tir-protocol.service >/dev/null 2>&1 || true
    systemctl disable rim-tir-client.service rim-tir-protocol.service >/dev/null 2>&1 || true
fi

dpkg -r rim-tir-client rim-tir-protocol
