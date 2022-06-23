import os
import sys
from datetime import datetime, timedelta
from time import sleep, time

from dotenv import load_dotenv
from qbittorrentapi import Client, LoginFailed

load_dotenv()

HOSTNAME = os.environ["QBIT_HOSTNAME"]
PORT = os.environ.get("QBIT_PORT", "8080")
USERNAME = os.environ["QBIT_USERNAME"]
PASSWORD = os.environ["QBIT_PASSWORD"]
UPDATE_INTERVAL = int(os.environ.get("UPDATE_INTERVAL", 10))
SECONDS_SINCE_ADDED_CUTOFF = int(os.environ.get("SECONDS_SINCE_ADDED_CUTOFF", 1800))
SECONDS_SINCE_CREATED_CUTOFF = int(os.environ.get("SECONDS_SINCE_CREATED_CUTOFF", 3600))

print(f"Connecting to '{HOSTNAME}' at port '{PORT}' as user '{USERNAME}'")
client = Client(host=HOSTNAME, port=PORT, username=USERNAME, password=PASSWORD)
try:
    client.auth_log_in()
except LoginFailed as e:
    print(
        f"Error connecting to client. Could not connect to '{HOSTNAME}' at port '{PORT}' as user '{USERNAME}'"
    )
    print(e)
    sys.exit(e)

print(f"Connected!")
print(
    f"Checking status every {UPDATE_INTERVAL} seconds with age cutoff of {SECONDS_SINCE_ADDED_CUTOFF} seconds"
)

while True:
    for info in client.torrents_info(status_filter="stalled_downloading"):
        # Check if the torrent passes the time since added cutoff
        seconds_since_added = int(time() - info.added_on)
        if seconds_since_added > SECONDS_SINCE_ADDED_CUTOFF:
            continue

        # Check if the torrent passes the time since created cutoff
        properties = client.torrents_properties(torrent_hash=info.hash)
        seconds_since_created = int(time() - properties.creation_date)
        if seconds_since_created > SECONDS_SINCE_CREATED_CUTOFF:
            continue

        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        age = timedelta(seconds=seconds_since_added)
        print(
            f"{stamp}. Found stalled download, {info.hash[-6:]}: {info.name}, added {age} ago"
        )
        print("Attempting resume and re-announce")
        client.torrents_resume(info.hash)
        client.torrents_reannounce(info.hash)
    sleep(UPDATE_INTERVAL)
