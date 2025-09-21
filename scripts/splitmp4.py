# coding: utf-8

"""
Découpage d'un fichier
"""

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import *
import os


"""times = [ [0, 9], 
          [11, 94],
          [96, 115],
          [120, 150], 
          [152, 191],
        ]"""

times_static = [[0, 6*60+20]]  # si besoin d'écrire en dur un minutage multiple
# times_static = [[58*60+48, 1*60*60+3*60+48]]
# times = [[2*60*60+13*60+34, 2*60*60+15*60+6]]

def combine_videos_folder_to_one(dirname, filename, nouveau_fname, times):
    if times == "":
       times = times_static
    if nouveau_fname == "":
       nouveau_fname = "compilation_output.mp4"
    filename = os.path.join(dirname, filename)
    clip = VideoFileClip(filename)
    L = []
    for time in times:
      subclip = clip.subclip(time[0], time[1]+1)
      L.append(subclip)
    print("\nconcaténation de toutes les videos")
    final_clip = concatenate_videoclips(L, method='chain')
    if filename.endswith(".mkv"):
      final_clip.write_videofile(os.path.join(dirname, nouveau_fname), codec="libx264")
    else:
       final_clip.write_videofile(os.path.join(dirname, nouveau_fname))
    try:
      os.remove("compilation_outputTEMP_MPY_wvf_snd.mp3")
    except FileNotFoundError:
      pass

def rewrite_times(t):
   h, m, s = t.split(":")
   h = int(h)*60*60
   m = int(m)*60
   s = int(s)
   return h + m + s

if __name__ == "__main__":
    dirname = input("Nom du dossier où se trouve le film : ")
    filename = input("Nom du fichier film : ")
    nouveau_fname = input("Nom du fichier video en sortie : ")
    time_debut = input("heure de début (séparateur : ) : ")
    time_fin = input("heure de fin (séparateur : ) : ")
    times = [[rewrite_times(time_debut), rewrite_times(time_fin)]]
    combine_videos_folder_to_one(dirname, filename, nouveau_fname, times)