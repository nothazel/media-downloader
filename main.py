import os
import re
import threading
import configparser
from queue import Queue
from tkinter import messagebox
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp as youtube_dl
import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image
import unicodedata

# Global variables
terminate_download = False
downloaded_count = 0
download_queue = Queue()
app = None
downloading = False

# Initialize Spotify API
config = configparser.ConfigParser()
config.read('config.ini')
SPOTIFY_CLIENT_ID = config['spotify']['client_id']
SPOTIFY_CLIENT_SECRET = config['spotify']['client_secret']
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

source_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source')

# Utility Func
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

# GUI
def initialize_gui():
    global app, quality_menu
    app = ctk.CTk()
    center_window(app, 600, 800)
    app.title("Media Downloader")

    spotify_logo = CTkImage(Image.open(os.path.join(source_folder, "spotify_logo.png")), size=(20, 20))
    download_logo = CTkImage(Image.open(os.path.join(source_folder, "download_logo.png")), size=(20, 20))
    sanitize_logo = CTkImage(Image.open(os.path.join(source_folder, "sanitize_logo.png")), size=(20, 20))

    # URL Entry and Label
    url_label = ctk.CTkLabel(app, text="Enter YouTube URL or Music Name:")
    url_label.pack(pady=10)

    global url_entry
    url_entry = ctk.CTkEntry(app, width=500)
    url_entry.pack(pady=10)

    # Dropdown menu to select audio or video default
    global content_type_var
    content_type_var = ctk.StringVar(value="Audio")
    content_type_menu = ctk.CTkOptionMenu(app, variable=content_type_var, values=["Audio", "Video"], command=update_quality_menu)
    content_type_menu.pack(pady=10)

    # Dropdown menu for quality selection default
    global quality_var
    quality_var = ctk.StringVar(value="320bps")
    quality_menu = ctk.CTkOptionMenu(app, variable=quality_var, values=["320Kbps", "192Kbps", "128Kbps"])
    quality_menu.pack(pady=10)

    # Create buttons with logos
    button_frame = ctk.CTkFrame(app)
    button_frame.pack(pady=10)

    download_button = ctk.CTkButton(button_frame, image=download_logo, text="", command=on_download, width=40, height=40, corner_radius=10)
    download_button.pack(side=ctk.LEFT, padx=5)

    sanitize_button = ctk.CTkButton(button_frame, image=sanitize_logo, text="", command=on_sanitize, width=40, height=40, corner_radius=10)
    sanitize_button.pack(side=ctk.LEFT, padx=5)

    # Create Spotify button with the logo
    spotify_button = ctk.CTkButton(app, image=spotify_logo, text="", command=open_spotify_window, width=40, height=40, corner_radius=10)
    spotify_button.pack(pady=10)

    global progress_label
    progress_label = ctk.CTkLabel(app, text="")
    progress_label.pack(pady=10)

    global progress_percentage
    progress_percentage = ctk.CTkLabel(app, text="0% complete")
    progress_percentage.pack(pady=5)

    global progress_bar
    progress_bar = ctk.CTkProgressBar(app, width=500)
    progress_bar.pack(pady=10)
    progress_bar.set(0)

    global log_text
    log_text = ctk.CTkTextbox(app, width=500, height=300)
    log_text.pack(pady=10)

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

def update_quality_menu(choice):
    global quality_var, quality_menu
    if choice == "Audio":
        quality_var.set("320Kbps")
        quality_menu.configure(values=["320Kbps", "192Kbps", "128Kbps"])
    else:  # Video
        quality_var.set("2160p")
        quality_menu.configure(values=["2160p", "1440p", "1080p", "720p", "480p"])

# Spotify functions
def open_spotify_window():
    spotify_window = ctk.CTkToplevel(app)
    center_window(spotify_window, 300, 200)
    spotify_window.title("Spotify Downloader")
    spotify_window.wm_attributes("-topmost", 1)

    spotify_url_label = ctk.CTkLabel(spotify_window, text="Enter Spotify playlist URL:")
    spotify_url_label.pack(pady=10)

    spotify_url_entry = ctk.CTkEntry(spotify_window, width=250)
    spotify_url_entry.pack(pady=10)

    spotify_download_button = ctk.CTkButton(spotify_window, text="Download", command=lambda: on_download_spotify(spotify_url_entry.get()))
    spotify_download_button.pack(pady=10)

