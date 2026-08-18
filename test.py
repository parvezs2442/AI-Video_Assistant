from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
import os


print("Key Loaded: ", os.getenv("SARVAM_API_KEY"))
print("CWD", os.getcwd())

source="https://youtu.be/dZyQNy3-HjU?si=0-1lUlGjqjcoLzFV"
language= 'hinglish'

chunks=process_input(source)
transcript = transcribe_all(chunks, language=language)

print("\n=== TRANSCRIPT ===\n")
print(transcript)





#taskkill /F /IM chrome.exe   tasklist | findstr chrome
#tasklist | findstr chrome   python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"
#python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"
#python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"