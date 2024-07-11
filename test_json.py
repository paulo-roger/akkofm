import os, pylast, logging, schedule, time, sys, requests, json
import xml.etree.ElementTree as ET
from pprint import pprint
from mastodon import Mastodon
from dotenv import load_dotenv
from datetime import datetime, timezone
from contextlib import contextmanager
from googleapiclient.discovery import build

load_dotenv()

# Configurações de log
logging.basicConfig(
  # filename='log.txt',
  format="[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt="%d/%m/%Y %H:%M:%S",
  level=logging.INFO
)

# Configurações de integração
LAST_API_KEY = os.getenv("LAST_API_KEY")
LAST_USER = os.getenv("LAST_USER")
MAST_ACC_TOKEN = os.getenv("MAST_ACC_TOKEN")
INSTANCE_URL = os.getenv("INSTANCE_URL")
NOWPLAYING = os.getenv("NOWPLAYING")
YT_API_KEY = os.getenv("YT_API_KEY")

# Create network and user objects once
network = pylast.LastFMNetwork(api_key=LAST_API_KEY)
user = pylast.User(LAST_USER, network)
mastodon = Mastodon(access_token=MAST_ACC_TOKEN, api_base_url=INSTANCE_URL, feature_set='pleroma')
youtube = build('youtube', 'v3', developerKey=YT_API_KEY)

last_posted_track = None  # Track the last posted toot

def find_metal_archives_entry(file_path):
  # Load the JSON data from the file
  with open(file_path, 'r') as file:
    data = json.load(file)
  
  # Initialize a variable to store the found entry
  metal_archives_entry = None
  
  # Iterate through the relations to find the metal-archives.com entry
  for relation in data.get("relations", []):
    url = relation.get("url", {}).get("resource", "")
    if "metal-archives.com" in url:
      metal_archives_entry = url
      break  # Stop searching once we find the first matching entry
  
  return metal_archives_entry

# Example usage
file_path = 'test.json'  # Path to your JSON file
result = find_metal_archives_entry(file_path)
print(result)


find_metal_archives_entry(file_path)
