import os
import sys
import configparser
import importlib.util
import subprocess

required_libraries = [
    'spotipy',
    'yt_dlp',
    'customtkinter',
    'pillow',
]

source_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source')

def check_setup():
    config_file = os.path.join(os.getcwd(), 'config.ini')
    config_exists = os.path.exists(config_file)
    if not config_exists:
        return False
    config = configparser.ConfigParser()
    config.read(config_file)
    return config.getboolean('Setup', 'completed', fallback=False)

def install_libraries():
    for lib in required_libraries:
        try:
            importlib.import_module(lib)
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

def create_shortcut():
    try:
        pythonw_executable = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        script_path = os.path.abspath('main.py')
        shortcut_path = os.path.join(os.path.dirname(script_path), "Media Downloader.lnk")

        if os.path.exists(shortcut_path):
            print(f"Shortcut already exists at: {shortcut_path}")
            return
        
        icon_path = os.path.join(source_folder, 'icon.ico')
        starting_directory = os.path.dirname(script_path)

        shortcut_command = (
            f'powershell.exe -Command "$ws = New-Object -ComObject WScript.Shell; '
            f'$sc = $ws.CreateShortcut(\'{shortcut_path}\'); '
            f'$sc.TargetPath = \'{pythonw_executable}\'; '
            f'$sc.Arguments = \'"\"{script_path}\""\'; '
            f'$sc.IconLocation = \'{icon_path},0\'; '
            f'$sc.WorkingDirectory = \'{starting_directory}\'; '
            f'$sc.Save()"'
        )
        
        result = subprocess.run(shortcut_command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            with open(os.path.join(starting_directory, 'shortcut_error.log'), 'w') as error_file:
                error_file.write(result.stderr)

    except Exception as e:
        with open(os.path.join(starting_directory, 'error.log'), 'w') as error_file:
            error_file.write(f"Error creating shortcut: {e}")

def main():
    setup_completed = check_setup()

    if not setup_completed:
        install_libraries()

        config_file = os.path.join(os.getcwd(), 'config.ini')
        config = configparser.ConfigParser()
        config.read(config_file)
        if not config.has_section('Setup'):
            config.add_section('Setup')
        config.set('Setup', 'completed', 'True')
        with open(config_file, 'w') as f:
            config.write(f)
        
    create_shortcut()

if __name__ == "__main__":
    main()
