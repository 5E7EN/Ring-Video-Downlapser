# Ring Timelapser

## How To Use

### Download Recordings

1. Log in to Ring website and get video ID of the recording to begin downloading from, and the video ID of the recording you want to stop downloading at.
    - You need what's called the "ding ID". You can get it by opening DevTools -> Network tab, clicking the download button after selecting the recording you want, selecting the download network request and navigating to the Payload tab. There you will find the recordings unique "ding ID".
2. In `download-ring-videos.py`, set the `STARTING_FROM_DING_ID` and `STOP_AT_DING_ID` values respectively.
3. Exercise patience...

### Timelapsing

1.
