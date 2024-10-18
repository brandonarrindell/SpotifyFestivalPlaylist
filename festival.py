"""
Festival Playlist Creator

This module creates Spotify playlists based on festival poster images using OpenAI's vision model.
"""

import os
import json
import io
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

# Constants
LIKED_SONGS_FILE = "liked_songs.json"
SPOTIFY_SCOPE = "user-library-read playlist-modify-public"
CHUNK_SIZE = 100
CACHE_EXPIRY_DAYS = 7  # Number of days before refreshing the liked songs cache


def setup_environment() -> None:
    """Set up environment variables for Spotify API and OpenAI."""
    required_vars = [
        "SPOTIPY_CLIENT_ID",
        "SPOTIPY_CLIENT_SECRET",
        "SPOTIPY_REDIRECT_URI",
        "OPENAI_API_KEY"
    ]

    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Please set the {var} in your .env file")


def get_spotify_client() -> spotipy.Spotify:
    """Create and return an authenticated Spotify client."""
    auth_manager = SpotifyOAuth(scope=SPOTIFY_SCOPE)
    return spotipy.Spotify(auth_manager=auth_manager)


def fetch_liked_songs(sp: spotipy.Spotify) -> List[Dict]:
    """Fetch all liked songs from the user's Spotify library."""
    print("Fetching liked songs...")
    liked_songs = []
    offset = 0
    limit = 50

    # Get total number of liked songs
    total = sp.current_user_saved_tracks(limit=1)['total']
    print(f"Total number of liked songs: {total}")

    # Create progress bar
    with tqdm(total=total, desc="Fetching", unit="song") as pbar:
        while True:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
            if not results['items']:
                break

            batch = [
                {
                    "name": track["track"]["name"],
                    "artists": [artist["name"] for artist in track["track"]["artists"]],
                    "uri": track["track"]["uri"],
                }
                for track in results["items"]
            ]
            liked_songs.extend(batch)

            offset += limit
            pbar.update(len(batch))

    print(f"Successfully fetched {len(liked_songs)} liked songs.")
    return liked_songs


def load_liked_songs() -> Dict:
    """Load liked songs from a JSON file."""
    if os.path.exists(LIKED_SONGS_FILE):
        with open(LIKED_SONGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"timestamp": None, "songs": []}


