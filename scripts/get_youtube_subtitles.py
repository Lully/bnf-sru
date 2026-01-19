# coding: utf-8

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def get_video_id(url):
    """
    Extract the video ID from a YouTube URL
    """
    if 'youtube.com/watch?v=' in url:
        return url.split('v=')[1]
    elif 'youtu.be/' in url:
        return url.split('be/')[1]
    else:
        raise ValueError("Invalid YouTube URL")

def fetch_available_languages(video_id):
    """
    Fetch available languages for the YouTube video transcript.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        languages = []

        # Iterate over the transcript list to get the languages
        for transcript in transcript_list:
            languages.append((transcript.language, transcript.language_code))

        return languages
    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
        return []
    except NoTranscriptFound:
        print("No transcripts found for this video.")
        return []

def choose_language(languages):
    """
    Display available languages and allow the user to choose one.
    """
    print("\nAvailable languages:")
    for idx, (language, code) in enumerate(languages):
        print(f"{idx + 1}. {language} ({code})")

    choice = int(input("\nEnter the number of the language you want to select: ")) - 1
    if choice < 0 or choice >= len(languages):
        print("Invalid choice. Please run the program again.")
        exit()

    return languages[choice][1]

def download_transcript(video_id, language_code, output_file):
    """
    Download the YouTube transcript in the selected language and save it to a .txt file.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in transcript:
                timestamp = format_time(entry['start'])
                f.write(f"{timestamp} - {entry['text']}\n")
        print(f"Transcript saved to {output_file}")
    except Exception as e:
        print(f"Error fetching transcript: {e}")

def format_time(seconds):
    """
    Format timestamp from seconds to HH:MM:SS.
    """
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"

def preview_transcript(output_file, lines=5):
    """
    Display the first 'n' lines of the transcript.
    """
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            transcript_lines = f.readlines()
            print("\nPreview of the transcript:")
            for line in transcript_lines[:lines]:
                print(line.strip())
    except Exception as e:
        print(f"Error reading the transcript file: {e}")

if __name__ == "__main__":
    url = input("Enter the YouTube video URL: ")
    video_id = get_video_id(url)

    # Fetch available languages
    languages = fetch_available_languages(video_id)

    if languages:
        # Ask user to select a language
        language_code = choose_language(languages)

        # Download transcript and save to file
        output_file = f"youtube_transcript_{video_id}_{language_code}.txt"
        download_transcript(video_id, language_code, output_file)

        # Preview the first 5 sentences of the transcript
        preview_transcript(output_file, 5)
    else:
        print("No available languages for this video.")