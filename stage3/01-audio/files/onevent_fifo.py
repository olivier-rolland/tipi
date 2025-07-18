#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from pathlib import Path

FIFO_PATH = "/tmp/spotfifo"

def send(event):
    """
    Sends an event by serializing it to JSON and writing it to a named pipe.

    Args:
        event (dict): The event data to be sent.
    """
    with open(FIFO_PATH, "w") as fifo:
        fifo.write(json.dumps(event) + "\n")
        fifo.flush()

def send_volume(volume):
    """
    Sends a volume change event.

    Args:
        volume (int): The new volume level to be sent.
    """
    event = {
        "event": "volume_changed",
        "volume": volume
    }
    send(event)

def send_track_position_event(event_type, track_id, position_ms):
    """
    Sends a position event with the specified type, track ID, and position.

    Args:
        event_type (str): The type of player event ("playing", "paused", "seeked", or "position_correction").
        track_id (str): The ID of the track associated with the event.
        position_ms (int): The current position in milliseconds.
    """
    event = {
        "event": event_type,
        "track_id": track_id,
        "position_ms": position_ms
    }
    send(event)

def send_track_id_event(event_type, track_id):
    """
    Sends a track id event with the specified type and track ID.

    Args:
        event_type (str): The type of player event ("unavailable", "end_of_track", "preload_next", "preloading", "loading", or "stopped").
        track_id (str): The ID of the track associated with the event.
    """
    event = {
        "event": event_type,
        "track_id": track_id
    }
    send(event)

def send_track_changed_event(track_id, uri, name, duration_ms, is_explicit, language, covers, number, disc_number, popularity, album, artists, album_artists):
    """
    Sends a track changed event with the specified details.

    Args:
        track_id (str): The ID of the track.
        uri (str): The URI of the track.
        name (str): The title of the track.
        duration_ms (int): The duration of the track in milliseconds.
        is_explicit (bool): Whether the track is explicit.
        language (str): The language of the track.
        covers (list): List of cover images for the track.
        number (int): Track number in the album.
        disc_number (int): Disc number in the album.
        popularity (int): Popularity score of the track.
        album (str): Name of the album.
        artists (list): List of artists for the track.
        album_artists (list): List of album artists for the track.
    """
    event = {
        "event": "track_changed",
        "track_id": track_id,
        "uri": uri,
        "name": name,
        "duration_ms": duration_ms,
        "is_explicit": is_explicit,
        "language": language,
        "covers": covers,
        "number": number,
        "disc_number": disc_number,
        "popularity": popularity,
        "album": album,
        "artists": artists,
        "album_artists": album_artists
    }
    send(event)

def send_episode_changed_event(track_id, uri, name, duration_ms, is_explicit, language, covers, show_name, publish_time, description):
    """
    Sends an episode changed event with the specified details.

    Args:
        track_id (str): The ID of the episode.
        uri (str): The URI of the episode.
        name (str): The title of the episode.
        duration_ms (int): The duration of the episode in milliseconds.
        is_explicit (bool): Whether the episode is explicit.
        language (str): The language of the episode.
        covers (list): List of cover images for the episode.
        show_name (str): Name of the show.
        publish_time (str): Publish time of the episode.
        description (str): Description of the episode.
    """
    event = {
        "event": "episode_changed",
        "track_id": track_id,
        "uri": uri,
        "name": name,
        "duration_ms": duration_ms,
        "is_explicit": is_explicit,
        "language": language,
        "covers": covers,
        "show_name": show_name,
        "publish_time": publish_time,
        "description": description
    }
    send(event)

if __name__ == "__main__":
    player_event = os.environ.get("PLAYER_EVENT")
    if not player_event:
        sys.exit(1)

    if player_event == "volume_changed":
        send_volume(int(os.environ.get("VOLUME")))

    elif player_event in ["playing", "paused", "seeked", "position_correction"]:
        send_track_position_event(
            player_event,
            os.environ.get("TRACK_ID"),
            int(os.environ.get("POSITION_MS"))
        )

    elif player_event in ["unavailable", "end_of_track", "preload_next", "preloading", "loading", "stopped"]:
        send_track_id_event(
            player_event,
            os.environ.get("TRACK_ID")
        )

    elif player_event == "track_changed":
        item_type = os.environ.get("ITEM_TYPE")
        if item_type == "Track":
            send_track_changed_event(
                os.environ.get("TRACK_ID"),
                os.environ.get("URI"),
                os.environ.get("NAME"),
                int(os.environ.get("DURATION_MS")),
                bool(os.environ.get("IS_EXPLICIT")),
                os.environ.get("LANGUAGE").split("\n"),
                os.environ.get("COVERS").split("\n"),
                int(os.environ.get("NUMBER")),
                int(os.environ.get("DISC_NUMBER")),
                os.environ.get("POPULARITY"),
                os.environ.get("ALBUM"),
                os.environ.get("ARTISTS").split("\n"),
                os.environ.get("ALBUM_ARTISTS").split("\n")
            )
        elif item_type == "Episode":
            send_episode_changed_event(
                os.environ.get("TRACK_ID"),
                os.environ.get("URI"),
                os.environ.get("NAME"),
                int(os.environ.get("DURATION_MS")),
                bool(os.environ.get("IS_EXPLICIT")),
                os.environ.get("LANGUAGE").split("\n"),
                os.environ.get("COVERS").split("\n"),
                os.environ.get("SHOW_NAME"),
                os.environ.get("PUBLISH_TIME"),
                os.environ.get("DESCRIPTION")
            )

