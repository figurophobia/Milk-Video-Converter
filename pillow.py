import os
import random
import subprocess
import cv2
from PIL import Image
from multiprocessing import Process, cpu_count, current_process
import argparse

def extract_audio(video_path, audio_path):
    """Extracts audio from a video file and saves it as an MP3 file."""
    print(f"Extracting audio from {video_path}...")
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path}"
    subprocess.call(command, shell=True)
    print(f"Audio extracted and saved to {audio_path}.")

def convert_video(input_path, output_path):
    """Converts a video file to a compatible format."""
    print(f"Converting {input_path} to {output_path}...")
    command = f"ffmpeg -i {input_path} -c:v libx264 -crf 23 -preset medium -c:a aac {output_path}"
    subprocess.call(command, shell=True)
    print(f"Video converted and saved to {output_path}.")

def extract_frames(video_path, output_folder):
    """Extracts frames from a video file and saves them in a folder."""
    print(f"Extracting frames from {video_path}...")
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    success, image = vidcap.read()
    count = 0

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Folder '{output_folder}' created.")

    while success:
        frame_path = f"{output_folder}/frame{count}.jpg"
        cv2.imwrite(frame_path, image)
        print(f"Frame {count} saved to {frame_path}.")
        success, image = vidcap.read()
        count += 1

    vidcap.release()
    print("Frame extraction completed.")
    return fps, count

def probably(prob):
    """Returns True with a probability equal to `prob`."""
    return random.random() < prob

def apply_filter(image, compression, effect, milk_type, calidad, frame_path):
    """Applies a custom filter to an image."""
    if effect:
        punt = 70
    else:
        punt = 100

    imag = image.convert('RGB')
    #Sacar el nombre del archivo dada su ruta absoluta, quita la extension
    nombre = os.path.splitext(os.path.basename(frame_path))[0]

    if compression:
        # Guarda la imagen con el mismo nombre en la carpeta 'filtered_frames'
        output_folder = 'filtered_frames'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_path = os.path.join(output_folder, f"{nombre}.jpg")
        imag.save(output_path, quality=100-calidad)
        imag = Image.open(output_path)

    width, height = imag.size

    for x in range(width):
        for y in range(height):
            pixelRGB = imag.getpixel((x, y))
            R, G, B = pixelRGB
            brightness = sum([R, G, B]) / 3
            new_pixel = (0, 0, 0, 255)  # Default black
            if milk_type == 1:
                if brightness <= 25:
                    new_pixel = (0, 0, 0, 255)
                elif brightness <= 70:
                    new_pixel = (0, 0, 0, 255) if probably(punt/100) else (102, 0, 31, 255)
                elif brightness < 120:
                    new_pixel = (102, 0, 31, 255) if probably(punt/100) else (0, 0, 0, 255)
                elif brightness < 200:
                    new_pixel = (102, 0, 31, 255)
                elif brightness < 230:
                    new_pixel = (137, 0, 146, 255) if probably(punt/100) else (102, 0, 31, 255)
                else:
                    new_pixel = (137, 0, 146, 255)
            else:
                if brightness <= 25:
                    new_pixel = (0, 0, 0, 255)
                elif brightness <= 70:
                    new_pixel = (0, 0, 0, 255) if probably(punt/100) else (92, 36, 60, 255)
                elif brightness < 90:
                    new_pixel = (92, 36, 60, 255) if probably(punt/100) else (0, 0, 0, 255)
                elif brightness < 150:
                    new_pixel = (92, 36, 60, 255)
                elif brightness < 200:
                    new_pixel = (203, 43, 43, 255) if probably(punt/100) else (92, 36, 60, 255)
                else:
                    new_pixel = (203, 43, 43, 255)

            imag.putpixel((x, y), new_pixel)

    return imag

