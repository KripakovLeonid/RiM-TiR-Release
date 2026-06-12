#!/bin/sh
set -e

if command -v systemctl >/dev/null 2>&1; then
    systemctl stop $service_names >/dev/null 2>&1 || true
    systemctl disable $service_names >/dev/null 2>&1 || true
fi

dpkg -r $package_names
