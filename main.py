
import json
import os
from dotenv import load_dotenv

from youtube import YoutubeAPI
from spotify import SpotifyAPI
load_dotenv() 

spotity = SpotifyAPI()
youtube = YoutubeAPI()

def get_playlist_dicts():
    playlists = spotity.get_playlists()
    playlist_tracks = {}
    for playlist in playlists:
        playlist_name = playlist['name']
        tracks = spotity.get_playlist_track_details(playlist['id'])
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

for playlist_name, tracks in playlist_tracks.items():
    # create playlists
    playlist_id = existing_playlists.get(playlist_name)
    if (playlist_id):
        # playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        print(f"playlist {playlist_name} already exists!") # URL: {playlist_url}")
    else: 
        new_playlist = youtube.create_playlist(playlist_name)
        print("created playlist", playlist_name)
        new_id = new_playlist.get('id')
        if (not new_id) :
            print("Something went wrong creating playlist!!") 
            continue
        else :
            existing_playlists[new_playlist['snippet']['title']] = new_id

    # add tracks
    print(f"adding {len(tracks)} tracks to ", playlist_name)
    print(f"id is {existing_playlists[playlist_name]}")
    existing_item_ids = youtube.get_playlist_items(playlist_id)
    for track in tracks:
        if track in video_id_cache:
            print(f'getting video id for {track} from cache...')
            video_id = video_id_cache[track]
        else: 
            video_id = youtube.get_video_id(track)
            if (not video_id):
                print(f'not video found for {track}, skipping...')
                continue
            video_id_cache[track] = video_id
        if (video_id in existing_item_ids):
            print(f'video {track} already in list, skipping...')
            continue
        print(f'adding video {track}...')
        res = youtube.add_item_to_playlist(playlist_id=playlist_id, video_id=video_id )
        print(res)

# TODO reduce requests to avoid exceeding youtube api quota

# Possible enhancements
# - delete vidoes if no longer in spotify list
