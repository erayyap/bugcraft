import minecraft_launcher_lib
import subprocess
import sys
import os
import time
import win32gui
import win32con
import uuid  # Import the uuid module

# --- Configuration ---
# Replace with your desired Minecraft version
MINECRAFT_VERSION = "19w35a"

# Minecraft directory (default location)
minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()

# --- Microsoft Account Login (Optional) ---
USE_MICROSOFT_LOGIN = False  # Set to True to enable Microsoft login
CLIENT_ID = "YOUR_CLIENT_ID"  # Replace with your Azure Application Client ID
REDIRECT_URL = "YOUR_REDIRECT_URL"  # Replace with your Azure Application Redirect URL

# --- Functions ---

def microsoft_login():
    """Handles Microsoft account login flow."""
    login_url, state, code_verifier = minecraft_launcher_lib.microsoft_account.get_secure_login_data(CLIENT_ID, REDIRECT_URL)
    print(f"Please open {login_url} in your browser and copy the url you are redirected into the prompt below.")
    code_url = input("Paste the redirect URL here: ")

    try:
        auth_code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(code_url, state)
    except AssertionError:
        print("States do not match! Make sure you copied the URL correctly.")
        sys.exit(1)
    except KeyError:
        print("URL not valid. Make sure you copied the URL correctly.")
        sys.exit(1)

    login_data = minecraft_launcher_lib.microsoft_account.complete_login(CLIENT_ID, None, REDIRECT_URL, auth_code, code_verifier)
    return login_data

def set_always_on_top(hwnd):
    """Sets the window with the given handle to be always on top."""
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

# --- Main Script ---

# 1. Install Minecraft
try:
    print(f"Installing Minecraft version {MINECRAFT_VERSION}...")
    minecraft_launcher_lib.install.install_minecraft_version(MINECRAFT_VERSION, minecraft_directory)
    print(f"Minecraft {MINECRAFT_VERSION} installed successfully!")
except Exception as e:
    print(f"Error installing Minecraft: {e}")
    sys.exit(1)

# 2. Login (if enabled)
if USE_MICROSOFT_LOGIN:
    try:
        login_data = microsoft_login()
        print(f"Logged in as {login_data['name']}!")
        options = {
            "username": login_data["name"],
            "uuid": login_data["id"],
            "token": login_data["access_token"]
        }
    except Exception as e:
        print(f"Error during Microsoft login: {e}")
        sys.exit(1)
else:
    # Offline mode (generate a random UUID)
    offline_uuid = str(uuid.uuid4())  # Generate a random UUID
    options = {
        "username": "Player",  # You can set a default offline username here
        "uuid": offline_uuid,  # Use the generated UUID
        "token": ""   # Leave empty for offline mode
    }

# 3. Launch Minecraft
try:
    print(f"Launching Minecraft {MINECRAFT_VERSION}...")
    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(MINECRAFT_VERSION, minecraft_directory, options)

    # Start Minecraft (get process ID)
    process = subprocess.Popen(minecraft_command)
    pid = process.pid
    print(f"Minecraft launched! (PID: {pid})")

    """# Wait for the Minecraft window to appear (adjust sleep time as needed)
    time.sleep(5)

    # Find the Minecraft window by title
    def window_enum_handler(hwnd, result):
        if "Minecraft" in win32gui.GetWindowText(hwnd):
            result.append(hwnd)

    windows = []
    win32gui.EnumWindows(window_enum_handler, windows)
    minecraft_hwnd = windows[0] if windows else None

    if minecraft_hwnd:
        set_always_on_top(minecraft_hwnd)
        print("Minecraft window set to always on top.")
    else:
        print("Minecraft window not found.")"""

except Exception as e:
    print(f"Error launching Minecraft: {e}")
    sys.exit(1)