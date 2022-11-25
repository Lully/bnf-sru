# coding: utf-8

explain = """Conversion de fichiers flac en fichiers mp3"""

from pydub import AudioSegment
from pydub.utils import mediainfo
import os
from stdf import input2default

def flacfile2mp3(filename, dir="", del_option=True):
    print("Conversion de", filename)
    filename_list = filename.split(".")
    if len(filename_list) == 2:
        root_filename, extension = filename_list
    elif len(filename_list) > 2:
        root_filename = ".".join(filename_list[0:-1])
        extension = filename_list[-1]
    file_metas = mediainfo(os.path.join(dir, filename))
    input_audio = AudioSegment.from_file(os.path.join(dir, filename), format=extension)
    input_audio.export(os.path.join(dir, f"{root_filename}.mp3"), format="mp3", tags=file_metas["TAG"])
    if del_option:
        try:
            os.remove(os.path.join(dir, filename))
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    print(explain)
    input_dir = input("Nom du fichier FLAC ou du dossier à convertir : ")
    if os.path.isdir(input_dir):
        extension = input2default(input("Extension des fichiers à convertir [flac] : "), "flac")
        del_option = input2default(input("Supprimer les fichiers après conversion [oui] : "), "oui")
        if del_option[0].lower() == "o":
            del_option = True
        else:
            del_option = False
        list_files = os.listdir(input_dir)
        for filename in list_files:
            if extension in filename:
                flacfile2mp3(filename, input_dir, del_option)
    elif os.path.isfile(input_dir):
        flacfile2mp3(input_dir, del_option=False)