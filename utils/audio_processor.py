import yt_dlp
from pydub import AudioSegment
import os


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

        "quiet": True,
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

    youtube_url = "https://www.youtube.com/watch?v=_HQ2H_0Ayy0"

    audio_file = download_youtube_audio(youtube_url)

    print(f"✅ Audio downloaded successfully: {audio_file}")