import os
import subprocess
import time

# Constants
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
VIDEOS_PATH = os.path.join(DIR_PATH, 'videos')
INPUT_VIDEOS_DIRECTORY = os.path.join(VIDEOS_PATH, 'input')
OUTPUT_FRAMES_DIRECTORY = os.path.join(VIDEOS_PATH, 'frames')
OUTPUT_VIDEOS_DIRECTORY = os.path.join(VIDEOS_PATH, 'output')
FRAMES_META_PATH = os.path.join(OUTPUT_FRAMES_DIRECTORY, 'frames.txt')
OUTPUT_TIMELAPSE_PATH = os.path.join(OUTPUT_VIDEOS_DIRECTORY, 'timelapse.mp4')

EXTRACT_FRAME_EVERY_N_SECONDS = 15
TIMELAPSE_FPS = 30


def ensure_directories_exist():
    """Ensure output directories exist."""
    if not os.path.exists(OUTPUT_FRAMES_DIRECTORY):
        os.makedirs(OUTPUT_FRAMES_DIRECTORY)
    if not os.path.exists(OUTPUT_VIDEOS_DIRECTORY):
        os.makedirs(OUTPUT_VIDEOS_DIRECTORY)


def get_video_files(directory):
    """Retrieve sorted video files from a given directory."""
    return sorted(
        [f for f in os.listdir(directory) if f.endswith('.mp4')],
        key=lambda x: int(os.path.splitext(x)[0]),
    )


def extract_frames_from_videos(video_files):
    """Extract frames every N seconds from each video."""
    for idx, video_file in enumerate(video_files):
        input_path = os.path.join(INPUT_VIDEOS_DIRECTORY, video_file)
        output_path = os.path.join(OUTPUT_FRAMES_DIRECTORY, f"frame_{idx:04}_%04d.jpg")

        print(f'{idx + 1}/{len(video_files)} - Extracting frames from {video_file}')

        command = [
            'ffmpeg', 
            '-loglevel', 'error',
            '-i', input_path,
            '-vf', f'fps=1/{EXTRACT_FRAME_EVERY_N_SECONDS}',
            output_path
        ]
        subprocess.call(command)


def combine_frames_into_timelapse():
    """Combine frames to create the timelapse video."""
    with open(FRAMES_META_PATH, "w") as f:
        frames = sorted(
            [frame for frame in os.listdir(OUTPUT_FRAMES_DIRECTORY) if frame.endswith(".jpg")]
        )

        for frame in frames:
            f.write(f"file '{os.path.join(OUTPUT_FRAMES_DIRECTORY, frame)}'\n")

    command = [
        'ffmpeg', 
        '-f', 'concat',
        '-r', str(TIMELAPSE_FPS),
        '-safe', '0',
        '-i', FRAMES_META_PATH,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        OUTPUT_TIMELAPSE_PATH,
    ]
    subprocess.call(command)


def main():
    ensure_directories_exist()

    video_files = get_video_files(INPUT_VIDEOS_DIRECTORY)
    print(f"Found {len(video_files)} video files.")

    start_time = time.time()
    extract_frames_from_videos(video_files)
    end_time = time.time()
    print(f"Extracted all frames in {end_time - start_time:.2f} seconds.")
    
    combine_frames_into_timelapse()

if __name__ == '__main__':
    main()
