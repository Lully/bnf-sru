# coding: utf-8

"""
Conversion des fichiers flac d'un répertoire en fichiers mp3
"""

import os
from pydub import AudioSegment


def convert_files(dirpath, extension):
    for file in os.listdir(dirpath):
        if file.endswith(extension):
            filename = os.path.join(dirpath, file)
            new_filename = filename.replace(extension, ".mp3")
            audio = AudioSegment.from_file(filename, format=extension)
            audio.export(new_filename, format="mp3")


if __name__ == "__main__":
    dir = input("Dossier où sont les fichiers flac à convertir : ")
    extension = input("Extension (par défaut : flac) : ")
    if extension == "":
        extension = "flac"
    convert_files(dir, extension)