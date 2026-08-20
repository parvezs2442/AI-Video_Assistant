from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import generate_title, summarize
import os


print("Key Loaded: ", os.getenv("SARVAM_API_KEY"))
print("CWD", os.getcwd())

source="https://youtu.be/tehb7mAdu-4?si=wMyj1zGmqibjbkd5"
language= 'hinglish'

chunks = process_input(source)

transcript = transcribe_all(chunks, language=language)
print("\n" + "=" * 60)
print("TRANSCRIPT")
print("=" * 60)
print(transcript[:500] + "..." if len(transcript) > 500 else transcript)

title = generate_title(transcript)
summary = summarize(transcript)

print("\n" + "=" * 60)
print(f"TITLE: {title}")
print("=" * 60)
print("\nSUMMARY")
print("=" * 60)
print(summary)






#taskkill /F /IM chrome.exe   tasklist | findstr chrome
#tasklist | findstr chrome   python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"
#python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"
#python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"




