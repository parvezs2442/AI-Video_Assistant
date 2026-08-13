import yt_dlp
from pydub import AudioSegment
import os

#Extract/download the audio from any video using link/url

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
FFMPEG_PATH = r"C:\Users\PARVEZ SAIFI\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin"

def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        # FFmpeg location
        "ffmpeg_location": FFMPEG_PATH,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True, #removes unnecessary consoles
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )
        filename = ydl.prepare_filename(info)
        filename = filename.replace(".webm", ".wav")
        filename = filename.replace(".m4a", ".wav")
    return filename

if __name__ == "__main__":

    youtube_url = "https://youtu.be/xKOyDDuQSVY?si=pAXzggqsc-IGMzQQ"
    audio_file = download_youtube_audio(youtube_url)
   

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")

    return output_path

data_final = convert_to_wav(audio_file)



def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)  #extracting the audio from wavepath
    chunk_ms = chunk_minutes * 60 *1000 
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]  #create chunks
        chunk_path = f"{wav_path}_chunk_{i}.wav" #defining chunk name
        chunk.export(chunk_path, format="wav") #exporting chunk file

        chunks.append(chunk_path) # appending chunk into chunks list
    return chunks

print(chunk_audio(data_final))

