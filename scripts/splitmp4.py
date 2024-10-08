# coding: utf-8

"""
Découpage d'un fichier
"""

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import *
import os

dirname = r"C:\Users\lully\Documents\zoom\2023-05-20 19.15.39 géraud cavalié - salle de réunion personnelle"
filename = r"video1692203011.mp4"

dirname = r"C:\Users\lully\Documents\Films\It's a wonderful Life (la vie est belle) (1946)"
filename = r"It's a Wonderful Life (1946).mp4"


"""times = [ [0, 9], 
          [11, 94],
          [96, 115],
          [120, 150], 
          [152, 191],
        ]"""

times = [[50*60+15, 58*60+48]]
times = [[58*60+48, 1*60*60+3*60+48]]
# times = [[2*60*60+13*60+34, 2*60*60+15*60+6]]

def combine_videos_folder_to_one(dirname, filename):
    filename = os.path.join(dirname, filename)
    clip = VideoFileClip(filename)
    L = []
    for time in times:
      subclip = clip.subclip(time[0], time[1]+1)
      L.append(subclip)
    print("\nconcaténation de toutes les videos")
    final_clip = concatenate_videoclips(L, method='chain')
    final_clip.write_videofile(os.path.join(dirname, "compilation_output.mp4"))
    try:
      os.remove("compilation_outputTEMP_MPY_wvf_snd.mp3")
    except FileNotFoundError:
      pass

    
combine_videos_folder_to_one(dirname, filename)