from utils.audio_processor import process_input
from core.transcriber import transcribe_all

source="https://youtu.be/V_OlWyt8g7I?si=CDArlAuUcJj5Uj20"

chunks=process_input(source)
print(transcribe_all(chunks))





#taskkill /F /IM chrome.exe   tasklist | findstr chrome
#tasklist | findstr chrome   python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"
#python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"
#python -m yt_dlp --cookies-from-browser "chrome:Profile 8" -f bestaudio "https://youtu.be/TioxU0wdMQg"