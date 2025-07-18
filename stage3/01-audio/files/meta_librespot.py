#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import select
import getopt
import logging
import argparse
from pathlib import Path

from spotipy import CacheFileHandler, Spotify
from spotipy.oauth2 import SpotifyOAuth

VERSION = "1.0"

SCOPES = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing"

FIFO_PATH = "/tmp/spotfifo"
CREDENTIALS_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "credentials.json"))
CONFIGURATION_FILE =  os.path.normpath(os.path.join(os.path.dirname(__file__), "meta_librespot.conf"))

params = {
    'config': CONFIGURATION_FILE,
    'librespot_fifo': FIFO_PATH,
    'spotify_client_id': None,
    'spotify_client_secret': None,
    'spotify_redirect_uri': None,
    'spotify_credentials_file': CREDENTIALS_FILE,
    'snapcast_host': 'localhost',
    'snapcast_port': 1780,
    'stream': 'default'
}

def send(msg):
    """
    Sends a JSON-encoded message to standard output.

    Args:
        msg (Any): The message object to be serialized to JSON and sent.

    Notes:
        The function writes the serialized message followed by a newline to stdout and flushes the output buffer.
    """
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def log(txt):
    """
    Logs a message and sends a Plugin.Stream.Log message if the logging level is DEBUG

    Args:
        txt (Str): The log message
    """
    logger.debug(txt)
    if logger.level == logging.DEBUG:
        msg = {
                "jsonrpc": "2.0",
                "method": "Plugin.Stream.Log",
                "params": {"severity": "Info", "message": f"{txt}"},
            }
        send(msg)

def opener(path, flags):
    """
    Opens a file at the specified path with the given flags, ensuring the file is opened in non-blocking mode.

    Args:
        path (str): The file system path to the file to be opened.
        flags (int): Flags that determine how the file is to be opened (e.g., os.O_RDONLY).

    Returns:
        int: A file descriptor for the opened file.
    """
    return os.open(path, flags | os.O_NONBLOCK)

