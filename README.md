#Media Downloader

This Python script enables you to download audio / video from YouTube videos and Spotify playlists. It supports keyword searches, direct links for YouTube, and playlist URLs for Spotify.

## Requirements

- Python (duh)
- Spotify API Client Credentials (Optional) (If you want spotify functionality)
- `ffmpeg`  (go check tutorial if don't know how to install them) or [click this](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z)

## Installation for Spotify Command


 In `config.ini` file that is in the root directory of the script create the following:
 you can get your Spotify API Client Credentials from [Create Spotify App](https://developer.spotify.com/dashboard/create) Only tick Web API as we'll use only that and after that you can get your Credentials from Settings.
```
[spotify]

client_id = your_client_id

client_secret = your_client_secret
```

## Usage

Run `setup.py` file and wait for it to set the script up for first use. After "Media Downloader" shortcut is created move it to wherever you like.

