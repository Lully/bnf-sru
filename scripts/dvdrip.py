# coding=utf-8

# Fonction fournie par ChatGPT


import ffmpeg
import subprocess
import json
import shutil
import os
import tempfile

def get_audio_streams_info(dvd_path):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'stream=index,codec_type',
        '-of', 'json',
        dvd_path
    ]
    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    streams_info = json.loads(output)['streams']
    audio_streams = [stream['index'] for stream in streams_info if stream['codec_type'] == 'audio']
    return audio_streams

def convert_dvd_to_mp4(dvd_path, num_vob, output_file):
    temp_dir = dvd_path
    if dvd_path == "D:\\VIDEO_TS" or dvd_path == "E:\\VIDEO_TS":
        temp_dir = tempfile.mkdtemp()
        print("Création du dossier temporaire", temp_dir)
        # Copier le contenu du DVD dans le dossier temporaire
        for item in os.listdir(dvd_path):
            if item.lower().endswith(('.vob')) and f"{num_vob}_" in item and "_0.vob" not in item.lower():
                print("Copie de ", item)
                item_path = os.path.join(dvd_path, item)
                if os.path.isfile(item_path):
                    shutil.copy(item_path, temp_dir)
        
    # Convertir les fichiers vidéo dans le dossier temporaire
    input_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) 
                   if f.lower().endswith(('.vob')) and f"{num_vob}_" in f and "_0.vob" not in f.lower()]
    
    audio_streams = get_audio_streams_info(input_files[0])
    map_string = ''.join([f':{i}' for i in range(len(audio_streams))])

    try:
        """(
            ffmpeg
            .input(temp_dir, pattern_type='glob', pattern='*.VOB')
            .output(output_file, vcodec='libx264', acodec='aac', s="750X756", aspect="16:9")
            .run()
        )"""
        (
            ffmpeg
            .concat(*[ffmpeg.input(f) for f in input_files])
            # .output(output_file, vcodec='libx264', acodec='ac3', map='0:a?', c='copy', s='copy')
            .output(output_file, vcodec='libx264', acodec='ac3', map=f'0:a{map_string}?,0:s?', c='copy')  # param "c" = copier les sous-titres. Avec ajout param s : copier tous les sous-titres
            # .output(output_file, vcodec='libx264', acodec='aac', map='0:a?', c='copy')
            
            # .output(output_file, vcodec='libx264', acodec='pcm_s16le')
            # .output(output_file, vcodec='libx264', acodec='aac')
            # .output(output_file, vcodec='libx264', crf=18, preset='slow', acodec='aac')  # meilleure qualité vidéo
            .run()
        )
        print("Conversion terminée avec succès !")
    except ffmpeg.Error as e:
        print(f"Erreur lors de la conversion : {e.stderr}")
        raise
    finally:
        # Supprimer le dossier temporaire
        if dvd_path == "D:\\VIDEO_TS" or dvd_path == "E:\\VIDEO_TS":
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    dvd_path = input("Chemin vers le dossier pointant vers le DVD (par défaut : D:\\VIDEO_TS) : ")
    if dvd_path == "":
        dvd_path = "D:\\VIDEO_TS"
    num_vob = input("Numéro des fichiers VOB à convertir : ")
    output_file = input("Chemin + nom du fichier mp4 en sortie : ")
    convert_dvd_to_mp4(dvd_path, num_vob, output_file)
