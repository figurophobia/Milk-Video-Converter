import os

import sys
import cv2
import random
from PIL import Image
import subprocess
from multiprocessing import Process, cpu_count
import shutil
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QCheckBox, QSpinBox, QComboBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

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
                progress_callback.emit(int(progress))
        time.sleep(1)

    for process in processes:
        process.join()

    if progress_callback:
        progress_callback.emit(100)

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

class FilterThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, video_path, fps, milk_type, pointillism, compression, quality):
        super().__init__()
        self.video_path = video_path
        self.fps = fps
        self.milk_type = milk_type
        self.pointillism = pointillism
        self.compression = compression
        self.quality = quality

    def run(self):
        extract_frames_with_ffmpeg(self.video_path, 'og', self.fps)
        apply_filter_to_frames('og', 'filtered_frames', compression=self.compression, effect=self.pointillism, milk_type=self.milk_type, quality=self.quality, progress_callback=self.progress)
        
        for file in os.listdir('og'):
            os.remove(f'og/{file}')

        video_name, video_ext = os.path.splitext(self.video_path)
        filtered_video_path = f"{video_name}_filtered{video_ext}"

        frames_to_video('filtered_frames', filtered_video_path, self.fps, self.video_path)

        for file in os.listdir('filtered_frames'):
            os.remove(f'filtered_frames/{file}')

        os.rmdir('filtered_frames')
        os.rmdir('og')

        self.finished.emit()

class VideoFilterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Milk Inside a Bag of Milk Video Filter")
        self.setGeometry(100, 100, 400, 300)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#040404"))  # Fondo de la ventana
        palette.setColor(QPalette.WindowText, QColor("#7c138b"))  # Texto de la ventana
        palette.setColor(QPalette.Base, QColor("#7c138b"))  # Fondo de los campos de entrada
        palette.setColor(QPalette.AlternateBase, QColor("#5d0423"))  # Fondo alternativo
        palette.setColor(QPalette.ToolTipBase, QColor("#5d0423"))  # Fondo de la herramienta
        palette.setColor(QPalette.ToolTipText, QColor("#040404"))  # Texto de la herramienta
        palette.setColor(QPalette.Text, QColor("#040404"))  # Texto en los campos de entrada
        palette.setColor(QPalette.Button, QColor("#7c138b"))  # Fondo de los botones
        palette.setColor(QPalette.ButtonText, QColor("#040404"))  # Texto de los botones
        palette.setColor(QPalette.Highlight, QColor("#5d0423"))  # Color de resaltado
        palette.setColor(QPalette.HighlightedText, QColor("#040404"))  # Texto resaltado
        self.setPalette(palette)

        font = QFont("Arial", 14, QFont.Bold)

        layout = QVBoxLayout()

        self.title = QLabel("Milk Inside a Bag of Milk Video Filter", self)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        self.select_video_btn = QPushButton("Select Video", self)
        self.select_video_btn.setFixedSize(150, 30)
        self.select_video_btn.clicked.connect(self.select_video)
        layout.addWidget(self.select_video_btn, alignment=Qt.AlignCenter)

        self.fps_checkbox = QCheckBox("Customize FPS", self)
        self.fps_checkbox.stateChanged.connect(self.toggle_fps_spinbox)
        layout.addWidget(self.fps_checkbox)

        self.fps_spinbox = QSpinBox(self)
        self.fps_spinbox.setFixedSize(80, 30)
        self.fps_spinbox.setRange(1, 60)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setEnabled(False)
        layout.addWidget(self.fps_spinbox)

        self.milk_type_label = QLabel("Select Milk Type:", self)
        self.milk_type_label.setFont(font)
        layout.addWidget(self.milk_type_label)

        self.milk_type_combo = QComboBox(self)
        self.milk_type_combo.setFixedSize(150, 30)
        self.milk_type_combo.addItem("Milk Type 1")
        self.milk_type_combo.addItem("Milk Type 2")
        layout.addWidget(self.milk_type_combo)

        self.pointillism_checkbox = QCheckBox("Apply Pointillism Effect", self)
        layout.addWidget(self.pointillism_checkbox)

        self.compression_checkbox = QCheckBox("Apply Compression", self)
        self.compression_checkbox.stateChanged.connect(self.toggle_quality_spinbox)
        layout.addWidget(self.compression_checkbox)

        self.quality_spinbox = QSpinBox(self)
        self.quality_spinbox.setFixedSize(80, 30)
        self.quality_spinbox.setRange(0, 100)
        self.quality_spinbox.setValue(90)
        self.quality_spinbox.setEnabled(False)
        layout.addWidget(self.quality_spinbox)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Progress: 0.00%", self)
        self.progress_label.setFont(font)
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        self.start_btn = QPushButton("Start Processing", self)
        self.start_btn.setFixedSize(150, 30)
        self.start_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.center()

    def toggle_fps_spinbox(self, state):
        self.fps_spinbox.setEnabled(state == Qt.Checked)

    def toggle_quality_spinbox(self, state):
        self.quality_spinbox.setEnabled(state == Qt.Checked)

    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.desktop().screen().rect().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def select_video(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.video_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)", options=options)
        if self.video_path:
            self.select_video_btn.setText(f"Selected: {os.path.basename(self.video_path)}")

    def update_progress(self, progress):
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"Progress: {progress:.2f}%")

    def processing_finished(self):
        self.progress_label.setText("Progress: 100.00% - FINISH!")
        self.start_btn.setEnabled(True)

    def start_processing(self):
        if not self.video_path:
            return

        fps = get_video_fps(self.video_path)
        if self.fps_checkbox.isChecked():
            fps = self.fps_spinbox.value()

        milk_type = 1 if self.milk_type_combo.currentIndex() == 0 else 2
        pointillism = self.pointillism_checkbox.isChecked()
        compression = self.compression_checkbox.isChecked()
        quality = self.quality_spinbox.value()

        self.start_btn.setEnabled(False)

        self.filter_thread = FilterThread(self.video_path, fps, milk_type, pointillism, compression, quality)
        self.filter_thread.progress.connect(self.update_progress)
        self.filter_thread.finished.connect(self.processing_finished)
        self.filter_thread.start()

def main():
    app = QApplication(sys.argv)
    ex = VideoFilterApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()