from venv import logger
from dotenv import load_dotenv

from youtube import YoutubeAPI
from spotify import SpotifyAPI
load_dotenv() 

spotify = SpotifyAPI()
youtube = YoutubeAPI()

def get_playlist_dicts():
    playlists = spotify.get_playlists()
    playlist_tracks = {}
    for playlist in playlists:
        playlist_name = playlist['name']
        tracks = spotify.get_playlist_track_details(playlist['id'])
        if (len(tracks) == 0):
            continue
        playlist_tracks[playlist_name] = tracks
    return playlist_tracks

playlist_tracks = get_playlist_dicts()
# for testing 
# with open("logs/playlist_data.json", "a") as f:
#     json.dump(str(playlist_tracks), f, indent=4)
#     f.write("\n")

existing_playlists = youtube.get_playlists()
existing_playlists_names = existing_playlists.keys()
video_id_cache = {}

try:
    for playlist_name, tracks in playlist_tracks.items():
        # create playlists
        playlist_id = existing_playlists.get(playlist_name)
        if (playlist_id):
            logger.info(f"Playlist {playlist_name} already exists!") # URL: {playlist_url}")
        else: 
            new_playlist = youtube.create_playlist(playlist_name)
            if not new_playlist or not new_playlist.get('id'):
                logger.error(f"Failed to create playlist {playlist_name}")
                continue
            logger.info("Created playlist", playlist_name)
            new_id = new_playlist.get('id')
            existing_playlists[new_playlist['snippet']['title']] = new_id

        # add tracks
        logger.info(f"Adding {len(tracks)} tracks to ", playlist_name)
        existing_item_ids = youtube.get_playlist_items(playlist_id)
        for track in tracks:
            if track in video_id_cache:
                logger.info(f'Getting video id for {track} from cache...')
                video_id = video_id_cache[track]
            else: 
                video_id = youtube.get_video_id(track)
                if (not video_id):
                    logger.info(f'No video found for {track}, skipping...')
                    continue
                video_id_cache[track] = video_id
            if (video_id in existing_item_ids):
                logger.info(f'Video {track} already in list, skipping...')
                continue
            logger.info(f'Adding video {track}...')
            res = youtube.add_item_to_playlist(playlist_id=playlist_id, video_id=video_id )
            if not res:
                logger.error(f"Failed to add video {track}.")
            else:
                logger.info(f'{track} successfully added.')
except Exception as e:
    if 'quotaExceeded' in str(e):
        logger.error("Quota exceeded, stopping the app.")
        # quota resets at 4.30pm ADL time

# TODO reduce requests to avoid exceeding youtube api query quota
