#!/bin/bash -e

echo "${TIMEZONE_DEFAULT}" > "${ROOTFS_DIR}/etc/timezone"
rm "${ROOTFS_DIR}/etc/localtime"

on_chroot << EOF
/usr/sbin/dpkg-reconfigure -f noninteractive tzdata
EOF
