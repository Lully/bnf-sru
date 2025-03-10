# coding: utf-8

from PIL import Image
import os

main_dir = r"D:\Documents\perso\Etienne\DUEC"
target_dir = os.path.join(main_dir, "compressed")

for fname in os.listdir(main_dir):
    filename = os.path.join(main_dir, fname)
    if ".jpg" in filename and fname not in os.listdir(target_dir):
        print(filename)
        image = Image.open(filename)
        width, height = image.size
        new_size = (width//2, height//2)
        resized_image = image.resize(new_size)
        resized_image.save(os.path.join(target_dir, fname), optimize=True, quality=50)