class LibrespotControl(object):

    def __init__(self):
        """
        Initializes the class instance by setting up Spotify authentication and default playback properties.

        - Initializes an empty properties dictionary and a Spotify client instance.
        - Sets the credentials file path if not provided on the command line.
        - Attempts to authenticate with Spotify using provided credentials and cache handler.
        - Initializes playback control properties (`canGoNext`, `canGoPrevious`, `canPlay`, `canPause`, `canSeek`, `canControl`) based on authentication status.
        - Sets default values for playback status, loop status, shuffle, volume, mute, rate, position, and metadata.
        """
        self._properties = {}
        self._sp = None

        try:
            cache_handler = CacheFileHandler(cache_path=params["spotify_credentials_file"])

            auth_manager = SpotifyOAuth(
                    client_id=params['spotify_client_id'],
                    client_secret=params['spotify_client_secret'],
                    redirect_uri=params['spotify_redirect_uri'],
                    scope=SCOPES,
                    cache_handler=cache_handler,
                    open_browser=False)

            self._sp = Spotify(auth_manager=auth_manager)
        except:
            self._sp = None

        canControl = self._sp is not None

        self._properties["canGoNext"] = canControl
        self._properties["canGoPrevious"] = canControl
        self._properties["canPlay"] = canControl
        self._properties["canPause"] = canControl
        self._properties["canSeek"] = canControl
        self._properties["canControl"] = canControl
        self._properties["loopStatus"] = "none"
        self._properties["shuffle"] = False
        self._properties["playbackStatus"] = "stopped"
        self._properties["volume"] = 100
        self._properties["mute"] = False
        self._properties["rate"] = 1.0
        self._properties["position"] = 0
        self._properties["metadata"] = {}

    def _check_track_id(self, track_id):
        """
        Checks if the provided track ID is stored in the properties.

        Args:
            track_id (str): The unique identifier for the track.

        Returns:
            bool: True if the track ID is valid, False otherwise.
        """
        if "metadata" in self._properties and "trackId" in self._properties["metadata"]:
            return self._properties["metadata"]["trackId"] == track_id
        return False

    def _update_volume(self, volume):
        """
        Updates the volume for the player.

        Args:
            volume (int): The desired volume level, typically between 0 and 100.
        """
        self._properties["volume"] = int(volume)

    def _update_position(self, position):
        """
        Updates the current position in the track.

        Args:
            position (int): The current position in the track, in milliseconds.
        """
        self._properties["position"] = position / 1000.0 # Convert milliseconds to seconds

    def _update_state(self, state):
        """
        Updates the playback state of the player.

        Args:
            state (str): The playback state, such as "playing", "paused", or "stopped".
        """
        self._properties["playbackStatus"] = state

    def _update_track(self, track_id, title, duration_ms, album, artists, album_artists, uri, covers):
        """
        Updates the metadata for the current track.

        Args:
            track_id (str): The unique identifier for the track.
            title (str): The title of the track.
            duration_ms (int): The duration of the track in milliseconds.
            album (str): The album name.
            artists (list): A list of artists associated with the track.
            album_artists (list): A list of album artists associated with the track.
            uri (str): The URI of the track.
            covers (list): A list of covers urls from largest to smallest in size
        """
        self._properties["metadata"] = {
            "trackId": track_id,
            "title": title,
            "duration": duration_ms / 1000.0,  # Convert milliseconds to seconds
            "album": album,
            "artist": artists,
            "albumArtist": album_artists,
            "url": uri,
            "artUrl": covers[-1]
        }

    def _update_episode(self, track_id, title, duration_ms, uri):
        """
        Updates the metadata for the current episode.

        Args:
            track_id (str): The unique identifier for the episode.
            title (str): The title of the episode.
            duration_ms (int): The duration of the episode in milliseconds.
            uri (str): The URI of the episode.
        """
        self._properties["metadata"] = {
            "trackId": track_id,
            "title": title,
            "duration": duration_ms / 1000.0,  # Convert milliseconds to seconds
            "url": uri
        }

    def _set_loop_status(self, loop_status):
        """
        Sets the loop status for playback.

        Args:
            loop_status (str): The desired loop status, can be "none", "track", or "playlist".
        """
        match loop_status:
            case "none":
                self._sp.repeat("off")
            case "track":
                self._sp.repeat("track")
            case "playlist":
                self._sp.repeat("context")

    def _set_shuffle(self, shuffle):
        """
        Sets the shuffle status for playback.

        Args:
            shuffle (bool): True to enable shuffle, False to disable.
        """
        self._sp.shuffle(shuffle)

    def _set_volume(self, volume):
        """
        Sets the volume for playback.

        Args:
            volume (int): The desired volume level, typically between 0 and 100.
        """
        self._sp.volume(volume)

    def _play(self):
        """
        Starts playback using the Spotify client.
        """
        self._sp.start_playback()

    def _pause(self):
        """
        Pauses the current playback using the Spotify client.
        """
        self._sp.pause_playback()

    def _playPause(self, status):
        """
        Toggles playback state between 'playing' and 'paused'.

        Args:
            status (str): The current playback status. Should be either "playing" or "paused".
        """
        match status:
            case "paused":
                self._properties["playbackStatus"] = "playing"
                self._sp.start_playback()
            case "playing":
                self._properties["playbackStatus"] = "paused"
                self._sp.pause_playback()

    def _next(self):
        """
        Skips to the next track in the playback queue using the underlying Spotify client.
        """
        self._sp.next_track()

    def _previous(self):
        """
        Skips to the previous track in the playback queue using the underlying Spotify client.
        """
        self._sp.previous_track()

    def _set_position(self, position):
        """
        Set the playback position of the current track.

        Args:
            position (float): The desired playback position in seconds.
        """
        self._sp.seek_track(int (position * 1000))
        self._properties["position"] = position

    def _seek(self, offset):
        """
        Adjusts the current playback position by a given offset.

        Args:
            offset (int): The number of seconds to move the playback position forward or backward.
        """
        self._set_position(self._properties["position"] + offset)

    def _send_properties(self):
        """
        Sends the current playback properties as a JSON-RPC message.

        Constructs a message with the current properties and sends it using the `send` function.
        The message is formatted according to the JSON-RPC 2.0 specification.
        """
        log(f'Properties: {self._properties}')
        msg = {
            "jsonrpc": "2.0",
            "method": "Plugin.Stream.Player.Properties",
            "params": self._properties
        }
        send(msg)

    def _get_properties(self, id):
        """
        Send the current properties.

        Args:
            id: The identifier for the JSON-RPC request.
        """
        send({ "id": id, "jsonrpc": "2.0", "result": self._properties } )

    def _set_properties(self, id, params):
        """
        Sets properties based on the provided parameters and sends a response.

        Args:
            id (Any): The identifier for the request, used in the response.
            params (dict): A dictionary containing properties to set. Expected structure:
                {
                    "loopStatus": str,  # Loop status (e.g., "none", "track", "playlist")
                    "shuffle": bool,    # Shuffle status
                    "volume": int,      # Volume level (0-100)
                    "mute": bool,       # Mute status
                    "rate": float       # Playback rate (e.g., 1.0 for normal speed)
                }
        """
        self._properties.update(params)
        if "loopStatus" in params:
            self._set_loop_status(params["loopStatus"])
        if "shuffle" in params:
            self._set_shuffle(params["shuffle"])
        if "volume" in params:
            self._set_volume(params["volume"])

        send({ "id": id, "jsonrpc": "2.0", "result": "ok" })

    def _on_fifo_data(self, msg):
        """
        Handles incoming FIFO data messages from librespot, parses the JSON payload, and updates internal state based on the event type.
        Args:
            msg (str): A JSON-formatted string containing event data from librespot.
        Events handled:
            - "volume_changed": Updates the volume.
            - "playing": Updates position and sets state to "playing" if track ID matches.
            - "paused": Updates position and sets state to "paused" if track ID matches.
            - "seeked" or "position_correction": Updates position if track ID matches.
            - "end_of_track" or "stopped": Sets state to "stopped" if track ID matches.
            - "track_changed": Updates track information.
            - "episode_changed": Updates episode information.
            - Any unknown event: Logs a debug message.
        After handling the event, sends updated properties.
        """
        json_data = json.loads(msg)
        if "event" in json_data:
            event = json_data["event"]

            match event:
                case "volume_changed":
                    self._update_volume(int(json_data["volume"]) / 65535.0 * 100.0)
                
                case "playing":
                    if self._check_track_id(json_data["track_id"]):
                        self._update_position(int(json_data["position_ms"]))
                        self._update_state("playing")

                case "paused":
                    if self._check_track_id(json_data["track_id"]):
                        self._update_position(int(json_data["position_ms"]))
                        self._update_state("paused")

                case "seeked" | "position_correction":
                    if self._check_track_id(json_data["track_id"]):
                        self._update_position(int(json_data["position_ms"]))

                case "end_of_track" | "stopped":
                    if self._check_track_id(json_data["track_id"]):
                        self._update_state("stopped")

                case "track_changed":
                    self._update_track(
                        json_data["track_id"],
                        json_data["name"],
                        int(json_data["duration_ms"]),
                        json_data["album"],
                        json_data["artists"],
                        json_data["album_artists"],
                        json_data["uri"],
                        json_data["covers"]
                    )

                case "episode_changed":
                    self._update_episode(
                        json_data["track_id"],
                        json_data["name"],
                        int(json_data["duration_ms"]),
                        json_data["uri"]
                    )

                case _:
                    logger.debug(f"Unknown librespot event: {event}")
            
            self._send_properties()
        else:
            logger.debug(f"Unknown librespot message: {msg}")

    def _control(self, id, params):
        """
        Handles playback control commands by dispatching actions based on the provided command in params.

        Args:
            id (Any): The identifier for the control request, used in the response.
            params (dict): A dictionary containing the control command and any additional parameters.
                Expected structure:
                    {
                        "command": str,  # The control command (e.g., "play", "pause", "next", etc.)
                        "params": dict   # (Optional) Additional parameters for certain commands
                    }

        Supported commands:
            - "play": Starts playback.
            - "pause" or "stop": Pauses playback.
            - "playPause": Toggles playback state based on current status.
            - "next": Skips to the next track.
            - "previous": Returns to the previous track.
            - "setPosition": Sets playback position (requires "position" in params).
            - "seek": Seeks by an offset (requires "offset" in params).

        Responds with "ok" upon handling the command.
        """
        match params["command"]:
            case "play":
                self._play()

            case "pause" | "stop":
                self._pause()

            case "playPause":
                self._playPause(self._properties["playbackStatus"])

            case "next":
                self._next()

            case "previous":
                self._previous()

            case "setPosition":
                self._set_position(params["params"]["position"])

            case "seek":
                self._seek(params["params"]["offset"])

            case _:
                logger.debug(f"Unknwon command {params['command']}")

        send({"id": id, "jsonrpc": "2.0", "result": "ok"})

    def _on_stdin_data(self, msg):
        """
        Handles incoming data from standard input, parses it as JSON, and processes requests.

        If the incoming JSON contains an "id" and the "method" is "Plugin.Stream.Player.GetProperties",
        constructs a response message with the current properties and sends it.

        Plugin.Stream.Player.Control and Plugin.Stream.Player.SetProperty methods are not expected
        because canControl is set to False.

        Args:
            data (str): The raw JSON string received from standard input.
        """
        json_data = json.loads(msg)
        if "id" in json_data and "method" in json_data:
            id = json_data["id"]
            match json_data["method"]:
                case "Plugin.Stream.Player.GetProperties":
                    self._get_properties(id)
                case "Plugin.Stream.Player.SetProperties":
                    self._set_properties(id, json_data["params"])
                case "Plugin.Stream.Player.Control":
                    self._control(id, json_data["params"])
                case _:
                    logger.debug(f"Unsupported snapcast request: {json_data['method']}")
        else:
            logger.debug(f"Unknown snapcast message: {msg}")

    def run(self):
        """
        Waits for data from either a named pipe or standard input and processes it accordingly.

        This method opens a named pipe for reading and sends a JSON-RPC notification indicating that the stream is ready.
        It then enters a loop, monitoring both the pipe and standard input for incoming data using the `select` module.
        When data is available from the pipe, it is read, stripped of leading/trailing whitespace, and passed to the `_on_fifo_data` handler.
        When data is available from standard input, it is similarly read, stripped, and passed to the `_on_stdin_data` handler.
        The loop continues until interrupted by a KeyboardInterrupt, at which point the method exits gracefully.
        """
        fifo_path = Path(params['librespot_fifo'])

        if not fifo_path.exists():
            try:
                os.mkfifo(fifo_path)
            except OSError as e:
                logger.error(f"Failed to create FIFO at {fifo_path}: {e}")
                sys.exit(1)

        if not fifo_path.is_fifo():
            logger.error(f"FIFO {fifo_path} is not a named pipe.")
            sys.exit(1)

        if not os.access(fifo_path, os.R_OK):
            logger.error(f"FIFO {fifo_path} is not readable.")
            sys.exit(1)    

        with open(fifo_path, 'r', opener=opener) as fifo:
            try:
                logger.debug(f'Ready')
                send({"jsonrpc": "2.0", "method": "Plugin.Stream.Ready"})
                while True:
                    rlist, _, _ = select.select([fifo, sys.stdin], [], [])
                    for r in rlist:
                        if r is fifo:
                            line = fifo.readline()
                            if line:
                                self._on_fifo_data(line.strip())
                        elif r is sys.stdin:
                            line = sys.stdin.readline()
                            if line:
                                self._on_stdin_data(line.strip())
            except KeyboardInterrupt:
                pass
            finally:
                fifo.close()
                logger.debug('Exiting.')

