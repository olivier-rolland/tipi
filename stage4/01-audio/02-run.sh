#!/bin/bash -e

install -D -m 644 -t "${ROOTFS_DIR}/lib/systemd/system" "files/mpd@.service"
install -D -m 644 "files/mpd-default.conf" "${ROOTFS_DIR}/etc/mpd/default.conf"

