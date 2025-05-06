from dotenv import load_dotenv
from youtube import YoutubeAPI
from spotify import SpotifyAPI
import logging
load_dotenv() 

spotify = SpotifyAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

youtube = YoutubeAPI()
existing_playlists = youtube.get_playlists()
existing_playlists_names = existing_playlists.keys()

# Display playlists and prompt user for selection
print("Available Spotify Playlists:")
playlist_names = list(playlist_tracks.keys())
for idx, name in enumerate(playlist_names, start=1):
    status = "(Added)" if name in existing_playlists_names else ""
    print(f"{idx}. {name} {status}")
print("0. Exit")

while True:
    try:
        selected_index = int(input("Enter the number of the playlist you want to add to YouTube (or 0 to exit): ")) - 1
        if selected_index == -1:
            print("Exiting...")
            exit(0)
        if selected_index < 0 or selected_index >= len(playlist_names):
            raise IndexError
        break
    except (ValueError, IndexError):
        print("Invalid selection. Please enter a valid number from the list.")

selected_playlist_name = playlist_names[selected_index]
selected_tracks = playlist_tracks[selected_playlist_name]


video_id_cache = {}
try:
    # create playlist
    playlist_id = existing_playlists.get(selected_playlist_name)

    if (playlist_id):
        logger.warning(f"Playlist {selected_playlist_name} already exists!") 
    else: 
        new_playlist = youtube.create_playlist(selected_playlist_name)
        playlist_id = new_playlist.get('id')
        if not new_playlist or not playlist_id:
            logger.error(f"Failed to create playlist {selected_playlist_name}")
            exit(1)
    # add tracks
    existing_item_ids = youtube.get_playlist_items(playlist_id)
    for track in selected_tracks:
        if track in video_id_cache:
            logger.info(f'Getting video id for "{track}" from cache...')
            video_id = video_id_cache[track]
        else: 
            video_id = youtube.get_video_id(track)
            if (not video_id):
                logger.warning(f'No video found for "{track}", skipping...')
                continue
            video_id_cache[track] = video_id
        if (video_id in existing_item_ids):
            logger.info(f'Video "{track}" already in list, skipping...')
            continue
        logger.info(f'Adding video "{track}"...')
        res = youtube.add_item_to_playlist(playlist_id=playlist_id, video_id=video_id )
        if not res:
            logger.error(f"Failed to add video.")
        else:
            logger.info(f'Video successfully added.')
except Exception as e:
    if 'quotaExceeded' in str(e):
        logger.error("YouTube Quota exceeded, stopping the app.")
        # quota resets at 4.30pm ADL time
    else:
        logger.error('An unknown error occurred:', e)

youtube_query_cost = youtube.get_query_cost()
spotify_query_count = spotify.get_query_count()
logger.info(f"Total spotify queries: {spotify_query_count}")
logger.info(f"Total youtube query cost: {youtube_query_cost}")