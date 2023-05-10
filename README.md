# Spotify Liked Artists Playlist Creator

This Python script creates a new Spotify playlist with the top 5 songs of each artist in your liked songs that match a given list of artist names.

## Prerequisites

Before running the script, make sure you have:

- Python 3.x installed
- A Spotify account
- Created a Spotify app and obtained a client ID and secret. See [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app) for instructions.
- Set environment variables `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` with your app's values. For example, you can add the following lines to your `.bashrc` or `.bash_profile` file (replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your app's values):

  ```bash
  export SPOTIPY_CLIENT_ID='YOUR_CLIENT_ID'
  export SPOTIPY_CLIENT_SECRET='YOUR_CLIENT_SECRET'
  export SPOTIPY_REDIRECT_URI='https://example.com/callback/'
  ```

## Usage

1. Clone or download this repository to your local machine.
2. Install the required packages by running `pip install -r requirements.txt`.
3. Run the script by running `python festival.py`.
4. Enter your Spotify username and a list of comma-separated artist names when prompted.
5. Enter a name for your new playlist when prompted.
6. The script will create a new playlist with the top 3 songs of each artist in your liked songs that match the given artist names.

Note: The script saves your liked songs in a file called `liked_songs.json` in the same directory as the script. If you run the script again, it will load your liked songs from this file instead of fetching them from Spotify again.

## License

This project is licensed under the [MIT License](LICENSE).
