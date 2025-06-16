#!/bin/bash -e

install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/sources.list.d" "files/raspotify.list"

curl -s -O --output-dir "${ROOTFS_DIR}/usr/share/keyrings" https://www.lesbonscomptes.com/pages/lesbonscomptes.gpg
curl -s -O --output-dir "${ROOTFS_DIR}/etc/apt/sources.list.d" https://www.lesbonscomptes.com/upmpdcli/pages/upmpdcli-rbookworm.list
curl -s -o "${ROOTFS_DIR}/usr/share/keyrings/raspotify.asc" https://dtcooper.github.io/raspotify/key.asc

on_chroot << EOF
apt-get update
EOF
