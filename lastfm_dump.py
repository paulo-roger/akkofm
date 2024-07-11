import os
import pylast
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Load configuration
LAST_API_KEY = os.getenv("LAST_API_KEY")
LAST_USER = os.getenv("LAST_USER")

# Create network and user objects
network = pylast.LastFMNetwork(api_key=LAST_API_KEY)
user = pylast.User(LAST_USER, network)

# Function to get the currently playing track
def now_listening():
    return user.get_now_playing()

# Function to get the last loved track
def last_loved():
    loved_tracks = user.get_loved_tracks(limit=1)
    return loved_tracks[0] if loved_tracks else None

# Function to save the track information to a text file
def save_tracks_to_file(file_path):
    current_track = now_listening()
    last_loved_track = last_loved()

    data = {
        "current_track": str(current_track) if current_track else "None",
        "last_loved_track": str(last_loved_track) if last_loved_track else "None",
        "timestamp": datetime.now(timezone.utc).isoformat()
        
    }

    with open(file_path, 'w') as file:
        for key, value in data.items():
            file.write(f"{key}: {value}\n")

    print("Track information saved to file.")

if __name__ == "__main__":
    save_tracks_to_file("lastfm_tracks.txt")
