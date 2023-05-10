import os
import spotipy
import sys
import json
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth

# Set environment variables - replace with your own client ID and secret
# See https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app
if "SPOTIPY_CLIENT_ID" not in os.environ:
    os.environ["SPOTIPY_CLIENT_ID"] = "YOUR_CLIENT_ID"

if "SPOTIPY_CLIENT_SECRET" not in os.environ:
    os.environ["SPOTIPY_CLIENT_SECRET"] = "YOUR_CLIENT_SECRET"

if "SPOTIPY_REDIRECT_URI" not in os.environ:
    os.environ["SPOTIPY_REDIRECT_URI"] = "https://example.com/callback/"

# Check that the user has changed the client ID and secret
assert (
    os.environ["SPOTIPY_CLIENT_ID"] != "YOUR_CLIENT_ID"
), "Please change the client ID to your own"
assert (
    os.environ["SPOTIPY_CLIENT_SECRET"] != "YOUR_CLIENT_SECRET"
), "Please change the client secret to your own"

# Input: Comma-separated list of artist names
username = input("Enter your Spotify username: ")
input_artists = input("Enter a list of comma-separated artist names: ")
artist_list = [artist.strip() for artist in input_artists.split(",")]

scope = "user-library-read playlist-modify-public"
token = util.prompt_for_user_token(username, scope)


def get_saved_tracks(sp, limit=50, offset=0):
    return sp.current_user_saved_tracks(limit=limit, offset=offset)


def fetch_liked_songs(sp):
    print("Fetching liked songs...")
    liked_songs = []
    offset = 0
    limit = 50
    results = get_saved_tracks(sp, limit, offset)

    while len(results["items"]) > 0:
        for idx, item in enumerate(results["items"]):
            track = item["track"]
            liked_songs.append(
                {
                    "name": track["name"],
                    "artists": [artist["name"] for artist in track["artists"]],
                    "uri": track["uri"],
                }
            )

        offset += limit
        results = get_saved_tracks(sp, limit, offset)

    return liked_songs


def load_liked_songs(filename):
    with open(filename, "r") as f:
        return json.load(f)


def save_liked_songs(filename, liked_songs):
    with open(filename, "w") as f:
        json.dump(liked_songs, f)


def add_tracks_to_playlist(sp, playlist_id, track_uris):
    chunk_size = 100
    for i in range(0, len(track_uris), chunk_size):
        chunk = track_uris[i : i + chunk_size]
        sp.playlist_add_items(playlist_id, chunk)


if token:
    sp = spotipy.Spotify(auth=token)

    # Load liked songs from JSON file or fetch and save them
    liked_songs_file = "liked_songs.json"
    if os.path.isfile(liked_songs_file):
        liked_songs = load_liked_songs(liked_songs_file)
    else:
        liked_songs = fetch_liked_songs(sp)
        save_liked_songs(liked_songs_file, liked_songs)

    # Get liked artists from liked songs
    liked_artists = [
        artist
        for artist in artist_list
        if any(artist in song["artists"] for song in liked_songs)
    ]

    # Create a new playlist
    playlist_name = input("Please enter a name for your playlist: ")
    new_playlist = sp.user_playlist_create(username, playlist_name)
    playlist_id = new_playlist["id"]

    # Get top 3 songs of each liked artist and add them to the new playlist
    track_uris = []
    for artist in liked_artists:
        top_tracks = sp.search(q=f"artist:{artist}", type="track", limit=5)
        for track in top_tracks["tracks"]["items"]:
            track_uris.append(track["uri"])

    # Add tracks to the new playlist in chunks of 100 or fewer
    add_tracks_to_playlist(sp, playlist_id, track_uris)

    print(
        f"Successfully created playlist '{playlist_name}' with top songs of liked artists."
    )
else:
    print("Can't get token for", username)
