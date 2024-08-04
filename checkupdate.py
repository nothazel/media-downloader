import os
import requests
import hashlib
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

MAIN_SCRIPT_SOURCE = "https://raw.githubusercontent.com/nothazel/media-downloader/main/main.py"

def get_remote_file_hash(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return hashlib.md5(response.content).hexdigest(), response.content
    except Exception as e:
        print(f"Error fetching file from {url}: {e}")
        return None, None

def get_local_file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def update_main_script(new_content):
    with open('main.py', 'wb') as f:
        f.write(new_content)
    print("main.py has been updated to the latest version.")

def ask_for_update():
    root = tk.Tk()
    root.withdraw()
    return messagebox.askyesno("Update Available", "A new version of the program is available. Do you want to update?")

def show_update_success_message():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Update Successful", "Successfully updated the program.")

def show_no_update_message():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Information", "The program is up to date.")

def check_for_updates():
    remote_hash, remote_content = get_remote_file_hash(MAIN_SCRIPT_SOURCE)
    if not remote_hash:
        return
    
    local_hash = get_local_file_hash('main.py')
    
    if local_hash != remote_hash:
        print("Newer version found.")
        if ask_for_update():
            update_main_script(remote_content)
            subprocess.Popen([sys.executable, 'main.py'])
            sys.exit()
        else:
            print("Update skipped.")
    else:
        show_no_update_message()

if __name__ == "__main__":
    check_for_updates()
