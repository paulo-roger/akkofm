import os, pylast, logging, schedule, time, sys
from pprint import pprint
from mastodon import Mastodon
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()

# Configurações de log
logging.basicConfig(
  format="[%(asctime)s] [%(levelname)s] %(message)s",
  datefmt="%d/%m/%Y %H:%M:%S",
  level=logging.INFO
)

# Configurações de integração
LAST_API_KEY   = os.getenv("LAST_API_KEY")
MAST_ACC_TOKEN = os.getenv("MAST_ACC_TOKEN")
INSTANCE_URL   = os.getenv("INSTANCE_URL")
NOWPLAYING     = os.getenv("NOWPLAYING")
#'Last played'

# Verifica o que está sendo ouvido
def now_listening_str():
  network = pylast.LastFMNetwork(api_key=LAST_API_KEY)
  user = pylast.User(os.getenv("LAST_USER"), network)
  now_playing = user.get_now_playing()
  if not now_playing: return None
  track_name = now_playing.get_title()
  artist_name = now_playing.get_artist().get_name()
  return track_name + ' - ' + artist_name 

# Verifica o ultimo like
def last_loved_str():
  if now_listening_str() is None: return None
  now = datetime.now(timezone.utc).timestamp()
  network = pylast.LastFMNetwork(api_key=LAST_API_KEY)
  user = pylast.User(os.getenv("LAST_USER"), network)
  loved = user.get_loved_tracks(limit=1)
  loved_timestamp = float(loved[0].timestamp)
  if now - loved_timestamp > 80: return None
  track_name =  str(loved[0].track.title)
  artist_name = str(loved[0].track.artist)
  return track_name + ' - ' + artist_name

# Inclui o que está sendo ouvido nos campos extras (Mudei)
def update_fields():
  if now_listening_str() is None: return None
  mastodon = Mastodon(access_token=MAST_ACC_TOKEN, api_base_url=INSTANCE_URL)
  profile_fields = mastodon.account_verify_credentials()['source']['fields']
  has_now_listening_field = False
  for row in profile_fields:
    # del row['verified_at']
    if row['name'] == NOWPLAYING:
      has_now_listening_field = True
      row['value'] = now_listening_str()

  if not has_now_listening_field:
    profile_fields.append({ 'name': NOWPLAYING, 'value': now_listening_str()})
  new_profile_fields = [row for row in profile_fields if row['value'] is not None]
  new_profile_tuples = [tuple(row.values()) for row in new_profile_fields]
  result = mastodon.account_update_credentials(fields = new_profile_tuples)
  return result

# Posta se eu amei a musica
def toot_nowplaying():
  if last_loved_str() is None: return None
  mastodon = Mastodon(access_token=MAST_ACC_TOKEN, api_base_url=INSTANCE_URL)
  toot = last_loved_str() + "\n\n" + "#NowPlaying #LovedTrack"
  result = mastodon.status_post(toot)
  return result

# Classe que oculta o output de prints subordinados a ela
class HiddenPrints:
  def __enter__(self):
    self._original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

  def __exit__(self, exc_type, exc_val, exc_tb):
    sys.stdout.close()
    sys.stdout = self._original_stdout

# Trabalho que executa o código principal do bot
def run():
  print("NowPlaying: ")
  logging.info(now_listening_str())
  print("Loved: ")
  logging.info(last_loved_str())
  print("Toot: ")
  logging.info(toot_nowplaying())
  with HiddenPrints():
    pprint(update_fields())

def main():
  # Informa que a execução está operacional
  logging.info("O bot está em funcionamento.\n")
  # Executa os trabalhos no início da execução, antes dos agendamentos
  run()
  # Agenda a execução do trabalho acima
  schedule.every(30).seconds.do(run)

  # Loop para verificar agendamentos e executá-los
  while True:
    logging.info("Verificando agendamentos")
    schedule.run_pending()
    time.sleep(60)

if __name__ == "__main__":
  while True:
    try:
      main()
    except pylast.WSError as e:
      logging.error(f"Encountered a WSError: {e}. Restarting in 10 seconds...")
      time.sleep(10)  # Wait 10 seconds before restarting
    except Exception as e:
      logging.error(f"Unexpected error: {e}. Restarting in 10 seconds...")
      time.sleep(10)  # Wait 10 seconds before restarting
