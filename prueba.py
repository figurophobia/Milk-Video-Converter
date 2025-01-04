import os
import random
import sys
import cv2
from PIL import Image
from multiprocessing import Pool, cpu_count
import argparse
import subprocess

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def probably(chance):
    return random.random() < chance

def apply_filter_to_frame(frame_path, compress, comp_level, pointillism, filter_choice):
    if pointillism:
        punt = 70
    else:
        punt = 100

    imag = Image.open(frame_path)
    imag = imag.convert('RGB')

    if compress:
        imag.save("temp.jpg", quality=100-comp_level)
        imag = Image.open("temp.jpg")

    width, height = imag.size

    if filter_choice == 1:
        for x in range(width):
            for y in range(height):
                pixelRGB = imag.getpixel((x, y))
                R, G, B = pixelRGB
                brightness = sum([R, G, B]) / 3
                if brightness <= 25:
                    imag.putpixel((x, y), (0, 0, 0, 255))
                elif brightness > 25 and brightness <= 70:
                    if probably(punt / 100):
                        imag.putpixel((x, y), (0, 0, 0, 255))
                    else:
                        imag.putpixel((x, y), (102, 0, 31, 255))
                elif brightness > 70 and brightness < 120:
                    if probably(punt / 100):
                        imag.putpixel((x, y), (102, 0, 31, 255))
                    else:
                        imag.putpixel((x, y), (0, 0, 0, 255))
                elif brightness >= 120 and brightness < 200:
                    imag.putpixel((x, y), (102, 0, 31, 255))
                elif brightness >= 200 and brightness < 230:
                    if probably(punt / 100):
                        imag.putpixel((x, y), (137, 0, 146, 255))
                    else:
                        imag.putpixel((x, y), (102, 0, 31, 255))
                else:
                    imag.putpixel((x, y), (137, 0, 146, 255))
    else:
        for x in range(width):
            for y in range(height):
                pixelRGB = imag.getpixel((x, y))
                R, G, B = pixelRGB
                brightness = sum([R, G, B]) / 3
                if brightness <= 25:
                    imag.putpixel((x, y), (0, 0, 0, 255))
                elif brightness > 25 and brightness <= 70:
                    if probably(punt / 100):
                        imag.putpixel((x, y), (0, 0, 0, 255))
                    else:
                        imag.putpixel((x, y), (92, 36, 60, 255))
                elif brightness > 70 and brightness < 90:
                    if probably(punt / 100):
                        imag.putpixel((x, y), (92, 36, 60, 255))
                    else:
                        imag.putpixel((x, y), (0, 0, 0, 255))
                elif brightness >= 90 and brightness < 150:
                    imag.putpixel((x, y), (92, 36, 60, 255))
                elif brightness >= 150 and brightness < 200:
                    if probably(punt / 100):
                        imag.putpixel((x, y), (203, 43, 43, 255))
                    else:
                        imag.putpixel((x, y), (92, 36, 60, 255))
                else:
                    imag.putpixel((x, y), (203, 43, 43, 255))

    imag.save(frame_path)

def process_frames(frame_paths, compress, comp_level, pointillism, filter_choice):
    for frame_path in frame_paths:
        apply_filter_to_frame(frame_path, compress, comp_level, pointillism, filter_choice)

def split_video_into_frames(video_path, fps, resolution):
    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    os.makedirs("frames", exist_ok=True)
    frame_paths = []
    count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if int(count % (frame_rate // fps)) == 0:
            frame = cv2.resize(frame, resolution)
            frame_path = f"frames/frame_{count}.jpg"
            cv2.imwrite(frame_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame_paths.append(frame_path)
        count += 1
    
    cap.release()
    return frame_paths

def combine_frames_into_video(frame_paths, output_path, fps, resolution):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, resolution)
    
    for frame_path in sorted(frame_paths, key=lambda x: int(x.split('_')[-1].split('.')[0])):
        frame = cv2.imread(frame_path)
        out.write(frame)
    
    out.release()

def add_audio_to_video(video_path, audio_path, output_path):
    command = f"ffmpeg -i {video_path} -i {audio_path} -c copy -map 0:v:0 -map 1:a:0 -shortest {output_path}"
    subprocess.call(command, shell=True)

def main():
    parser = argparse.ArgumentParser(description='Apply filters to a video.')
    parser.add_argument('video', help='Path to the video file')
    parser.add_argument('fps', type=int, help='Frames per second for processing')
    parser.add_argument('--resolution', type=str, default='640x480', help='Resolution for the frames, e.g., 640x480')
    args = parser.parse_args()
    
    resolution = tuple(map(int, args.resolution.split('x')))

    compress = input('Do you want to compress the frames? (yes/no): ').strip().lower() == 'yes'
    comp_level = 0
    if compress:
        comp_level = int(input('Enter the level of compression (0 best quality to 100 worst quality): ').strip())

    pointillism = input('Do you want the pointillism effect on the frames? (yes/no): ').strip().lower() == 'yes'
    filter_choice = int(input('Choose filter: 1 for Milk1 effect, 2 for Milk2 effect: ').strip())

    frame_paths = split_video_into_frames(args.video, args.fps, resolution)
    num_processes = cpu_count()
    chunk_size = len(frame_paths) // num_processes
    
    pool = Pool(processes=num_processes)
    chunks = [frame_paths[i:i + chunk_size] for i in range(0, len(frame_paths), chunk_size)]
    
    for chunk in chunks:
        pool.apply_async(process_frames, (chunk, compress, comp_level, pointillism, filter_choice))
    
    pool.close()
    pool.join()
    
    cap = cv2.VideoCapture(args.video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    combine_frames_into_video(frame_paths, 'output_video.avi', args.fps, resolution)
    
    # Extract audio from original video
    original_audio_path = 'original_audio.aac'
    command = f"ffmpeg -i {args.video} -q:a 0 -map a {original_audio_path}"
    subprocess.call(command, shell=True)
    
    # Add audio to processed video
    add_audio_to_video('output_video.avi', original_audio_path, 'final_output_video.avi')
    print("Filtered video saved as 'final_output_video.avi'")

if __name__ == '__main__':
    main()