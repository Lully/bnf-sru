# coding: utf-8

"""
Découpage d'un fichier
"""

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import *
import os

dirname = r""
filename = r""

# Replace the filename below.
required_video_file = os.path.join(dirname, filename)

times = [[15, 28], 
         [33, 66],
         [70, 97]
        ]

def combine_videos_folder_to_one(folder_path):
    filename = os.path.join(dirname, "video.mp4")
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

    
combine_videos_folder_to_one(dirname)