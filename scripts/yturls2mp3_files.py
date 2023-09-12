# coding: utf-8

explain = """
Script pour récupérer des vidéos Youtube en autant de fichiers  MP3 (musique)
à partir d'une liste d'URL séparées par des virgules
"""

import os
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import youtube_dl




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
        filename = f"{video_info['title']}.mp3"
    options={
        'format':'bestaudio/best',
        'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        'keepvideo':False,
        'outtmpl':filename,
    }

    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])
    return os.path.join(dir, filename)


def split_mp3file(filename, split_rules):
    # filename = nom (avec chemin) du fichier à découper
    # split_rules = liste d'instances de classe Split_rule
    try:
        complete_sound = AudioSegment.from_mp3(filename)
    except CouldntDecodeError:
        complete_sound = AudioSegment.from_file(filename, format="mp4")
    dir = os.path.dirname(filename)
    for rule in split_rules:
        print(rule)
        track = complete_sound[rule.start:rule.end]
        track.export(os.path.join(dir, rule.output_filename), format="mp3")


def get_millisec(time_str):
    """Convertir un horodatage hh:mm:ss en millisecondes"""
    h, m, s = time_str.split(':')
    millisec = 1000 * (int(h) * 3600 + int(m) * 60 + int(s))
    return millisec


def format_millisecondes(liste_horaires):
    # La liste des horaires est exprimée en hh:mm:ss
    # Il faut convertir chaque élément en une paire de millisecondes
    liste_millisecondes = []
    i = 0
    for el in liste_horaires:
        el1 = get_millisec(el)
        try:
            el2 = get_millisec(liste_horaires[i+1])
        except IndexError:
            el2 = ""
        liste_millisecondes.append((el1, el2))
        i += 1
    return liste_millisecondes


def rewrite_horodatage_table(table_horaires):
    # Pour une liste dont chaque item a comme premier élément un horodatage,
    # renvoie la même liste mais dont ce premier élément est remplacé par 
    # le début et la fin en millisecondes
    millisecondes = format_millisecondes([el[0] for el in table_horaires]) # listes d'horodatage (paires (début,fin))
    i = 0
    for el in table_horaires:
        el[0] = millisecondes[i]
        i += 1
    return table_horaires

if __name__=='__main__':
    url_YT = input("liste des URL de la vidéo Youtube [sep : virgule]: ").split(",")
    dirname = input("Dossier où déposer les fichiers : ")
    for u in url_YT:
        if "http" in u:
            print("Téléchargement de la video en MP3", u)
            full_video = download_youtube_url(u, dirname)

"""
Splitter 
rom pydub import AudioSegment


"""