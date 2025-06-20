# TiPi

Tiny Raspberry Pi, TiPi for short, is a lightweight version of the standard Raspberry Pi OS lite image designed for headless servers and low-CPU applications, such as media servers.

The build uses a customized [pi-gen](https://github.com/RPi-Distro/pi-gen) to create the image.

## Installing

Use `rpi-imager` to install the TiPi images.

## Configuring



## Contributing

### Content

Stages 0, 1, and 2 are re-used from [pi-gen](https://github.com/RPi-Distro/pi-gen) but all development packages removed.

Additionally, in Stage 2, suggested and recommended packages and source package cache are removed, kernel logs to console are limited to warnings and errors, journal storage, swap file, and translation packages are disabled, wired networking and ssh discovery are enabled, and missing bluetooth packages are added.

In Stage 3 audio packages are installed: MPD, upmpdcli, raspotify, and snapcast (client and server).

### Build

Running `sudo ./build.sh` will generate 2 images in the `deploy` folder:

- `image_2025-06-16-tipi-bookworm-arm64.img.xz` without the audio packages
- `image_2025-06-16-tipi-bookworm-arm64-audio.img.xz` with the audio packages
