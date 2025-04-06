import os
import json
from venv import logger
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy
load_dotenv() 

CACHE_FILE = "caches/spotify_cache.json"

class SpotifyAPI :
    sp = None
    query_count = 0
    cache = {}

    def __init__(self):
        CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
        CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
        REDIRECT_URL = os.getenv('REDIRECT_URL')
        SCOPE = os.getenv('SPOTIFY_SCOPE')
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URL, scope=SCOPE))

        # Load cache
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                self.cache = json.load(f)

    def save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)

    def delete_cache(self):
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            self.cache = {}
            logger.info("Cache deleted successfully.")
        else:
            logger.warning("Cache file does not exist.")

    def get_playlists(self, include_unowned=False):
        cache_key = f"playlists_{include_unowned}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        all_playlists = []
        playlists = None
        try:
            while True:
                if playlists:
                    playlists = self.sp.next(playlists)
                else:
                    playlists = self.sp.current_user_playlists(limit=50)
                self.query_count += 1

                all_playlists.extend(playlists['items'])

                if not playlists['next']:
                    break

            if include_unowned:
                self.cache[cache_key] = all_playlists
                self.save_cache()
                return all_playlists

            user_id = self.sp.me()['id']
            user_playlists = [playlist for playlist in all_playlists if playlist['owner']['id'] == user_id]
            self.cache[cache_key] = user_playlists
            self.save_cache()
            return user_playlists
        except Exception as e:
            logger.error(f"Error during get_playlists: {e}")
        return []
    
    def get_playlist_tracks(self, playlist_id):
        if playlist_id in self.cache:
            return self.cache[playlist_id]

        try:
            results = self.sp.playlist_tracks(playlist_id)
            self.query_count += 1
            self.cache[playlist_id] = results['items']
            self.save_cache()
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
    
    def get_query_count(self):
        return self.query_count

