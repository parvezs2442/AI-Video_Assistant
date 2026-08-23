import os
import re
import shutil
import hashlib
import yt_dlp
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_ffmpeg_path() -> str:
    """Resolve FFmpeg binary location dynamically."""
    # 1. Check environment variable
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 2. Check system PATH
    sys_path = shutil.which("ffmpeg")
    if sys_path:
        return os.path.dirname(sys_path)
    
    # 3. Fallback to hardcoded local path
    fallback_path = r"C:\Users\PARVEZ SAIFI\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin"
    if os.path.exists(fallback_path):
        return fallback_path
        
    return ""

# Initialize pydub converter location
ffmpeg_dir = get_ffmpeg_path()
if ffmpeg_dir:
    AudioSegment.converter = os.path.join(ffmpeg_dir, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    print(f"FFmpeg located at: {ffmpeg_dir}")
else:
    print("Warning: FFmpeg was not found in PATH or environment variables. Local processing may fail.")


def extract_video_id(url: str) -> str:
    """Extract YouTube 11-character video ID from a URL."""
    patterns = [
        r'(?:v=|\/)([\w-]{11})(?:\?|&|$)',
        r'youtu\.be\/([\w-]{11})',
        r'embed\/([\w-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def get_ydl_opts(output_template: str) -> dict:
    """Build yt-dlp configurations dynamically, resolving FFmpeg and cookies."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "js_runtimes": {
            "deno": {}
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }
    
    # Add FFmpeg location
    if ffmpeg_dir:
        ydl_opts["ffmpeg_location"] = ffmpeg_dir
        
    # Cookie priority: 1) local cookies.txt, 2) browser cookies fallback
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
        print("Using local cookies.txt for YouTube downloading.")
    else:
        ydl_opts["cookiesfrombrowser"] = ("chrome", "firefox", "edge")
        print("cookies.txt not found. Falling back to extracting cookies from Chrome/Firefox/Edge.")
        
    return ydl_opts


def fetch_youtube_transcript(video_id: str) -> list:
    """Attempt to download transcripts/captions directly via API."""
    try:
        print(f"Attempting direct caption extraction for video: {video_id}...")
        # Try retrieving English first, fallback to Auto-generated or Hindi
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
        transcript = []
        for entry in srt:
            start = entry['start']
            end = start + entry['duration']
            transcript.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'text': entry['text'].strip()
            })
        print(f"Successfully extracted {len(transcript)} transcript segments directly from YouTube.")
        return transcript
    except Exception as e:
        print(f"Direct caption extraction failed: {e}. Falling back to audio download & transcription.")
        return None


def download_youtube_audio(url: str) -> str:
    """Download audio of a YouTube video to a WAV file."""
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = get_ydl_opts(output_path)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
    filename = os.path.splitext(filename)[0] + ".wav"
    return filename


def convert_to_wav(input_path: str) -> str:
    """Convert any local audio/video file to Whisper-compatible mono 16kHz WAV."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    
    # Avoid re-conversion if it already exists
    if os.path.exists(output_path):
        print(f"Converted WAV already exists: {output_path}")
        return output_path
        
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Split a WAV file into smaller chunks to prevent transcription memory/time issues."""
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        
        # Avoid recreating chunks if they already exist
        if not os.path.exists(chunk_path):
            chunk.export(chunk_path, format="wav")
            
        chunks.append(chunk_path)
        
    return chunks


def process_input(source: str) -> dict:
    """
    Process user input (URL or local path).
    Returns a structured dictionary:
    {
       "type": "youtube_transcript" or "audio_chunks",
       "data": list of segment dicts (for transcript) or list of file paths (for chunks),
       "video_id": str (unique key),
       "video_title": str,
       "video_url": str
    }
    """
    video_id = ""
    video_title = ""
    
    if source.startswith("http://") or source.startswith("https://"):
        video_id = extract_video_id(source)
        if not video_id:
            # Fallback hash of URL if extraction fails
            video_id = hashlib.md5(source.encode()).hexdigest()
            
        print(f"Detected YouTube URL. Video ID: {video_id}")
        
        # Get video metadata (Title) via fast yt-dlp check
        try:
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
            }
            if os.path.exists("cookies.txt"):
                ydl_opts["cookiefile"] = "cookies.txt"
            else:
                ydl_opts["cookiesfrombrowser"] = ("chrome", "firefox", "edge")
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source, download=False)
                video_title = info.get("title", f"YouTube Video {video_id}")
        except Exception as e:
            print(f"Warning: Could not fetch video title: {e}")
            video_title = f"YouTube Video {video_id}"
            
        # Try direct caption extraction first
        transcript = fetch_youtube_transcript(video_id)
        if transcript:
            return {
                "type": "youtube_transcript",
                "data": transcript,
                "video_id": video_id,
                "video_title": video_title,
                "video_url": source
            }
            
        # Fallback to audio download
        print("Downloading audio to perform local/API transcription...")
        wav_path = download_youtube_audio(source)
        chunks = chunk_audio(wav_path)
        return {
            "type": "audio_chunks",
            "data": chunks,
            "video_id": video_id,
            "video_title": video_title,
            "video_url": source
        }
        
    else:
        # Local file path
        filename = os.path.basename(source)
        video_title = os.path.splitext(filename)[0]
        # Generate video_id from filepath hash
        video_id = hashlib.md5(os.path.abspath(source).encode()).hexdigest()
        
        print(f"Detected Local file. Converting into WAV: {filename}...")
        wav_path = convert_to_wav(source)
        chunks = chunk_audio(wav_path)
        
        return {
            "type": "audio_chunks",
            "data": chunks,
            "video_id": video_id,
            "video_title": video_title,
            "video_url": source
        }