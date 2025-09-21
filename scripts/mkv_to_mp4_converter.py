import os
import ffmpeg
import tkinter as tk
from tkinter import filedialog

def convert_to_mp4(input_path, output_path):
    try:
        input_filename = os.path.basename(input_path)
        output_filename = os.path.splitext(input_filename)[0] + ".mp4"
        output_file_path = os.path.join(output_path, output_filename)

        ffmpeg.input(input_path).output(output_file_path, vcodec="h264", acodec="aac").run()

        print("Conversion successful. Output file:", output_file_path)
    except Exception as e:
        print("Error during conversion:", str(e))

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("MKV Files", "*.mkv")])
    if file_path:
        output_path = os.path.dirname(file_path)
        convert_to_mp4(file_path, output_path)

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    print("Select an MKV file for conversion to MP4.")
    select_file()

if __name__ == "__main__":
    main()
