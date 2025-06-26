# TiPi

Tiny Raspberry Pi, TiPi for short, is a lightweight version of the standard Raspberry Pi OS lite image designed for headless servers and low-CPU applications, such as media servers.

The build uses a customized [pi-gen](https://github.com/RPi-Distro/pi-gen) to create the image.

## Installing

Use `rpi-imager` to install the TiPi images.

## Configuring

### Audio devices and mixers

To get the list of the available ALSA devices, run:

```
$ aplay -L
```

To get the list of the available ALSA mixer controls for a given device, run:

```
$ amixer -D <device> scontrols
```

### Media server

1. Edit `/etc/mpd.conf` to configure mpd.
2. Start and enable mpd

    ```
    $ systemctl start mpd.service
    $ systemctl enable mpd.service
    ```

See the full mpd documentation [here](https://mpd.readthedocs.io/en/latest/).

#### Remote music

If the musique directory is located in a remote server, export it ion NFS or Samba and change `music_directory` to:

```
music_directory "nfs://fileserver.local/srv/mp3"
```

Or

```
music_directory "smb://fileserver.local/mp3"
```

If the remote server is also a mpd server, you can reuse its music database by changing the `database` section to:

```
database {
	plugin "proxy"
	host "fileserver.local"
	port "6600"
}
```

#### Bit perfect

Set the alsa `audio_output` section to:

```
audio_output {
        type                    "alsa"
        name                    "<name>"
        device                  "hw:CARD=<name>,DEV=<dev>"
        mixer_type              "none"
        auto_resample           "no"
        auto_channels           "no"
        auto_format             "no"
        replay_gain_handler     "none"
```

Disable loudness and volume normalization:

```
replaygain "off"
volume_normalization "no"
```

### UPNP

1. Edit `/etc/upmpdcli.conf` to configure upmpdcli
2. Start and enabled upmpdcli

    ```
    $ systemctl start upmpdcli.service
    $ systemctl enable upmpdcli.service
    ```

See the full upmpdcli documentation [here](https://www.lesbonscomptes.com/upmpdcli/pages/docs.html).

### Spotify

1. Edit `/etc/raspotify/conf` to configure raspotify
2. Start and enable raspotify

    ```
    $ systemctl start raspotify.service
    $ systemctl enable raspotify.service
    ```

See the full librespot documentation [here](https://github.com/librespot-org/librespot/wiki).

#### Bit perfect

Set the output device to the direct hardware device without any conversions:

```
LIBRESPOT_DEVICE="hw:CARD=<name>,DEV=<dev>"
```

Set the output format to a format supported by the ALSA device:

```
LIBRESPOT_FORMAT="<F64|F32|S32|S24|S24_3|S16>"
```

Disable volume normalization:

```
LIBRESPOT_ENABLE_VOLUME_NORMALISATION=off
```

Disable dithering:

```
LIBRESPOT_DITHER="none"
```

Bypass volume control:

```
LIBRESPOT_MIXER="softvol"
LIBRESPOT_VOLUME_CTRL="fixed"
LIBRESPOT_INITIAL_VOLUME="100"
```

### Multiroom

#### Server

1. Edit `/etc/snapserver.conf` to configure the snapcast server
2. Start and enable snapserver

    ```
    $ systemctl start snapserver.service
    $ systemctl enable snapserver.service
    ```

See the full snapcast server documentation [here](https://github.com/badaix/snapcast/blob/develop/doc/configuration.md) and [here](https://github.com/badaix/snapcast/blob/develop/doc/player_setup.md).

##### MPD

1. Configure mpd to output in a pipe:

    ```
    audio_output {
        type            "fifo"
        name            "Snapcast"
        path            "/var/lib/mpd/fifo"
        format          "44100:16:2"
        mixer_type      "software"
    }
    ```

2. Create the pipe:

    ```
    sudo mkfifo /var/lib/mpd/fifo
    sudo chown mpd:audio /var/lib/mpd/fifo
    ```

3. Set the source in `/etc/snapserver.conf`:

    ```
    source = pipe:///var/lib/mpd/fifo?name=MPD&sampleformat=44100:16:2&codec=flac
    ```

##### Spotify

Set the source in `/etc/snapserver.conf`:

```
source = librespot:///usr/bin/librespot?name=Spotify&
```

If raspotify is also configured and running, set the following source instead:

```
source = librespot:///usr/bin/librespot?name=Spotify&killall=false
```

#### Client

1. Edit `/etc/default/snapclient` to configure the snapcast client

    ```
    SNAPCLIENT_OPTS="--host <snapcast server> --player alsa --soundcard <device name>"
    ```

2. Start and enable snapclient

    ```
    $ systemctl start snapclient.service
    $ systemctl enable snapclient.service
    ```

### Bluetooth

1. Start and enable the bluetooth agent

    ```
    $ sudo systemctl start bt-agent.service
    $ sudo systemctl enable bt-agent.service
    ```

2. Configure the bluetooth ALSA output device

    ```
    $ sudo systemctl edit bluealsa-aplay

    [Service]
    ExecStart=
    ExecStart=/usr/bin/bluealsa-aplay --pcm=<device name>
    ```

3. Restart the bluetooth ALSA playback service

    ```
    $ sudo systemctl restart bluealsa-aplay.service
    ```

4. Configure the bluetooth device

    ```
    $ bluetoothctl

    power on
    pairable on
    quit
    ```

5. When you want to pair a device, turn the bluetooth device in discoverable mode

    ```
    $ bluetoothctl discoverable on
    ```

You can change the name of the bluetooth device with the following command:

```
$ sudo hostnamectl hostname --pretty <name>
```

You can change the class of the bluetooth device in the `/etc/bluetooth/main.conf` file:

```
[General]
Class = 0x200400
```

See [here](https://www.ampedrftech.com/cod.htm) for the possible classes.

## Contributing

### Content

Stages 0, 1, and 2 are re-used from [pi-gen](https://github.com/RPi-Distro/pi-gen) but all development packages removed.

Additionally, in Stage 2, suggested and recommended packages and source package cache are removed, kernel logs to console are limited to warnings and errors, journal storage, swap file, and translation packages are disabled, wired networking and ssh discovery are enabled, and missing bluetooth packages are added.

In Stage 3 audio packages are installed: mpd, upmpdcli, raspotify, and snapcast (client and server).

### Build

Running `sudo ./build.sh` will generate 2 images in the `deploy` folder:

- `image_2025-06-16-tipi-bookworm-arm64.img.xz` without the audio packages
- `image_2025-06-16-tipi-bookworm-arm64-audio.img.xz` with the audio packages
