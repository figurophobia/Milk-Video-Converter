import os
import sys
import cv2
import random
from PIL import Image, ImageTk
import subprocess
from multiprocessing import Process, cpu_count
import shutil
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def get_video_fps(video_path):
    """Gets the FPS of a video file."""
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    vidcap.release()
    return fps

def extract_frames_with_ffmpeg(video_path, output_folder, fps):
    """Extracts frames from a video file using ffmpeg."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        # Ensure the folder is empty
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    command = f"ffmpeg -y -i {video_path} -vf fps={fps} {output_folder}/frame%06d.jpg"
    subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    nombre = os.path.splitext(os.path.basename(frame_path))[0]

    if compression:
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
            new_pixel = (0, 0, 0, 255)

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
    for frame_num in range(start, end):
        frame_path = os.path.join(input_folder, f"frame{frame_num:06d}.jpg")
        if os.path.exists(frame_path):
            image = Image.open(frame_path)
            filtered_image = apply_filter(image, compression, effect, milk_type, quality, frame_path)
            filtered_frame_path = os.path.join(output_folder, f"frame{frame_num:06d}.jpg")
            filtered_image.save(filtered_frame_path)

def apply_filter_to_frames(input_folder, output_folder, compression=False, effect=False, milk_type=1, quality=90, progress_callback=None):
    """Applies the custom filter to each extracted frame and saves them to the output folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        # Ensure the folder is empty
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

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

    while any(process.is_alive() for process in processes):
        og_files = len(os.listdir(input_folder))
        filtered_files = len(os.listdir(output_folder))
        if og_files > 0:
            progress = (filtered_files / og_files) * 100
            if progress_callback:
                progress_callback(int(progress))
        time.sleep(1)

    for process in processes:
        process.join()

    if progress_callback:
        progress_callback(100)

def frames_to_video(input_folder, output_path, fps, original_video_path):
    """Converts a sequence of frames into a video file using ffmpeg and retains the original audio."""
    frame_files = [f for f in os.listdir(input_folder) if f.endswith('.jpg')]
    
    if not frame_files:
        return
    
    frame_files.sort(key=lambda x: int(x[5:-4]))
    
    with open('frames.txt', 'w') as f:
        for frame_file in frame_files:
            frame_path = os.path.join(input_folder, frame_file)
            f.write(f"file '{frame_path}'\n")

    command = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-r', str(fps),
        '-i', 'frames.txt',
        '-i', original_video_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-strict', 'experimental',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove('frames.txt')

class FilterThread:
    def __init__(self, video_path, fps, milk_type, pointillism, compression, quality, progress_callback, finish_callback):
        self.video_path = video_path
        self.fps = fps
        self.milk_type = milk_type
        self.pointillism = pointillism
        self.compression = compression
        self.quality = quality
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback

    def run(self):
        extract_frames_with_ffmpeg(self.video_path, 'og', self.fps)
        apply_filter_to_frames('og', 'filtered_frames', compression=self.compression, effect=self.pointillism, milk_type=self.milk_type, quality=self.quality, progress_callback=self.progress_callback)
        
        for file in os.listdir('og'):
            os.remove(f'og/{file}')

        video_name, video_ext = os.path.splitext(self.video_path)
        filtered_video_path = f"{video_name}_filtered{video_ext}"

        frames_to_video('filtered_frames', filtered_video_path, self.fps, self.video_path)

        for file in os.listdir('filtered_frames'):
            os.remove(f'filtered_frames/{file}')

        os.rmdir('filtered_frames')
        os.rmdir('og')

        self.finish_callback()

class VideoFilterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.initUI()

    def initUI(self):
        self.title("Milk Inside a Bag of Milk Video Filter")
        self.geometry("400x600")
        self.configure(bg="#1e1e2e")  # Dark blue background color

        font = ("Arial", 14, "bold")
        button_font = ("Arial", 12, "bold")

        self.title_label = tk.Label(self, text="Milk Inside a Bag of Milk Video Filter", font=font, fg="#f1fa8c", bg="#1e1e2e")
        self.title_label.pack(pady=10)

        self.select_video_btn = tk.Button(self, text="Select Video", command=self.select_video, font=button_font, bg="#50fa7b", fg="#282a36")
        self.select_video_btn.pack(pady=5)

        self.fps_checkbox_var = tk.IntVar()
        self.fps_checkbox = tk.Checkbutton(self, text="Customize FPS", variable=self.fps_checkbox_var, command=self.toggle_fps_spinbox, bg="#1e1e2e", fg="#f1fa8c", selectcolor="#1e1e2e")
        self.fps_checkbox.pack(pady=5)

        self.fps_spinbox = tk.Spinbox(self, from_=1, to=60, state="disabled", font=button_font, bg="#44475a", fg="#f8f8f2")
        self.fps_spinbox.pack(pady=5)

        self.milk_type_label = tk.Label(self, text="Select Milk Type:", font=font, fg="#f1fa8c", bg="#1e1e2e")
        self.milk_type_label.pack(pady=5)

        self.milk_type_combo = ttk.Combobox(self, values=["Milk Type 1", "Milk Type 2"], font=button_font)
        self.milk_type_combo.current(0)
        self.milk_type_combo.pack(pady=5)

        self.pointillism_checkbox_var = tk.IntVar()
        self.pointillism_checkbox = tk.Checkbutton(self, text="Apply Pointillism Effect", variable=self.pointillism_checkbox_var, bg="#1e1e2e", fg="#f1fa8c", selectcolor="#1e1e2e")
        self.pointillism_checkbox.pack(pady=5)

        self.compression_checkbox_var = tk.IntVar()
        self.compression_checkbox = tk.Checkbutton(self, text="Apply Compression", variable=self.compression_checkbox_var, command=self.toggle_quality_spinbox, bg="#1e1e2e", fg="#f1fa8c", selectcolor="#1e1e2e")
        self.compression_checkbox.pack(pady=5)

        self.quality_spinbox = tk.Spinbox(self, from_=0, to=100, state="disabled", font=button_font, bg="#44475a", fg="#f8f8f2")
        self.quality_spinbox.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.progress_label = tk.Label(self, text="Progress: 0.00%", font=font, fg="#f1fa8c", bg="#1e1e2e")
        self.progress_label.pack(pady=5)

        self.start_btn = tk.Button(self, text="Start Processing", command=self.start_processing, font=button_font, bg="#50fa7b", fg="#282a36")
        self.start_btn.pack(pady=10)

    def toggle_fps_spinbox(self):
        if self.fps_checkbox_var.get():
            self.fps_spinbox.config(state="normal")
        else:
            self.fps_spinbox.config(state="disabled")

    def toggle_quality_spinbox(self):
        if self.compression_checkbox_var.get():
            self.quality_spinbox.config(state="normal")
        else:
            self.quality_spinbox.config(state="disabled")

    def select_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if self.video_path:
            self.select_video_btn.config(text=f"Selected: {os.path.basename(self.video_path)}")

    def update_progress(self, progress):
        self.progress_bar["value"] = progress
        self.progress_label.config(text=f"Progress: {progress:.2f}%")
        self.update_idletasks()

    def processing_finished(self):
        self.progress_label.config(text="Progress: 100.00% - FINISH!")
        self.start_btn.config(state="normal")
        messagebox.showinfo("Processing Finished", "The video has been processed successfully!")

    def start_processing(self):
        if not self.video_path:
            messagebox.showwarning("No Video Selected", "Please select a video file to process.")
            return

        fps = get_video_fps(self.video_path)
        if self.fps_checkbox_var.get():
            fps = int(self.fps_spinbox.get())

        milk_type = 1 if self.milk_type_combo.current() == 0 else 2
        pointillism = bool(self.pointillism_checkbox_var.get())
        compression = bool(self.compression_checkbox_var.get())
        quality = int(self.quality_spinbox.get())

        self.start_btn.config(state="disabled")

        self.filter_thread = FilterThread(
            self.video_path, fps, milk_type, pointillism, compression, quality,
            progress_callback=self.update_progress, finish_callback=self.processing_finished
        )
        self.after(100, self.filter_thread.run)

def main():
    app = VideoFilterApp()
    app.mainloop()

if __name__ == "__main__":
    main()