import json
import os
import subprocess
import cv2 as cv

from PIL import Image

def get_image_metadata(image_path):
    image = Image.open(image_path)
    width, height = image.size
    size = os.stat(image_path).st_size

    return width, height, size


def get_video_metadata(video_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration',
        '-of', 'json',
        video_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout

    metadata = json.loads(output)
    stream_info = metadata.get('streams', [{}])[0]

    duration = float(stream_info.get('duration', 0))
    width = int(stream_info.get('width', 0))
    height = int(stream_info.get('height', 0))
    size = os.stat(video_path).st_size

    return duration, width, height, size


def generate_video_thumbnail(video_path, thumbnail_path):
    # Open the video file
    print('video_path: ', video_path)
    print('thumbnail_path: ', thumbnail_path)
    vidcap = cv.VideoCapture(video_path)

    # Set the video capture position to 1 second (1000 milliseconds)
    vidcap.set(cv.CAP_PROP_POS_MSEC, 1000)

    # Read a frame from the video
    success, image = vidcap.read()

    # Check if the frame was read successfully
    if success:
        # Save the frame as a thumbnail image file
        cv.imwrite(thumbnail_path, image)
    else:
        print("Failed to read frame from video.")

    # Release the video capture object
    vidcap.release()
