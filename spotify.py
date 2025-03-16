import os
from venv import logger
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy
load_dotenv() 

class SpotifyAPI :
    sp = None

    def __init__(self):
        CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
        CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
        REDIRECT_URL = os.getenv('REDIRECT_URL')
        SCOPE = os.getenv('SPOTIFY_SCOPE')
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URL, scope=SCOPE))

    def get_playlists(self):
        try:
            playlists = self.sp.current_user_playlists()
            return playlists['items']
        except Exception as e:
            logger.error(f"Error during get_playlists: {e}")
        return []
    
    def get_playlist_tracks(self, playlist_id):
        try:
            results = self.sp.playlist_tracks(playlist_id)
            return results['items']
        except Exception as e:
            logger.error(f"Error during get_playlist_tracks: {e}")
        return []
    
    def get_artist_names_as_string(self, track):
        artists = track.get('artists', None)
        if (not artists):
            return artists
        artist_names = [artist['name'] for artist in artists]
        return ', '.join(artist_names)

    def get_playlist_track_details(self, playlist_id):
        tracks  = self.get_playlist_tracks(playlist_id)

        trackDetails = []
        for item in tracks:
            track = item.get('track', None)
            if track is None:
                continue

            if item['track'].get('type') == 'episode':
                continue
            artist_name = self.get_artist_names_as_string(track)
            track_name = track.get('name', None)

            if (not artist_name or not track_name):
                logger.warning(f"Could not find artist name/s or track name: {artist_name}, {track_name} ")
                continue

            trackDetails.append(f"{artist_name}: {track_name}")
        return trackDetails

