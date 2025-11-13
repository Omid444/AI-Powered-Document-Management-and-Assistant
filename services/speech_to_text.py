# services/speech_to_text.py

from openai import OpenAI
from io import BytesIO

client = OpenAI()

async def speech_to_text_service(audio_bytes: bytes) -> str:
    """
    Convert spoken audio (webm) to text using OpenAI Whisper.
    """

    # تبدیل بایت‌ها به فایل در حافظه
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "input.webm"  # بسیار مهم: Whisper به نام فایل اهمیت می‌دهد

    response = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",   # مدل جدید whisper
        file=audio_file,
        response_format="text"
    )

    return response