def extract_playlist_id(url):
    match = re.search(r'(playlist/|spotify:playlist:)([a-zA-Z0-9]+)', url)
    if match:
        return match.group(2)
    else:
        raise ValueError("Invalid Spotify playlist URL")

def fetch_spotify_playlist_tracks(playlist_url):
    try:
        playlist_id = extract_playlist_id(playlist_url)
        results = sp.playlist_tracks(playlist_id, limit=50)
        tracks = []
        log_message("Fetching Spotify playlist tracks...")
        while results:
            for item in results['items']:
                track = item['track']
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                tracks.append(f"{track_name} {artist_name}")
            log_message(f"{len(tracks)} tracks found so far...")
            if results['next']:
                results = sp.next(results)
            else:
                results = None
        log_message(f"Total of {len(tracks)} tracks found in the Spotify playlist.")
        return tracks
    except Exception as e:
        log_message(f"Error: {e}")
        return []

# Download functions
def download_content(query, content_type="audio"):
    global downloaded_count

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'downloads')
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': f'bestaudio/best' if content_type == "audio" else f'bestvideo[height<={int(quality_var.get()[:-1])}]+bestaudio/best',
        'default_search': 'auto' if "youtube.com" in query or "youtu.be" in query else 'ytsearch',
        'progress_hooks': [progress_hook],
        'noplaylist': False if "youtube.com" in query or "youtu.be" in query else True,
        'quiet': True,
        'outtmpl': os.path.join(output_dir, f"%(title)s.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality_var.get(),
        }] if content_type == "audio" else [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            log_message(f"Starting download: {query}")
            ydl.download([query])

            progress_label.configure(text="Download complete!")
            log_message("Download and conversion complete!")
            downloaded_count += 1

    except Exception as e:
        log_message(f"Download error: {e}")

    if download_queue.empty():
        log_message(f"Total of {downloaded_count} items downloaded.")

def progress_hook(d):
    global terminate_download
    if terminate_download:
        raise Exception("Download terminated by user")

    if d['status'] == 'downloading':
        try:
            progress_str = d.get('_percent_str', '0.00%')
            progress_percentage.configure(text=f"{progress_str} complete")
            progress = float(progress_str.replace('%', '').strip()) / 100.0
            progress_bar.set(progress)
        except Exception:
            pass
    elif d['status'] == 'finished':
        progress_bar.set(1)
        log_message("Download finished. Processing...")

# Utility functions
def log_message(message):
    log_text.insert(ctk.END, message + "\n")
    log_text.see(ctk.END)

def sanitize_filename(filename):
    replacements = {'Ö': 'O', 'Ç': 'C', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S'}
    nfkd_form = unicodedata.normalize('NFKD', filename)
    return ''.join(replacements.get(char, char) for char in nfkd_form if not unicodedata.combining(char))

def on_download():
    global terminate_download
    terminate_download = False
    query = url_entry.get().strip()
    if not query:
        messagebox.showerror("Error", "Please enter a valid URL or search query.")
        return

    content_type = content_type_var.get().lower()
    download_queue.put((query, content_type))
    start_download_thread()

def start_download_thread():
    global downloading
    if not downloading:
        downloading = True
        download_thread = threading.Thread(target=process_download_queue)
        download_thread.start()

def process_download_queue():
    global downloading
    while not download_queue.empty():
        query, content_type = download_queue.get()
        download_content(query, content_type)
    downloading = False

def on_sanitize():
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    for filename in os.listdir(downloads_dir):
        sanitized_name = sanitize_filename(filename)
        os.rename(os.path.join(downloads_dir, filename), os.path.join(downloads_dir, sanitized_name))
    log_message("Sanitization complete.")

def on_download_spotify(playlist_url):
    tracks = fetch_spotify_playlist_tracks(playlist_url)
    if tracks:
        for track in tracks:
            download_queue.put((track, "audio"))
        start_download_thread()

def on_closing():
    global terminate_download
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        terminate_download = True
        app.destroy()

if __name__ == "__main__":
    initialize_gui()
