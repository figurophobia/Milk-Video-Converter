import os
import random
import sys
from PIL import Image
import argparse

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def probably(chance):
    return random.random() < chance

def apply_filter(filename, compress, comp_level, pointillism, filter_choice):
    if pointillism:
        punt = 70
    else:
        punt = 100

    imag = Image.open(filename)
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

    output_filename = f"filtered_{os.path.basename(filename)}"
    imag.save(output_filename)
    print(f"Filtered image saved as '{output_filename}'")

def main():
    parser = argparse.ArgumentParser(description='Apply filters to an image.')
    parser.add_argument('image', help='Path to the image file')
    args = parser.parse_args()

    compress = input('Do you want to compress the image? (yes/no): ').strip().lower() == 'yes'
    comp_level = 0
    if compress:
        comp_level = int(input('Enter the level of compression (0 best quality to 100 worst quality): ').strip())

    pointillism = input('Do you want the pointillism effect on the image? (yes/no): ').strip().lower() == 'yes'
    filter_choice = int(input('Choose filter: 1 for Milk1 effect, 2 for Milk2 effect: ').strip())

    apply_filter(args.image, compress, comp_level, pointillism, filter_choice)

if __name__ == '__main__':
    main()