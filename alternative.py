import cv2
from PIL import Image
import os
import random
from multiprocessing import Process, cpu_count, current_process, Value
import subprocess
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import time

def extract_audio(video_path, audio_path):
    print(f"Extrayendo audio de {video_path}...")
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path}"
    subprocess.call(command, shell=True)
    print(f"Audio extraído y guardado en {audio_path}.")

def convert_video(input_path, output_path):
    print(f"Convirtiendo {input_path} a {output_path}...")
    command = f"ffmpeg -i {input_path} -c:v libx264 -c:a aac {output_path}"
    subprocess.call(command, shell=True)
    print(f"Video convertido y guardado en {output_path}.")

def extract_frames(video_path, output_folder):
    print(f"Extrayendo frames de {video_path}...")
    vidcap = cv2.VideoCapture(video_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    success, image = vidcap.read()
    count = 0

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta '{output_folder}' creada.")

    while success:
        frame_path = f"{output_folder}/frame{count}.jpg"
        cv2.imwrite(frame_path, image)  # Guarda el frame como archivo JPEG
        print(f"Frame {count} guardado en {frame_path}.")
        success, image = vidcap.read()
        count += 1

    vidcap.release()
    print("Extracción de frames completada.")
    return fps, count

def probably(prob):
    return random.random() < prob

def apply_filter(image, compression, effect, milk_type, quality, pointillism):
    if effect:
        punt = 70
    else:
        punt = 100

    imag = image.convert('RGB')

    if compression:
        imag.save("temp.jpg", quality=100-quality)
        imag = Image.open("temp.jpg")

    width, height = imag.size

    for x in range(width):
        for y in range(height):
            pixelRGB = imag.getpixel((x, y))
            R, G, B = pixelRGB
            brightness = sum([R, G, B]) / 3
            new_pixel = (0, 0, 0, 255)  # Por defecto negro
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

    if pointillism:
        imag = apply_pointillism_effect(imag)

    return imag

def apply_pointillism_effect(image):
    output_image = Image.new('RGB', image.size)
    width, height = image.size

    for _ in range(10000):  # Ajustar el número de puntos según sea necesario
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = image.getpixel((x, y))
        size = random.randint(1, 3)  # Ajustar el tamaño de los puntos según sea necesario
        for dx in range(size):
            for dy in range(size):
                if 0 <= x + dx < width and 0 <= y + dy < height:
                    output_image.putpixel((x + dx, y + dy), color)

    return output_image

def apply_filter_to_frame_range(start, end, input_folder, output_folder, compression, effect, milk_type, quality, pointillism, progress):
    process_name = current_process().name
    for frame_num in range(start, end):
        frame_path = os.path.join(input_folder, f"frame{frame_num}.jpg")
        if os.path.exists(frame_path):
            print(f"{process_name} procesando {frame_path}...")
            image = Image.open(frame_path)
            filtered_image = apply_filter(image, compression, effect, milk_type, quality, pointillism)
            filtered_frame_path = os.path.join(output_folder, f"frame{frame_num}.jpg")
            filtered_image.save(filtered_frame_path)
            print(f"{process_name} guardó el frame filtrado en {filtered_frame_path}.")
            
            # Actualizar progreso
            with progress.get_lock():
                progress.value += 1
        else:
            print(f"{process_name}: {frame_path} no existe. Saltando.")

def apply_filter_to_frames(input_folder, output_folder, compression=False, effect=False, milk_type=1, quality=90, pointillism=False, progress_bar=None):
    print(f"Aplicando filtro a los frames en '{input_folder}' y guardando en '{output_folder}'...")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Carpeta '{output_folder}' creada.")

    frame_files = [f for f in os.listdir(input_folder) if f.endswith('.jpg')]
    frame_files.sort(key=lambda x: int(x[5:-4]))
    total_frames = len(frame_files)

    num_processes = min(cpu_count(), total_frames)  # No crear más procesos que frames
    frames_per_process = total_frames // num_processes

    progress = Value('i', 0)  # Valor compartido para progreso

    processes = []
    for i in range(num_processes):
        start = i * frames_per_process
        end = (i + 1) * frames_per_process if i != num_processes - 1 else total_frames
        process = Process(target=apply_filter_to_frame_range, args=(start, end, input_folder, output_folder, compression, effect, milk_type, quality, pointillism, progress))
        processes.append(process)
        process.start()

    while any(p.is_alive() for p in processes):
        if progress_bar:
            progress_bar['value'] = (progress.value / total_frames) * 100
            progress_bar.update()
        time.sleep(0.1)
    
    for process in processes:
        process.join()

    if progress_bar:
        progress_bar['value'] = 100  # Asegurarse de que la barra de progreso esté completa
        progress_bar.update()

    print("Aplicación de filtro a todos los frames completada.")

def frames_to_video(input_folder, output_path, fps):
    print(f"Convirtiendo frames en '{input_folder}' a video '{output_path}' a {fps} fps...")
    frame_files = [f for f in os.listdir(input_folder) if f.endswith('.jpg')]
    
    if not frame_files:
        print("No se encontraron frames en la carpeta de entrada.")
        return
    
    frame_files.sort(key=lambda x: int(x[5:-4]))  # Ordenar los frames por número

    frame = cv2.imread(os.path.join(input_folder, frame_files[0]))
    height, width, _ = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_file in frame_files:
        frame_path = os.path.join(input_folder, frame_file)
        frame = cv2.imread(frame_path)
        out.write(frame)

    out.release()
    print(f"Video guardado en '{output_path}'.")

def download_video(link, output_path):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except Exception as e:
        print(e)

def process_video(link, compression, pointillism, milk_type, quality, progress_bar):
    video_path = 'video.mp4'
    if link.startswith("http"):
        download_video(link, video_path)
    else:
        video_path = link

    converted_video_path = 'converted_video.mp4'
    convert_video(video_path, converted_video_path)

    audio_path = 'audio.mp3'
    extract_audio(converted_video_path, audio_path)

    fps, total_frames = extract_frames(converted_video_path, 'og')

    apply_filter_to_frames('og', 'filtered_frames', compression=compression, milk_type=milk_type, quality=quality, pointillism=pointillism, progress_bar=progress_bar)

    for file in os.listdir('og'):
        os.remove(f'og/{file}')

    frames_to_video('filtered_frames', 'filtered_video.mp4', fps)

    final_video_path = 'final_video_with_audio.mp4'
    command = f"ffmpeg -i filtered_video.mp4 -i {audio_path} -c copy -map 0:v:0 -map 1:a:0 {final_video_path}"
    subprocess.call(command, shell=True)

    for file in os.listdir('filtered_frames'):
        os.remove(f'filtered_frames/{file}')

    os.rmdir('filtered_frames')
    os.rmdir('og')
    os.remove(audio_path)
    os.remove(video_path)
    os.remove(converted_video_path)
    os.remove('filtered_video.mp4')

    messagebox.showinfo("Proceso completado", "El video ha sido procesado y guardado como 'final_video_with_audio.mp4'")

def main():
    root = tk.Tk()
    root.title("Procesador de Video de YouTube")

    tk.Label(root, text="Enlace de YouTube:").grid(row=0, column=0, padx=10, pady=10)
    link_entry = tk.Entry(root, width=50)
    link_entry.grid(row=0, column=1, padx=10, pady=10)

    compression_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Usar Compresión", variable=compression_var).grid(row=1, column=0, padx=10, pady=10)

    pointillism_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Aplicar Puntillismo", variable=pointillism_var).grid(row=1, column=1, padx=10, pady=10)

    tk.Label(root, text="Tipo de Milk Filter:").grid(row=2, column=0, padx=10, pady=10)
    milk_type_var = tk.IntVar(value=1)
    tk.Radiobutton(root, text="1", variable=milk_type_var, value=1).grid(row=2, column=1, padx=10, pady=10)
    tk.Radiobutton(root, text="2", variable=milk_type_var, value=2).grid(row=2, column=2, padx=10, pady=10)

    tk.Label(root, text="Calidad de Compresión (0-100):").grid(row=3, column=0, padx=10, pady=10)
    quality_scale = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL)
    quality_scale.set(90)
    quality_scale.grid(row=3, column=1, padx=10, pady=10)

    def select_video_file():
        video_file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        if video_file_path:
            link_entry.delete(0, tk.END)
            link_entry.insert(0, video_file_path)

    tk.Button(root, text="Seleccionar Video", command=select_video_file).grid(row=0, column=2, padx=10, pady=10)

    progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
    progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

    def start_processing():
        link = link_entry.get()
        compression = compression_var.get()
        pointillism = pointillism_var.get()
        milk_type = milk_type_var.get()
        quality = quality_scale.get()

        if not link:
            messagebox.showerror("Error", "Por favor, ingrese un enlace de YouTube válido o seleccione un archivo de video.")
            return

        process_video(link, compression, pointillism, milk_type, quality, progress_bar)

    tk.Button(root, text="Procesar Video", command=start_processing).grid(row=6, column=0, columnspan=3, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()