# spotify-to-youtube-playlists

Convert Spotify playlists to Youtube music video playlists

## Overview

Convert Spotify playlists into Youtube playlists. The converter searches Youtube for the first title and artist match, preferring music videos. 

## How to run

### Install Dependencies

```sh
pip install -r requirements.txt
```

### Setup Spotify Connection

1. Create a Spotify Developer account at https://developer.spotify.com/dashboard/applications
2. Create a new application and get the Client ID and Client Secret
3. Set the Redirect URI to `http://localhost:8888/callback`
4. Add the Client ID, Client Secret, and Redirect URI to your environment variables:
   ```sh
   export SPOTIFY_CLIENT_ID='your_client_id'
   export SPOTIFY_CLIENT_SECRET='your_client_secret'
   export SPOTIFY_REDIRECT_URI='http://localhost:8888/callback'
   ```

### Setup Google Connection

1. Create a Developer Account in Google Cloud Console https://console.cloud.google.com/
2. Create a new Project
3. Enable the YouTube Data API v3 for your project 'Apis & Services' '+ Enable APIs and Services' -> Enable YouTube Data API v3
4. IN 'APIs & Services' => 'Create credentials'
5. In 'APIs & Services' -> 'Credentials' -> "Configure Consent Screen". You will be prompted to create Google Auth Platform - > Create
6. Google Auth Platform -> OAuth Overview -> Create OAUTH client
   Select 'Web Application', in Authorized redirect URIs put "http://localhost:8888/"
7. In Google Auth Platform -> Audience --> add the users you want to use in 'Test users'
8. Set the path to the JSON file in your environment variables

### Run project

```sh
./main.py
```
If it's your first time running, you will be prompted to login to Spotify and Youtube.

You will be presented with a numbered list of playlists:

![image](https://github.com/user-attachments/assets/fee3a76e-ad20-474d-b39c-b4a9391abc55)

Choose a playlist to download by entering the corresponding number:

![image](https://github.com/user-attachments/assets/d6d2bf18-8ad9-4408-8ca3-5c1efdafe0ef)

Observe the magic:

![image](https://github.com/user-attachments/assets/d49e192a-121f-470b-8dc6-a6be72749310)

> [!NOTE]  
> Due to Youtube API's restrictive query quota (especially for search queries), I've added caching for query results. So if you have large playlists and hit the quota, you can try again the next day (or on another youtube api project) and it will only search for the missing songs. 