def save_liked_songs(liked_songs: List[Dict]) -> None:
    """Save liked songs to a JSON file with a timestamp."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "songs": liked_songs
    }
    with open(LIKED_SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_cached_or_fetch_liked_songs(sp: spotipy.Spotify) -> List[Dict]:
    """Get liked songs from cache if recent, otherwise fetch from Spotify."""
    cached_data = load_liked_songs()
    if cached_data["timestamp"]:
        cache_date = datetime.fromisoformat(cached_data["timestamp"])
        if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
            print("Using cached liked songs.")
            return cached_data["songs"]

    liked_songs = fetch_liked_songs(sp)
    save_liked_songs(liked_songs)
    return liked_songs


def get_liked_artists(artist_list: List[str], liked_songs: List[Dict]) -> List[str]:
    """Get a list of liked artists from the input list."""
    liked_artists_set = set(
        artist for song in liked_songs for artist in song["artists"])
    return list(set(artist_list) & liked_artists_set)


def get_top_tracks(sp: spotipy.Spotify, artists: List[str], limit: int = 5) -> List[str]:
    """Get top tracks for a list of artists."""
    track_uris = []
    for artist in artists:
        top_tracks = sp.search(q=f"artist:{artist}", type="track", limit=limit)
        track_uris.extend([track["uri"]
                          for track in top_tracks["tracks"]["items"]])
    return track_uris


def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, track_uris: List[str]) -> None:
    """Add tracks to a playlist in chunks."""
    for i in range(0, len(track_uris), CHUNK_SIZE):
        chunk = track_uris[i:i + CHUNK_SIZE]
        sp.playlist_add_items(playlist_id, chunk)


def create_festival_playlist(sp: spotipy.Spotify, playlist_name: str, track_uris: List[str]) -> None:
    """Create a new playlist and add tracks to it."""
    new_playlist = sp.user_playlist_create(sp.me()['id'], playlist_name)
    add_tracks_to_playlist(sp, new_playlist["id"], track_uris)


def parse_festival_poster(image_path: str) -> List[Tuple[str, float]]:
    """Parse the festival poster image and return a list of artists with confidence scores."""
    print("Starting festival poster analysis with OpenAI...")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with Image.open(image_path) as img:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

    print("Sending image to OpenAI for analysis...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in music festivals and artist recognition. Your task is to analyze festival posters and extract artist names with high accuracy."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this festival poster image and follow these steps:

                            1. Identify all text that could potentially be artist names.
                            2. For each potential artist name:
                            - Evaluate if it's likely to be a musical artist or band name.
                            - Consider factors like font size, positioning, and styling on the poster.
                            - Assign a confidence score (0-1) based on how certain you are that it's an artist name.
                            3. Exclude any text that is clearly not an artist name (e.g., festival name, date, location, sponsors).
                            4. If you're unsure about a name, include it with a lower confidence score.
                            5. Return your analysis as a JSON object with this structure:
                            {
                                "artists": [
                                {"name": "Artist1", "confidence": 0.95},
                                {"name": "Artist2", "confidence": 0.8},
                                ...
                                ]
                            }

                            Aim for high precision in your artist identification."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64.b64encode(img_byte_arr).decode('utf-8')}"
                        }
                    },
                ],
            }
        ],
        max_tokens=1000,
        response_format={"type": "json_object"}
    )
    print("Received response from OpenAI.")

    try:
        artists_json = json.loads(response.choices[0].message.content)
        artists = [(artist['name'], artist['confidence'])
                   for artist in artists_json["artists"]]
        print(
            f"Successfully parsed {len(artists)} potential artists from the poster.")
        return artists
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing OpenAI response: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        return []


def filter_artists(sp: spotipy.Spotify, artists: List[Tuple[str, float]], popularity_threshold: int = 20, confidence_threshold: float = 0.7) -> List[str]:
    """Filter artists based on Spotify popularity and OpenAI confidence score."""
    filtered_artists = []
    for artist, confidence in artists:
        if confidence < confidence_threshold:
            continue
        results = sp.search(q=artist, type='artist', limit=1)
        if results['artists']['items']:
            popularity = results['artists']['items'][0]['popularity']
            if popularity >= popularity_threshold:
                filtered_artists.append(artist)
    return filtered_artists


def display_artists(artists: List[Tuple[str, float]]) -> None:
    """Display the list of artists extracted from the poster with their confidence scores."""
    print("\nArtists extracted from the festival poster:")
    for i, (artist, confidence) in enumerate(artists, 1):
        print(f"{i}. {artist} (Confidence: {confidence:.2f})")
    print()  # Add a blank line for better readability


def create_full_festival_playlist(sp: spotipy.Spotify, artists: List[str], playlist_name: str) -> None:
    """Create a playlist with top tracks from all artists on the poster."""
    track_uris = get_top_tracks(sp, artists)
    create_festival_playlist(sp, playlist_name, track_uris)
    print(
        f"Successfully created playlist '{playlist_name}' with top songs from all festival artists.")


def main():
    """Main function to run the Festival Playlist Creator."""
    setup_environment()

    poster_path = input("Enter the path to the festival poster image: ")

    try:
        sp = get_spotify_client()
    except spotipy.SpotifyException as e:
        print(f"Error authenticating with Spotify: {e}")
        return

    potential_artists = parse_festival_poster(poster_path)
    if not potential_artists:
        print("No artists found in the poster. Exiting.")
        return

    print("\nAll potential artists from the poster:")
    display_artists(potential_artists)

    filtered_artists = filter_artists(sp, potential_artists)
    print(f"\nFiltered {len(filtered_artists)} likely festival artists.")
    display_artists([(artist, confidence) for artist, confidence in potential_artists if artist in filtered_artists])

    mode = input(
        "Choose a mode:\n1. Create playlist based on liked songs\n"
        "2. Create playlist with all festival artists\nEnter 1 or 2: "
    )

    if mode == "1":
        liked_songs = get_cached_or_fetch_liked_songs(sp)
        liked_artists = get_liked_artists([artist for artist, _ in filtered_artists], liked_songs)
        print(f"\nFound {len(liked_artists)} artists from the poster in your liked songs.")
        display_artists([(artist, confidence) for artist, confidence in potential_artists if artist in liked_artists])
        track_uris = get_top_tracks(sp, liked_artists)
        playlist_name = input("Please enter a name for your playlist: ")
        create_festival_playlist(sp, playlist_name, track_uris)
        print(f"Successfully created playlist '{playlist_name}' with top songs from your liked artists.")
    elif mode == "2":
        playlist_name = input("Please enter a name for your playlist: ")
        create_full_festival_playlist(sp, [artist for artist, _ in filtered_artists], playlist_name)
    else:
        print("Invalid mode selected. Exiting.")


if __name__ == "__main__":
    main()
