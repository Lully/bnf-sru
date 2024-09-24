from pytube import YouTube

def progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(f"Descărcare: {percentage_of_completion:.2f}% completă.")

def download_mp3(video_url, output_path):
    yt = YouTube(video_url)
    yt.register_on_progress_callback(progress)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_stream.download(output_path)
    print(f"Descărcarea melodiei '{yt.title}' este completă.")

video_url = "https://www.youtube.com/watch?v=5TPLX9r6RQY"
output_path = r"C:\Users\lully\Documents\helene\MN\Musique"
download_mp3(video_url, output_path)