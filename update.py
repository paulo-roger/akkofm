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

# Verifica o que está sendo ouvido
def now_listening_str():
  now_playing = user.get_now_playing()
  if not now_playing:
    return None

  track_info = {
    "playing": now_playing.get_title() + " - " + now_playing.get_artist().get_name(),
    "track_name": now_playing.get_title(),
    "album": now_playing.get_album().get_title() if now_playing.get_album() else None,
    "artist_name": now_playing.get_artist().get_name(),
    "cover_art": now_playing.get_cover_image(),
    # "correction": now_playing.get_correction(),
    # "tags": now_playing.get_tags(), # deu erro
    # "wiki": now_playing.get_wiki_content(),
    "album_mbid": now_playing.get_album().get_mbid(),
    "track_mbid": now_playing.get_mbid(),
    "top_tags": now_playing.get_top_tags() if now_playing.get_top_tags() else None
  }

  return track_info

# Verifica o ultimo like
def last_loved_str(current_track):
  if current_track is None: return None
  now = datetime.now(timezone.utc).timestamp()
  loved = user.get_loved_tracks(limit=1)
  loved_timestamp = float(loved[0].timestamp)
  track_name = str(loved[0].track.title)
  artist_name = str(loved[0].track.artist)
  current_loved_track = track_name + ' - ' + artist_name
  # if 0 <= (now - loved_timestamp) < 120 and current_loved_track == current_track:
  if 0 <= (now - loved_timestamp) < 60 and current_loved_track == current_track['playing']:
    return current_track
  else: return None

# Inclui o que está sendo ouvido nos campos extras (Mudei)
def update_fields(track):
  profile_fields = mastodon.account_verify_credentials()['source']['fields']
  
  if track is None:
    for row in profile_fields:
      if row['name'] == NOWPLAYING:
        row['name'] = 'Last played'
  
  else: 
    current_track = track['playing']
    has_now_listening_field = False
    for row in profile_fields:
      if row['name'] == 'Last played' or row['name'] == NOWPLAYING:
        has_now_listening_field = True
        row['name'] = NOWPLAYING
        row['value'] = current_track

    if not has_now_listening_field:
      profile_fields.append({'name': NOWPLAYING, 'value': current_track})

  new_profile_fields = [row for row in profile_fields if row['value'] is not None]
  new_profile_tuples = [tuple(row.values()) for row in new_profile_fields]
  result = mastodon.account_update_credentials(fields=new_profile_tuples)
  return result

def youtube_search(query):
  request = youtube.search().list(
    part="snippet",
    maxResults=1,  # Number of results to return
    q=query,        # The search query term
    type="video",   # We only want videos
    videoCategoryId="10"  # Music category
  )
  response = request.execute()
  first_item = response['items'][0]
  video_id = first_item['id']['videoId']
  video_url = f"https://www.youtube.com/watch?v={video_id}"
  return video_url

def songwhip(link):
  url = "https://songwhip.com/"
  data = { "url": link }

  try:
    # Make the POST request
    response = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    
    # Check if the request was successful
    if response.status_code == 200:
      response_data = response.json()
      songwhip_url = response_data.get('url', link)  # Get 'url' from response, fallback to link if not found
      print("Request was successful!")
      print("Response Data:", songwhip_url)
      return songwhip_url
    else:
      print("Songwhip: Request failed with status code:", response.status_code)
      print("Songwhip: Response Content:", response.text)
      return link
  except requests.exceptions.RequestException as e:
    # Handle any request exceptions
    print(f"Songwhip: Request failed with exception: {e}")
    return link

def metal_archives(type, query):
  base_url = 'https://metal-api.dev/'  # Replace with the actual base URL of the API
  
  if type == 'band':
    endpoint = f'/search/bands/name/{query}'
  if type == 'album':
    endpoint = f'/search/albums/title/{query}'

  url = f'{base_url}{endpoint}'
    
  try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes
    query_data = response.json()
    print(query_data)
    return query_data
  except requests.exceptions.RequestException as e:
    print(f'Error: {e}')
    return None

def get_artist_mbid(mbid, type='release'):
  """
  Retrieve the link for the artist of an album from MusicBrainz using the MusicBrainz API.
  
  :param album_mbid: The MusicBrainz ID of the album.
  :return: The URL of the artist on MusicBrainz, or None if not found.
  """
  if mbid is None:
    return None

  base_url = "https://musicbrainz.org/ws/2/"
  url = f"{base_url}{type}/{mbid}?inc=artists&fmt=json"
    
  try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
      
    # Extract artist information
    if 'artist-credit' in data and len(data['artist-credit']) > 0:
      artist_mbid = data['artist-credit'][0]['artist']['id']
      return artist_mbid
    else:
      print(f"No artist found for album with MBID: {mbid}")
      return None
    
  except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    return None

