import os
from pathlib import Path
from openai import OpenAI

def make_tts(text, outpath):
    key=os.getenv("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY is not configured")
    outpath=Path(outpath); outpath.parent.mkdir(parents=True, exist_ok=True)
    client=OpenAI(api_key=key)
    with client.audio.speech.with_streaming_response.create(model=os.getenv("OPENAI_TTS_MODEL","gpt-4o-mini-tts"), voice=os.getenv("OPENAI_TTS_VOICE","coral"), input=text, response_format="mp3") as response:
        response.stream_to_file(str(outpath))
    return outpath
