#!/bin/bash -e

gpasswd -a pi audio

install -m 755 -o mpd -g audio -d /var/lib/mpd/music
install -m 755 -o mpd -g audio -d /var/lib/mpd/playlists
install -m 755 -o mpd -g audio -d /var/log/mpd

chown -R mpd:audio /etc/mpd
