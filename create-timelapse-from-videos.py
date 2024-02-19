import os
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

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
    def sort_key(filename):
        try:
            return int(filename.split('_')[0])
        except ValueError:
            return 0
    
    return sorted(
        [f for f in os.listdir(directory) if f.endswith('.mp4')],
        key=sort_key,
    )


def extract_frame_from_video(video_file, idx, total_videos, input_directory, output_directory, extract_frame_every_n_seconds, progress_counter, progress_lock):
    """Extract frames every N seconds from a single video, with progress logging."""
    input_path = os.path.join(input_directory, video_file)
    output_path = os.path.join(output_directory, f"frame_{idx:05}_%04d.jpg")

    command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-i', input_path,
        '-vf', f'fps=1/{extract_frame_every_n_seconds}',
        output_path
    ]
    subprocess.call(command)
    
    with progress_lock:
        progress_counter.value += 1
        print(f'Progress: [{progress_counter.value}/{total_videos}] {video_file} processed.')


def extract_frames_from_videos_parallel(video_files, input_directory, output_directory, extract_frame_every_n_seconds):
    """Extract frames from videos in parallel with progress logging."""
    total_videos = len(video_files)
    manager = Manager()
    progress_counter = manager.Value('i', 0)
    progress_lock = manager.Lock()
    
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(extract_frame_from_video, video_file, idx, total_videos, input_directory, output_directory, extract_frame_every_n_seconds, progress_counter, progress_lock)
            for idx, video_file in enumerate(video_files)
        ]
        for future in futures:
            future.result()


def combine_frames_into_timelapse():
    """Combine frames to create the timelapse video."""
    with open(FRAMES_META_PATH, "w") as f:
        frames = sorted(
            [frame for frame in os.listdir(OUTPUT_FRAMES_DIRECTORY) if frame.endswith(".jpg")],
            key=lambda x: (int(x.split('_')[1]), int(x.split('_')[2].split('.')[0]))
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
    extract_frames_from_videos_parallel(video_files, INPUT_VIDEOS_DIRECTORY, OUTPUT_FRAMES_DIRECTORY, EXTRACT_FRAME_EVERY_N_SECONDS)
    end_time = time.time()
    print(f"Extracted all frames in {end_time - start_time:.2f} seconds.")
    
    combine_frames_into_timelapse()

if __name__ == '__main__':
    main()
