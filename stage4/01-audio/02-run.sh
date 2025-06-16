#!/bin/bash -e

install -D -m 644 -t "${ROOTFS_DIR}/lib/systemd/system" "files/mpd@.service"
install -D -m 644 "files/mpd-default.conf" "${ROOTFS_DIR}/etc/mpd/default.conf"

install -D -m 644 -t "${ROOTFS_DIR}/lib/systemd/system" "files/upmpdcli@.service"
install -D -m 644 "files/upmpdcli-default.conf" "${ROOTFS_DIR}/etc/upmpdcli/default.conf"

install -D -m 644 -t "${ROOTFS_DIR}/lib/systemd/system" "files/raspotify@.service"
install -D -m 644 "files/raspotify-default.conf" "${ROOTFS_DIR}/etc/raspotify/default.conf"
