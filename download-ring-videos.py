import json
import getpass
import time
import logging
import time
from pathlib import Path
from pprint import pprint

# https://github.com/tchellomello/python-ring-doorbell
from ring_doorbell import Ring, Auth, RingStickUpCam
from oauthlib.oauth2 import MissingTokenError

# Constants
STARTING_FROM_DING_ID = 7270130651641920309 # August 22, 8:59 AM, Beginning of digging
STOP_AT_DING_ID = 7270294388680145717 # Aug 22, Last Video # 7277219435034426165 <- Continue at CLOSE TO Sep 10, 3:28:05 PM. # Continue at 7333246501726698293 after reaching safe date buffer. OUTDATED BUT CLOSE TO: February 9, 11:32 AM, Enclosed extension
CAM_NAME = "High from Garage"
CHUNK_SIZE = 8192
MAX_RETRIES = 50
CACHE_FILE_PATH = Path("token.cache")
USER_AGENT = "ConstructionTimelapser/1.0"
RETRY_SLEEP_TIME = 5

logging.getLogger('ring_doorbell').setLevel(logging.DEBUG)


def token_updated(token):
    """Callback function to update token cache."""
    with CACHE_FILE_PATH.open('w') as cache_file:
        json.dump(token, cache_file)


def otp_callback():
    """Handle 2-factor authentication."""
    return input("2FA code (check your email/phone/authenticator): ")


def initialize_auth():
    """Initialize authentication."""
    if CACHE_FILE_PATH.is_file():
        with CACHE_FILE_PATH.open('r') as cache_file:
            auth_token = json.load(cache_file)
        return Auth(USER_AGENT, auth_token, token_updated)
    
    username = input("Enter your Ring email address: ")
    password = getpass.getpass("Password: ")
    auth = Auth(USER_AGENT, None, token_updated)

    try:
        auth.fetch_token(username, password)
    except MissingTokenError:
        auth.fetch_token(username, password, otp_callback())
    return auth


def download(cam: RingStickUpCam):
    """Download videos from a camera."""
    count = 0
    eid = STOP_AT_DING_ID

    while True:
        # Fetch the camera event history
        events = cam.history(older_than=eid, limit=CHUNK_SIZE)

        # Get amount of recordings
        recording_count = len(events)
        print(f'Found recordings count: {recording_count}')

        # Loop through the events and download each video (newest -> oldest)
        for event in events:
            eid = event['id']
            date = event['created_at'].strftime("%Y_%m_%d-%H_%M_%S")
            print(f'Downloading recording: {eid} @ {date}')

            if eid < STARTING_FROM_DING_ID:
                print(f'Reached the oldest event for {cam.name}!')
                return

            success = download_event(cam, eid, date)
            if success:
                count += 1
                print(f'Downloaded #{count} -> {eid}')
                # Delay between downloads
                time.sleep(1)


def download_event(cam: RingStickUpCam, eid, recordingDate):
    """Attempt to download a specific event. Returns True if successful."""
    retries = 0
    video_path = Path(f'videos/{cam.name}')
    video_path.mkdir(parents=True, exist_ok=True)

    while retries < MAX_RETRIES:
        try:
            cam.recording_download(eid, filename=video_path/f'{eid}_{recordingDate}.mp4')
            return True
        except Exception as e:
            if '404' in str(e):
                retries += 1
                print(f"[Not Ready Yet] Download failed for {eid}. Retrying {retries}/{MAX_RETRIES}...")
                time.sleep(RETRY_SLEEP_TIME)
            elif '504' in str(e):
                retries += 1
                print(f"[Gateway Timeout] Download failed for {eid}. Retrying {retries}/{MAX_RETRIES}...")
                time.sleep(RETRY_SLEEP_TIME)
            elif 'RemoteDisconnected' in str(e):
                retries += 1
                print(f"[Remote Disconnected] Download failed for {eid}. Retrying {retries}/{MAX_RETRIES}...")
                time.sleep(RETRY_SLEEP_TIME)
            else:
                retries += 1
                print(f"[Unrecognized Error] Download failed for {eid}. Retrying {retries}/{MAX_RETRIES}...")
                time.sleep(RETRY_SLEEP_TIME)
            
    print(f"- Failed to download {eid} after {MAX_RETRIES} attempts!")
    return False


def main():
    """Main function."""
    auth = initialize_auth()

    ring = Ring(auth)
    ring.update_data()

    devices = ring.devices()
    pprint(devices)

    # Find target camera by name
    targetCam = None
    for cam in devices['stickup_cams']:
        if cam.name == CAM_NAME:
            targetCam = cam
            break

    # Download recordings
    print(f'\nDownloading videos from {targetCam.name}...')
    download(targetCam)

    print('\nDONE.')


if __name__ == "__main__":
    main()