# Festival Playlist Creator

This Python script creates a Spotify playlist based on a festival poster image. It uses OpenAI's vision model to extract artist names from the poster, then creates a playlist with top tracks from those artists that are also in your Spotify liked songs.

## Prerequisites

Before running the script, make sure you have:

- Python 3.x installed
- A Spotify account
- A Spotify Developer account with a registered app (to get client ID and secret)
- An OpenAI account with API access

## Setup

1. Clone or download this repository to your local machine.

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory with the following content:
   ```
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=https://example.com/callback/
   OPENAI_API_KEY=your_openai_api_key
   ```
   Replace the placeholder values with your actual Spotify and OpenAI credentials.

## Usage

1. Run the script:
   ```
   python festival.py
   ```

2. Enter your Spotify username when prompted.

3. Provide the path to the festival poster image when asked.

4. The script will:
   - Parse the festival poster to extract artist names
   - Fetch your liked songs from Spotify (or use cached data if available)
   - Create a playlist with top tracks from the festival artists that are also in your liked songs

5. Enter a name for your new playlist when prompted.

## Features

- Uses OpenAI's vision model to extract artist names from festival posters
- Caches liked songs to reduce API calls to Spotify
- Shows a progress bar while fetching liked songs
- Creates a playlist with top tracks from festival artists that you've liked

## Notes

- The script saves your liked songs in a file called `liked_songs.json`. This cache expires after 7 days.
- Make sure your festival poster image is clear and readable for best results.

## License

This project is licensed under the MIT License.
