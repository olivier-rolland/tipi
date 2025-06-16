#!/bin/bash -e

curl -s -O --output-dir "${ROOTFS_DIR}/usr/share/keyrings" https://www.lesbonscomptes.com/pages/lesbonscomptes.gpg
curl -s -O --output-dir "${ROOTFS_DIR}/etc/apt/sources.list.d" https://www.lesbonscomptes.com/upmpdcli/pages/upmpdcli-rbookworm.list

on_chroot << EOF
apt-get update
EOF
