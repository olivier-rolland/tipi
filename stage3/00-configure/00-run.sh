#!/bin/bash -e

install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d" "files/97no-recommends-suggests.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d" "files/97no-src-pkg-cache.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d" "files/97no-translation.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/sysctl.d"       "files/limit_kernel_logs.conf"

on_chroot << EOF
# Remove optional packages

apt autoremove -y
EOF
