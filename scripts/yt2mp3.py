# coding: utf-8

from pytube import YouTube
import  os
import yt_dlp
from csv import reader
from stdf import *

explain = """Import d'URL de fichiers musique trouvés sur Youtube
En entrée, un fichier à 2 colonnes : URL | Nom du fichier """

def progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(f"Descărcare: {percentage_of_completion:.2f}% completă.")

def download_mp3(video_url, output_path, i=None):
    yt = YouTube(video_url)
    yt.register_on_progress_callback(progress)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_stream.download(output_path)
    print(f"Descărcarea melodiei '{yt.title}' este completă.")

def download_youtube_audio(url: str, filename: str):
    """
    Télécharge l'audio d'une vidéo YouTube en MP3.

    :param url: URL de la vidéo YouTube
    :param filename: Nom du fichier de sortie (sans extension)
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{filename}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # Qualité en kbps
        }],
        'quiet': False,  # mettre True pour moins de logs
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_youtube_mp3_v2(url: str, output_dir: str = "."):
    """
    Télécharge la piste audio d'une vidéo YouTube en MP3.

    - url : URL de la vidéo YouTube
    - output_dir : dossier où enregistrer le fichier
    """

    # S'assurer que le dossier existe
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [
            {   # Convertir en MP3
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",  # ou 320 si vous préférez
            }
        ],
        "quiet": False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_youtube_mp3_v3(url: str, output_dir: str = "."):
    """
    Télécharge l'audio d'une vidéo YouTube et le convertit en MP3.
    Fonction robuste : évite les erreurs de format non disponible.
    """

    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),

        # IMPORTANT :
        # 'bestaudio' prend n'importe quel format audio disponible sans imposer un format impossible.
        "format": "bestaudio",

        # Convertir l'audio obtenu en MP3 via ffmpeg
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],

        # Pour éviter d'interrompre le téléchargement si un paramètre manque
        "ignoreerrors": True,
        "verbose": False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    print(explain, "\n")
    fname = input("Nom du fichier (2 colonnes) contenant les URL/nom de fichier : ")
    output_path = input("Dossier où déposer les fichiers : ")
    liste_fichiers = file2list(fname, all_cols=True)

    i = 1
    for piste in liste_fichiers:
        # download_youtube_mp3_v2(piste[0], os.path.join(output_path, piste[1]))
        download_youtube_mp3_v3(piste[0], output_path)