# coding: utf-8

explain = """
Script pour récupérer une vidéo Youtube, la convertir en MP3 (musique)
et la découper en plusieurs fichiers 
à partir une table de minutage + nom de fichier

table de minutage:
[
    ["00:00:00", "01. titre 1", "fichier1.mp3"],
    ["00:04:32", "02. titre 2", "fichier2.mp3"],
    ["00:09:05", "03. titre 3", "fichier3.mp3"]
]

"""

import os
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import youtube_dl

from cleanstring import clean_string



def download_youtube_url(video_url, dir="", filename=""):
    """
    Téléchargement d'une vidéo Youtube pour la convertir
    en fichier MP3
    3 paramètres : URL de la vidéo
    Dossier où déposer le fichier (par défaut : là où est le script)
    Nom du fichier (par défaut : nom de la vidéo elle-même)

    Renvoie le nom complet du fichier (avec dossier)
    """
    video_info = youtube_dl.YoutubeDL().extract_info(
        url = video_url,download=False
    )
    if filename == "":
        filename = clean_string(f"{video_info['title']}.mp4", False, False)
    options={
        'format':'bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        """'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp4',
                'preferredquality': '192',
            }],"""
        'keepvideo':True,
        'outtmpl':filename,
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])
    return os.path.join(dir, filename)



if __name__=='__main__':
    url_YT = input("URL de la vidéo Youtube (sép : ';'): ")
    """split_rules = []
    for el in table_millisecondes:
        print(el)
        split_rules.append(Split_rule(el))"""
    for url in url_YT.split(";"):
        print("Téléchargement de la video en MP4", url)
        full_video = download_youtube_url(url)

"""
Splitter 
rom pydub import AudioSegment


"""