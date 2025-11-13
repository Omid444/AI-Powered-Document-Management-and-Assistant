# services/text_to_speech.py

from openai import OpenAI
import base64

client = OpenAI()

async def text_to_speech_service(text: str) -> dict:
    """
    Convert text response to mp3 audio using OpenAI TTS (gpt-4o-mini-tts).
    """

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",                # صدای پیش‌فرض
        input=text,
        format="mp3"
    )

    # خروجی بایت‌های mp3
    audio_bytes = response.read()

    # تبدیل به base64 برای ارسال به فرانت
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {
        "text": text,
        "audio": audio_base64
    }
