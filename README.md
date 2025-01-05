# MILK-VIDEO-CONVERTER

This repository contains a Python script that processes a local video file, applies custom filters to make it look like the game MILK INSIDE/OUTSIDE A BAG OF MILK created by Nikita Kryukov, and saves the processed video.

The original filter was created by [LucaSinUnaS](https://github.com/LucaSinUnaS) to apply it to an image. I just adapted it to process a full video. Go check his work [here](https://github.com/LucaSinUnaS/Milk-Filter).

## What the script does:

- Extracts frames from the video.
- Applies custom filters to the frames, acording to the user's input.
- Reassembles the frames into a new video with the original audio.


## Requirements

Ensure you have Python 3 installed. Install the required dependencies using the following command:

```bash
pip install -r requirements.txt
```

## Usage (CLI VERSION)

To use the script, follow these steps
Download the repository to your PC, you can do this by cloning the repository or downloading the ZIP file.
If you want to clone the repository, use the following command:

```bash
git clone https://github.com/figurophobia/Milk-Video-Converter
```
This will create a folder named "Milk-Video-Converter" in your current directory.
Place your video file in the same directory as the script (preferably in .mp4 format).
Run the script with the path to your video file as an argument:

```python
python videoCLI.py /path/to/your/video/file
```
Follow the on-screen prompts to customize the frame extraction FPS, select the milk type, apply pointillism effect, and apply compression.

If you dont want to customize the frame extraction FPS, the script will detect the FPS of the video and use it as the default value, this is not recommended for videos with high FPS, such as 60 FPS, it will create a lot of frames and the script will take a long time to process them.

Be patient, the script will take some time to process the video, depending on the video's length and the selected filters, it may take a few minutes to complete.
The progress of the script will be displayed in the console, showing the % of the video processed.

Example (you can use the testVideo.mp4 file on the repository to test the script):
```python
python videoCLI.py testVideo.mp4
```


## License

This project is licensed under the MIT License - see the LICENSE file for details.

