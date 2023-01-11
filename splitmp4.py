# coding: utf-8

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import *
import os

dirname = r"D:\Documents\perso\Géraud\24\espagnol"
filename = "video.mp4"

# Replace the filename below.
required_video_file = os.path.join(dirname, filename)

times = [[0, 300], 
         [300, 600],
         [600, 900]
        ]

for time in times:
  starttime = int(time.split("-")[0])
  endtime = int(time.split("-")[1])
  ffmpeg_extract_subclip(required_video_file, starttime, endtime, targetname=os.path.join(dirname, str(times.index(time)+1)+".mp4"))

def combine_videos_folder_to_one(folder_path):
    L =[]
    for root, dirs, files in os.walk(folder_path):
        #files.sort()
        for file in files:
            if file != filename and file.endswith("mp4"):
                filePath = os.path.join(root, file)
                video = VideoFileClip(filePath)
                L.append(video)
    final_clip = concatenate_videoclips(L,method='compose')
    final_clip.to_videofile("compilation_output.mp4", fps=60, remove_temp=False)

    
