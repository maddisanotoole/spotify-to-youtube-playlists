import os
from dotenv import load_dotenv
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.http import BatchHttpRequest
# TODO implement batch requests 

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_FILE = "token.json" 
class YoutubeAPI: 
    youtube = None

    def __init__(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # local only

        API_SERVICE_NAME = "youtube"
        API_VERSION = "v3"
        CLIENT_SECRETS_FILE = "client_secret.json"
        REDIRECT_URL = os.getenv('REDIRECT_URL')

        credentials = None
        if (os.path.exists(TOKEN_FILE)):
            credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if (not credentials or not credentials.valid):
            if (credentials and credentials.expired and credentials.refresh_token):
                credentials.refresh(Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES)
                flow.redirect_uri = REDIRECT_URL
                credentials = flow.run_local_server(port=8888, access_type="offline", prompt='select_account')
                
            with open(TOKEN_FILE, 'w') as token:
                token.write(credentials.to_json())

        self.youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

    def search(self, search_query) : 
        request = self.youtube.search().list(
        part="snippet",
        maxResults=1, 
        q=search_query
        )
        response = request.execute()
        return(response)
    
    def get_video_id(self, video_name):
        search = video_name  + " music video"
        print(f"searching for {search}...")
        search_results = self.search(search)
        items = search_results.get('items', None)
        if (not items or len(items) == 0):
            print('No videos found')
            return None
        # TODO - check if result is valid
        video = items[0]
        # print("video", video)
        return video['id']['videoId']
    
    def get_playlists(self): 
        playlist_ids = {}
        next_page_token = None
        
        while True:
            request = self.youtube.playlists().list(
                part= "snippet",
                mine=True,
                maxResults = 50,
                pageToken= next_page_token
            )
            
            response = request.execute()

            for item in response['items']:
                playlist_name = item['snippet']['title']
                playlist_ids[playlist_name] = item['id']
            next_page_token = response.get('nextPageToken')
            if (not next_page_token):
                break
        return playlist_ids
    
    def get_playlist_items(self, playlist_id):
        item_ids = []
        next_page_token = None

        while True:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response['items']:
                video_id = item['contentDetails']['videoId']
                item_ids.append(video_id)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return item_ids
    
    def create_playlist(self, playlist_name):
        request = self.youtube.playlists().insert(
            part="snippet",
            body={
                "snippet": {
                    "title": playlist_name
                }
            }
        )
        response = request.execute()
        return response
    
    def add_item_to_playlist(self, playlist_id, video_id):
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
        return response