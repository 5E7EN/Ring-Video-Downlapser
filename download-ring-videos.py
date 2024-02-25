import json
import getpass
import time
import logging
import time
import os
import concurrent.futures
from pathlib import Path
from pprint import pprint

# https://github.com/tchellomello/python-ring-doorbell
from ring_doorbell import Ring, Auth, RingStickUpCam
from oauthlib.oauth2 import MissingTokenError

# Constants
STARTING_FROM_DING_ID = 0
STOP_AT_DING_ID = 0
CAM_NAME = ""
CHUNK_SIZE = 10000
MAX_THREADS = 10
CACHE_FILE_PATH = Path("token.cache")
USER_AGENT = "RingTimelapser/1.0"
MAX_RETRIES = 50
RETRY_SLEEP_TIME = 5

logging.getLogger('ring_doorbell').setLevel(logging.INFO)


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
    """Download videos from a camera with thread pool to limit max threads."""
    count = 0
    eid = STOP_AT_DING_ID

    while True:
        # Fetch the camera event history
        events = cam.history(older_than=eid, limit=CHUNK_SIZE)

        # Get amount of recordings
        recording_count = len(events)
        logging.info(f'Found {recording_count} recordings.')

        if recording_count == 0:
            logging.info("No more recordings found.")
            break

        # Download events using ThreadPoolExecutor to manage concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Prepare the tasks
            tasks = {executor.submit(download_event, cam, event['id'], event['created_at'].astimezone().strftime("%Y_%m_%d-%H_%M_%S")): event for event in events}
            
            for future in concurrent.futures.as_completed(tasks):
                eid = tasks[future]['id']
                try:
                    success = future.result()
                    if success:
                        logging.info(f'Successfully downloaded recording: {eid}')
                    else:
                        logging.error(f'Failed to download recording: {eid}')
                except Exception as exc:
                    logging.error(f'An error occurred while downloading recording: {eid}. Error: {exc}')

                # Update eid to fetch older events in the next iteration
                if eid < STARTING_FROM_DING_ID:
                    logging.info(f'Reached the oldest event for {cam.name}!')
                    return

                # Add a delay between each thread execution
                time.sleep(1)  # Adjust delay time as needed

def download_event(cam: RingStickUpCam, eid, recordingDate):
    """Attempt to download a specific event. Returns True if successful."""
    retries = 0
    video_path = Path(f'videos/{cam.name}')
    video_path.mkdir(parents=True, exist_ok=True)
    file_path = video_path / f'{eid}_{recordingDate}.mp4'

    # Check if file already exists
    if os.path.isfile(file_path):
        print(f"- Skipping download for {eid}_{recordingDate}.mp4 as it already exists.")
        return True

    while retries < MAX_RETRIES:
        try:
            print(f"[-] Downloading {eid}...")
            cam.recording_download(eid, filename=file_path)
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