def apply_filter_to_frame_range(start, end, input_folder, output_folder, compression, effect, milk_type, quality):
    """Applies the filter to a range of frames and saves them to the output folder."""
    process_name = current_process().name
    for frame_num in range(start, end):
        frame_path = os.path.join(input_folder, f"frame{frame_num}.jpg")
        if os.path.exists(frame_path):
            print(f"{process_name} processing {frame_path}...")
            image = Image.open(frame_path)
            filtered_image = apply_filter(image, compression, effect, milk_type, quality, frame_path)
            filtered_frame_path = os.path.join(output_folder, f"frame{frame_num}.jpg")
            filtered_image.save(filtered_frame_path)
            print(f"{process_name} saved filtered frame to {filtered_frame_path}.")
        else:
            print(f"{process_name}: {frame_path} not found. Skipping.")

def apply_filter_to_frames(input_folder, output_folder, compression=False, effect=False, milk_type=1, quality=90):
    """Applies the custom filter to each extracted frame and saves them to the output folder."""
    print(f"Applying filter to frames in '{input_folder}' and saving to '{output_folder}'...")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Folder '{output_folder}' created.")

    frame_files = [f for f in os.listdir(input_folder) if f.endswith('.jpg')]
    frame_files.sort(key=lambda x: int(x[5:-4]))
    total_frames = len(frame_files)

    num_processes = min(cpu_count(), total_frames)
    frames_per_process = total_frames // num_processes

    processes = []
    for i in range(num_processes):
        start = i * frames_per_process
        end = (i + 1) * frames_per_process if i != num_processes - 1 else total_frames
        process = Process(target=apply_filter_to_frame_range, args=(start, end, input_folder, output_folder, compression, effect, milk_type, quality))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("Finished applying filter to all frames.")

def frames_to_video(input_folder, output_path, fps):
    """Converts a sequence of frames into a video file."""
    print(f"Converting frames in '{input_folder}' to video '{output_path}' at {fps} fps...")
    frame_files = [f for f in os.listdir(input_folder) if f.endswith('.jpg')]
    
    if not frame_files:
        print("No frames found in the input folder.")
        return
    
    frame_files.sort(key=lambda x: int(x[5:-4]))

    frame = cv2.imread(os.path.join(input_folder, frame_files[0]))
    height, width, _ = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_file in frame_files:
        frame_path = os.path.join(input_folder, frame_file)
        frame = cv2.imread(frame_path)
        out.write(frame)

    out.release()
    print(f"Video saved to '{output_path}'.")

def main():
    parser = argparse.ArgumentParser(description='Process a local video file and apply filters.')
    parser.add_argument('video_path', type=str, help='Path to the local video file')
    args = parser.parse_args()

    video_path = args.video_path

    converted_video_path = 'converted_video.mp4'
    convert_video(video_path, converted_video_path)

    audio_path = 'audio.mp3'
    extract_audio(converted_video_path, audio_path)

    fps, total_frames = extract_frames(converted_video_path, 'og')

    milk_type = int(input("Select milk type (1 or 2): "))
    pointillism = input("Apply pointillism effect? (y/n): ").lower() == 'y'
    compression = input("Apply compression? (y/n): ").lower() == 'y'

    quality = 90
    if compression:
        quality = int(input("Enter compression quality (0-100, where 0 is best quality): "))

    apply_filter_to_frames('og', 'filtered_frames', compression=compression, effect=pointillism, milk_type=milk_type, quality=quality)

    for file in os.listdir('og'):
        os.remove(f'og/{file}')

    frames_to_video('filtered_frames', 'filtered_video.mp4', fps)

    final_video_path = 'final_video_with_audio.mp4'
    command = f"ffmpeg -i filtered_video.mp4 -i {audio_path} -c:v libx264 -crf 23 -preset medium -c:a aac -strict -2 {final_video_path}"
    subprocess.call(command, shell=True)

    for file in os.listdir('filtered_frames'):
        os.remove(f'filtered_frames/{file}')

    os.rmdir('filtered_frames')
    os.rmdir('og')
    os.remove(audio_path)
    os.remove(converted_video_path)
    os.remove('filtered_video.mp4')

if __name__ == "__main__":
    main()