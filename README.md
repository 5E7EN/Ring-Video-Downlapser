# Ring Timelapser

## How To Use

### Download Recordings

1. Log in to Ring website and get video ID of the recording to begin downloading from, and the video ID of the recording you want to stop downloading at.
    - You need what's called the "ding ID". You can get it by opening DevTools -> Network tab, clicking the download button after selecting the recording you want, selecting the download network request and navigating to the Payload tab. There you will find the recordings unique "ding ID".
2. In `download-ring-videos.py`, set the `STARTING_FROM_DING_ID`, `STOP_AT_DING_ID`, and `CAM_NAME` values respectively.
3. Begin downloading the videos within the specified range using `python download-ring-videos.py`.
4. When prompted, enter your Ring credentials (to be cached locally for future use in a `token.cache` file)
5. Practice patience...

### Timelapsing

1. Once the videos finish downloading, locate the camera footage you'd like to use in `videos/<cam-name>`, copy it into the `videos` folder, and rename the copy to "input". Alternatively, simply rename the cam name folder to "input".
2. Adjust the parameters/constants in the `create-timelapse-from-videos.py` script as desired
3. Run `python create-timelapse-from-videos.py`. This will extract all the necessary frames to the `frames` directory, then compile the final video to the `output` directory, saved as `timelapse.mp4` (by default).
4. Exercise patience...

Note: Following the frame extractions, you can manually trigger the timelapse creation without having to re-extract the frames by invoking the script with the `--only-timelapse` flag.