def get_ma_url(artist_mbid):
  if artist_mbid is None:
    print("Artist MBID is None.")
    return None

  base_url = "https://musicbrainz.org/ws/2/"
  url = f"{base_url}artist/{artist_mbid}?inc=url-rels&fmt=json"

  print(url)

  try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()    
    # Initialize a variable to store the found entry
    metal_archives_entry = "String Initialized"
    # Iterate through the relations to find the metal-archives.com entry
    for relation in data.get("relations", []):
      url = relation.get("url", {}).get("resource", "")
      if "metal-archives.com" in url:
        metal_archives_entry = url
        break  # Stop searching once we find the first matching entry    
    return metal_archives_entry

  except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    return None

# Posta se eu amei a musica
def toot_nowplaying(current_loved_track):
  global last_posted_track
  if current_loved_track is None or current_loved_track == last_posted_track:
    return None

  youtube_link = youtube_search(current_loved_track['playing'])
  link = songwhip(youtube_link)

  album_mbid = current_loved_track['album_mbid']
  track_mbid = current_loved_track['track_mbid']
  if album_mbid:
    artist_mbid = get_artist_mbid(album_mbid)
  else: artist_mbid = get_artist_mbid(track_mbid, 'recording')
  
  metal_archives_string = top_tag = top_tag2 = ""

  track = current_loved_track['track_name']
  album = current_loved_track['album']
  artist = current_loved_track['artist_name']
  artist_no_space = current_loved_track['artist_name'].replace(" ", "")
  cover_art = current_loved_track['cover_art']
  if current_loved_track['top_tags']:
    top_tag = current_loved_track['top_tags'][0].item.get_name().title().replace(" ", "")
    top_tag2 = current_loved_track['top_tags'][1].item.get_name().title().replace(" ", "")

  if artist_mbid:
    ma_link = get_ma_url(artist_mbid)
    print("============================\nMetal Archives: ", ma_link)
    if ma_link:
      metal_archives_string = f"<br>:metalarchives: <a href='{ma_link}'>[{artist} on metal-archives]</a><br>"
    artist = f"<a href='https://musicbrainz.org/artist/{artist_mbid}'>{artist}</a>"
  if album_mbid:
    album = f"<a href='https://musicbrainz.org/release/{album_mbid}'>{album}</a>"

  hashtags_list = ['NowPlaying', artist_no_space, top_tag, top_tag2, 'Music', 'LovedTrack']
  # Initialize an empty string to store the result
  hashtags_string = "<br>"
  # Iterate through the hashtags list
  for tag in hashtags_list:
    # Check if the tag is not empty
    if tag:
      # Append the tag with a leading # and a trailing space
      hashtags_string += f"#{tag} "
  # Remove the trailing space
  hashtags_string = hashtags_string.strip()

  # toot = f"<a href='{youtube_link}'><strong>{current_loved_track['playing']}</strong></a> <br><br> #NowPlaying #LovedTrack"
  toot = f"🎵 Now Playing: <a href='{link}'><strong>{track}</strong></a> by <strong>{artist}</strong><br>\
💽 Album: <strong>{album}</strong><br>" 

  toot = toot + metal_archives_string + hashtags_string

#   toot = f"<table><tr>\
# <td><img src='{cover_art}' alt='{album} cover' width='80px'></td>\
# <td>&nbsp;&nbsp;&nbsp;</td><td>\
# 🎵 <b>Now Playing:</b> {track} by {artist} <br>\
# 💽 <b>Album:</b> {album} <br>\
# ▶️ <b>Listen:</b> <a href='{link}'>[Song link]</a><br><br></td></tr></table>\
# <br>#NowPlaying #{artist_no_space} #{top_tag} #Music #LovedTrack"

  result = mastodon.status_post(toot, content_type='text/html')
  last_posted_track = current_loved_track  # Update the last posted track
  return result

# Classe que oculta o output de prints subordinados a ela
@contextmanager
def hidden_prints():
  original_stdout = sys.stdout
  sys.stdout = open(os.devnull, 'w')
  try:
    yield
  finally:
    sys.stdout.close()
    sys.stdout = original_stdout

# Trabalho que executa o código principal do bot
def run():
  current_track = now_listening_str()
  current_loved_track = last_loved_str(current_track)

  print("\n")
  print("NowPlaying: ")
  logging.info(current_track)
  print("Loved: ")
  logging.info(current_loved_track)
  print("Toot: ")
  logging.info(toot_nowplaying(current_loved_track))
  print("=========== End Cycle ===========\n\n")

  with hidden_prints():
    pprint(update_fields(current_track))

def main():
  # Informa que a execução está operacional
  logging.info("O bot está em funcionamento.\n")

  # Loop para verificar agendamentos e executá-los
  while True:
    try:
      run()
    except pylast.WSError as e:
      logging.error(f"\n\nEncountered a WSError: {e}. Restarting in 10 seconds...")
      time.sleep(10)  # Wait 10 seconds before restarting
      continue
    except Exception as e:
      logging.error(f"\n\nUnexpected error: {e}. Restarting in 10 seconds...")
      time.sleep(10)  # Wait 10 seconds before restarting
      continue
    time.sleep(45)  # Sleep for a short time to allow schedule to run

main()