#def usage(params):
#    print("""\
#Usage: %(progname)s [OPTION]...
#
#     --librespot_fifo=FIFO   Set the fifo to read from (default: %(librespot_fifo)s)
#     --snapcast_host=ADDR    Set the snapcast server address (default: %(snapcast_host)s)
#     --snapcast_port=PORT    Set the snapcast server port (default: %(snapcast_port)s)
#     --stream=ID             Set the stream id (default: %(stream)s)
#
#     -h, --help              Show this help message
#     -d, --debug             Run in debug mode
#     -v, --version           %(progname)s version""" % params)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))

    parser.add_argument('-c', '--config', default=params['config'], help='Set configuration file (default: %(default)s)')
    parser.add_argument('--librespot-fifo', default=params['librespot_fifo'], help='Set the fifo to read from (default: %(default)s)')
    parser.add_argument('--spotify-client-id', default=params['spotify_client_id'], help='Set the Spotify client ID (default: %(default)s)')
    parser.add_argument('--spotify-client-secret', default=params['spotify_client_secret'], help='Set the Spotify client secret (default: %(default)s)')
    parser.add_argument('--spotify-redirect-uri', default=params['spotify_redirect_uri'], help='Set the Spotify redirect URI (default: %(default)s)')
    parser.add_argument('--spotify-credentials-file', default=params['spotify_credentials_file'], help='Set the Spotify credentials file path (default: %(default)s)')
    parser.add_argument('--snapcast-host', default=params['snapcast_host'], help='Set the snapcast server address (default: %(default)s)')
    parser.add_argument('--snapcast-port', type=int, default=params['snapcast_port'], help='Set the snapcast server port (default: %(default)s)')
    parser.add_argument('--stream', default=params['stream'], help='Set the stream id')
    parser.add_argument('-d', '--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('-v', '--version', action='version', version=VERSION)

    args = parser.parse_args()

    # Load configuration from file if it exists
    try:
        with open(args.config) as file:
            json_data = json.load(file)
            params.update(json_data)
    except:
        pass

    # Update params with command line arguments
    for key in vars(args):
        if key in params:
            attr = getattr(args, key)
            if attr is not None and attr != parser.get_default(key):
                params[key] = attr

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(asctime)s %(module)s %(levelname)s: %(message)s'))

    logger = logging.getLogger('meta_librespot')
    logger.propagate = False
    logger.setLevel(logging.INFO if not args.debug else logging.DEBUG)
    logger.addHandler(log_handler)

    librespot_control = LibrespotControl()
    librespot_control.run()
