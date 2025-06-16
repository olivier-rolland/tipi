#!/bin/bash -e

install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d"          "files/97no-recommends-suggests.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d"          "files/97no-src-pkg-cache.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d"          "files/97no-translation.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/sysctl.d"                "files/limit_kernel_logs.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/systemd/journald.conf.d" "files/disable_storage.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/systemd/network"         "files/20-eth0.network"
install -D -m 644 -t "${ROOTFS_DIR}/etc/avahi/services"          "files/ssh.service"

on_chroot << EOF
# Remove optional packages

apt autoremove -y

# Disable swap

/sbin/dphys-swapfile swapoff
/sbin/dphys-swapfile uninstall
systemctl -q stop dphys-swapfile
systemctl -q disable dphys-swapfile
EOF
