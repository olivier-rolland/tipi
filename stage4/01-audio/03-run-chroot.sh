#!/bin/bash -e

SNAPCAST_VERSION=0.31.0

gpasswd -a pi audio

install -m 755 -o mpd -g audio -d /var/lib/mpd/music
install -m 755 -o mpd -g audio -d /var/lib/mpd/playlists
install -m 755 -o mpd -g audio -d /var/log/mpd

chown -R mpd:audio /etc/mpd
chown -R upmpdcli:audio /etc/upmpdcli
chown -R root:audio /etc/raspotify

SNAPSERVER=snapserver_${SNAPCAST_VERSION}-1_${ARCH}_${RELEASE}.deb

wget -nc "https://github.com/badaix/snapcast/releases/download/v${SNAPCAST_VERSION}/${SNAPSERVER}"
apt install --yes "./${SNAPSERVER}"
rm -f "${SNAPSERVER}"

SNAPCLIENT=snapclient_${SNAPCAST_VERSION}-1_${ARCH}_${RELEASE}.deb

wget -nc "https://github.com/badaix/snapcast/releases/download/v${SNAPCAST_VERSION}/${SNAPCLIENT}"
apt install --yes "./${SNAPCLIENT}"
rm -f "${SNAPCLIENT}"
