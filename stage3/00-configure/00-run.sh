#!/bin/bash -e

install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d" "files/97no-recommends-suggests.conf"

on_chroot << EOF
# Remove optional packages

apt autoremove -y
EOF
