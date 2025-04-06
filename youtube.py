from enum import Enum
import os
import json
from venv import logger
from dotenv import load_dotenv
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_FILE = "token.json"
CACHE_FILE = "caches/youtube_cache.json"

# https://developers.google.com/youtube/v3/determine_quota_cost
class QuotaCost(Enum):
    SEARCH = 100
    PLAYLISTS_LIST = 1  # playlist items have same quota cost as playlist
    PLAYLISTS_INSERT = 50
    VIDEO_LIST = 1


class YoutubeAPI: 
    youtube = None
    query_cost = 0
    cache = {}

    def __init__(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # local only

        API_SERVICE_NAME = "youtube"
        API_VERSION = "v3"
        CLIENT_SECRETS_FILE = "client_secret.json"
        REDIRECT_URL = os.getenv('REDIRECT_URL')

        credentials = None
        if (os.path.exists(TOKEN_FILE)):
            try:
                credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception as e:
                logger.error(f"Error loading credentials from file: {e}")
        if (not credentials or not credentials.valid):
            if (credentials and credentials.expired and credentials.refresh_token):
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
            else:
                try:
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        CLIENT_SECRETS_FILE, SCOPES)
                    flow.redirect_uri = REDIRECT_URL
                    credentials = flow.run_local_server(port=8888, access_type="offline", prompt='select_account')
                except Exception as e:
                    logger.error(f"Error during OAuth flow: {e}")
                    return
                
            try:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(credentials.to_json())
            except Exception as e:
                logger.error(f"Error saving credentials to file: {e}")

        self.youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

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


    def search(self, search_query) : 
        if search_query in self.cache:
            return self.cache[search_query]

        try:
            request = self.youtube.search().list(
                part="snippet",
                maxResults=1, 
                q=search_query
            )
            response = request.execute()
            self.query_cost += QuotaCost.SEARCH.value
            self.cache[search_query] = response
            self.save_cache()
            return response
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                raise e
        except Exception as e:
            logger.error(f"Error during search: {e}")
        return None
    
    def get_video_id(self, video_name):
        search = video_name  + " music video"
        search_results = self.search(search)
        if not search_results:
            return None
        items = search_results.get('items', None)
        if (not items or len(items) == 0):
            logger.warning('No videos found')
            return None
        # TODO - check if result is valid
        video = items[0]
        return video['id'].get('videoId')
    
    def get_playlists(self): 
        playlist_ids = {}
        next_page_token = None
        
        while True:
            try:
                request = self.youtube.playlists().list(
                    part= "snippet",
                    mine=True,
                    maxResults = 50,
                    pageToken= next_page_token
                )
                response = request.execute()
                self.query_cost += QuotaCost.PLAYLISTS_LIST.value
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                    raise e
                logger.error(f"Error during get_playlists: {e}")
                exit(1)
            except Exception as e:
                logger.error(f"Error during get_playlists: {e}")
                exit(1)

            for item in response['items']:
                playlist_name = item['snippet']['title']
                playlist_ids[playlist_name] = item['id']
            next_page_token = response.get('nextPageToken')
            if (not next_page_token):
                break
        return playlist_ids
    
    def get_playlist_items(self, playlist_id):
        if playlist_id in self.cache:
            return self.cache[playlist_id]

        item_ids = []
        next_page_token = None

        while True:
            try:
                request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                self.query_cost += QuotaCost.PLAYLISTS_LIST.value
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                    raise e
                logger.error(f"Error during get_playlist_items: {e}")
                break
            except Exception as e:
                logger.error(f"Error during get_playlist_items: {e}")
                break

            for item in response['items']:
                video_id = item['contentDetails']['videoId']
                item_ids.append(video_id)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        self.cache[playlist_id] = item_ids
        self.save_cache()
        return item_ids
    
    def create_playlist(self, playlist_name):
        try:
            request = self.youtube.playlists().insert(
                part="snippet",
                body={
                    "snippet": {
                        "title": playlist_name
                    }
                }
            )
            response = request.execute()
            self.query_cost += QuotaCost.PLAYLISTS_INSERT.value
            return response
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                raise e
            logger.error(f"Error during create_playlist: {e}")
        except Exception as e:
            logger.error(f"Error during create_playlist: {e}")
        return None
    
    def add_item_to_playlist(self, playlist_id, video_id):
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            response = request.execute()
            self.query_cost += QuotaCost.PLAYLISTS_INSERT.value
            return response
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
                raise e
            logger.error(f"Error during add_item_to_playlist: {e}")
        except Exception as e:
            logger.error(f"Error during add_item_to_playlist: {e}")
        return None

    def get_query_cost(self):
        return self.query_cost