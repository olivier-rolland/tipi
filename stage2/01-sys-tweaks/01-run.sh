#!/bin/bash -e

install -m 755 files/resize2fs_once	"${ROOTFS_DIR}/etc/init.d/"

install -m 644 files/50raspi		"${ROOTFS_DIR}/etc/apt/apt.conf.d/"

install -m 644 files/console-setup   	"${ROOTFS_DIR}/etc/default/"

if [ -n "${PUBKEY_SSH_FIRST_USER}" ]; then
	install -v -m 0700 -o 1000 -g 1000 -d "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh
	echo "${PUBKEY_SSH_FIRST_USER}" >"${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/authorized_keys
	chown 1000:1000 "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/authorized_keys
	chmod 0600 "${ROOTFS_DIR}"/home/"${FIRST_USER_NAME}"/.ssh/authorized_keys
fi

if [ "${PUBKEY_ONLY_SSH}" = "1" ]; then
	sed -i -Ee 's/^#?[[:blank:]]*PubkeyAuthentication[[:blank:]]*no[[:blank:]]*$/PubkeyAuthentication yes/
s/^#?[[:blank:]]*PasswordAuthentication[[:blank:]]*yes[[:blank:]]*$/PasswordAuthentication no/' "${ROOTFS_DIR}"/etc/ssh/sshd_config
fi

on_chroot << EOF
systemctl disable hwclock.sh
systemctl disable nfs-common
systemctl disable rpcbind
if [ "${ENABLE_SSH}" == "1" ]; then
	systemctl enable ssh
else
	systemctl disable ssh
fi
systemctl enable regenerate_ssh_host_keys
EOF

if [ "${USE_QEMU}" = "1" ]; then
	echo "enter QEMU mode"
	install -m 644 files/90-qemu.rules "${ROOTFS_DIR}/etc/udev/rules.d/"
	on_chroot << EOF
systemctl disable resize2fs_once
EOF
	echo "leaving QEMU mode"
else
	on_chroot << EOF
systemctl enable resize2fs_once
EOF
fi

on_chroot <<EOF
for GRP in input spi i2c gpio; do
	/usr/sbin/groupadd -f -r "\$GRP"
done
for GRP in adm dialout cdrom audio users sudo video games plugdev input gpio spi i2c netdev render bluetooth; do
  /usr/sbin/adduser $FIRST_USER_NAME \$GRP
done
EOF

if [ -f "${ROOTFS_DIR}/etc/sudoers.d/010_pi-nopasswd" ]; then
  sed -i "s/^pi /$FIRST_USER_NAME /" "${ROOTFS_DIR}/etc/sudoers.d/010_pi-nopasswd"
fi

on_chroot << EOF
setupcon --force --save-only -v
EOF

on_chroot << EOF
/usr/sbin/usermod --pass='*' root
EOF

rm -f "${ROOTFS_DIR}/etc/ssh/"ssh_host_*_key*

sed -i "s/PLACEHOLDER//" "${ROOTFS_DIR}/etc/default/keyboard"
on_chroot << EOF
DEBIAN_FRONTEND=noninteractive /usr/sbin/dpkg-reconfigure keyboard-configuration
EOF

sed -i 's/^#\?Storage=.*/Storage=volatile/' "${ROOTFS_DIR}/etc/systemd/journald.conf"

if [ -e "${ROOTFS_DIR}/etc/avahi/avahi-daemon.conf" ]; then
  sed -i 's/^#\?publish-workstation=.*/publish-workstation=yes/' "${ROOTFS_DIR}/etc/avahi/avahi-daemon.conf"
fi

install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d"          "files/97no-recommends-suggests"
install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d"          "files/97no-src-pkg-cache"
install -D -m 644 -t "${ROOTFS_DIR}/etc/apt/apt.conf.d"          "files/97no-translation"
install -D -m 644 -t "${ROOTFS_DIR}/etc/sysctl.d"                "files/limit_kernel_logs.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/systemd/journald.conf.d" "files/disable_storage.conf"
install -D -m 644 -t "${ROOTFS_DIR}/etc/avahi/services"          "files/ssh.service"
install -D -m 644 -t "${ROOTFS_DIR}/usr/lib/systemd/system"      "files/bt-agent.service"
install -D -m 644 -t "${ROOTFS_DIR}/etc/dpkg/dpkg.cfg.d"         "files/99no-doc"

on_chroot << EOF
/sbin/dphys-swapfile swapoff
/sbin/dphys-swapfile uninstall
systemctl -q stop dphys-swapfile
systemctl -q disable dphys-swapfile
EOF
