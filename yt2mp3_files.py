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


class Split_rule:
    def __init__(self, track):
        # min est un tuple en millisecondes (début et fin)
        self.start = track[0][0]
        self.end = track[0][1]
        self.title = track[1]
        self.output_filename = track[2] + ".mp3"
    def __str__(self):
        string = "debut: " + str(self.start) + " // " + "fin: " + str(self.end) + " // titre : " + self.title
        return string



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
    url_YT = input("URL de la vidéo Youtube : ")
    table_minutes = [["00:00:00", "01 Grand Corps Malade et Camille Lellouche - Mais Je T aime", "01 Grand Corps Malade et Camille Lellouche - Mais Je T aime"],
                    ["00:03:56", "02 Camille Lellouche - N insiste pas", "02 Camille Lellouche - N insiste pas"],
                    ["00:06:57", "03 Grand Corps Malade et Louane - Derrière", "03 Grand Corps Malade et Louane - Derrière"],
                    ["00:10:41", "04 Soprano - Dingue", "04 Soprano - Dingue"],
                    ["00:15:23", "05 Louane - Donne-moi ton coeur", "05 Louane - Donne-moi ton coeur"],
                    ["00:18:35", "06 Kendji Girac - Evidemment", "06 Kendji Girac - Evidemment"],
                    ["00:22:40", "07 Kendji Girac - Dernier tro (en duo avec Gims)", "07 Kendji Girac - Dernier tro (en duo avec Gims)"],
                    ["00:25:39", "08 Louane - Aimer à mort", "08 Louane - Aimer à mort"],
                    ["00:27:56", "09 Amir - Longtemps", "09 Amir - Longtemps"],
                    ["00:31:45", "10 Vianney - Beau-Papa", "10 Vianney - Beau-Papa"],
                    ["00:35:01", "11 Vitaa et Slimane - De l or", "11 Vitaa et Slimane - De l or"],
                    ["00:39:02", "12 Amir ft Indila - Carrousel", "12 Amir ft Indila - Carrousel"],
                    ["00:43:09", "13 Amel Bent, Vitaa et Camélia Jordana - Ma Soeur", "13 Amel Bent, Vitaa et Camélia Jordana - Ma Soeur"],
                    ["00:45:45", "14 GIMS - jusqu ici tout bien", "14 GIMS - jusqu ici tout bien"],
                    ["00:50:00", "15 M Pokora - Si on disait", "15 M Pokora - Si on disait"],
                    ["00:53:11", "16 Patrick Fiori et Florent Pagny - J y vais", "16 Patrick Fiori et Florent Pagny - J y vais"],
                    ["00:56:36", "17 Keen V - Je garde le sourire", "17 Keen V - Je garde le sourire"],
                    ["00:59:23", "18 Vitaa et Slimane - Je te le donne", "18 Vitaa et Slimane - Je te le donne"],
                    ["01:03:36", "19 Barbara Pravi - Voilà", "19 Barbara Pravi - Voilà"],
                    ["01:06:58", "20 Amel Bent - 1, 2, 3", "20 Amel Bent - 1, 2, 3"],
                    ["01:09:12", "21 M Pokora - Les planètes", "21 M Pokora - Les planètes"],
                    ["01:12:52", "22 Vitaa et Slimane - Avant toi", "22 Vitaa et Slimane - Avant toi"],
                    ["01:16:28", "23 Les Frangines - Deven Quelqu un", "23 Les Frangines - Deven Quelqu un"],
                    ["01:19:40", "24 Julien Doré - Nous", "24 Julien Doré - Nous"],
                    ["01:22:27", "25 Amir - On verra bien", "25 Amir - On verra bien"]
                    ]
    table_millisecondes = rewrite_horodatage_table(table_minutes)
    """split_rules = []
    for el in table_millisecondes:
        print(el)
        split_rules.append(Split_rule(el))"""
    split_rules = [Split_rule(el) for el in table_millisecondes]
    print("Téléchargement de la video en MP3", url_YT)
    full_video = download_youtube_url(url_YT)
    split_mp3file(full_video, split_rules)

"""
Splitter 
rom pydub import AudioSegment


"""