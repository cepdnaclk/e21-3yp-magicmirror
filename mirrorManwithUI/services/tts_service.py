import os
import subprocess


# ================= TTS via edge-tts + pygame (used by SinhalaBot / main app) =================
def speak_pygame(text, voice="si-LK-ThiliniNeural"):
    """High-quality TTS that uses edge-tts + pygame for playback.
    Originally from main2.py SinhalaBot.speak()
    """
    try:
        import edge_tts
        import asyncio
        import pygame
        import tempfile

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Generate to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name

        # Run edge-tts asynchronously inside a new loop
        communicate = edge_tts.Communicate(text, voice)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(communicate.save(temp_filename))
        loop.close()

        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()

        # This loop ensures the 'idle' signal doesn't send too early
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        try:
            os.remove(temp_filename)
        except:
            pass

    except Exception as e:
        print(f"❌ TTS Error: {e}")
        fallback_speak(text)


# ================= FALLBACK TTS via gTTS + pygame =================
def fallback_speak(text):
    """Fallback TTS using gTTS. Originally from main2.py SinhalaBot._fallback_speak()"""
    try:
        from gtts import gTTS
        import io
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        tts = gTTS(text=text, lang='si')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()

        # This loop ensures the 'idle' signal doesn't send too early
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"❌ Fallback TTS Error: {e}")


# ================= TTS via edge-tts + ffplay (used by MusicAssistant on RPi) =================
async def speak_ffplay(text, voice="en-GB-SoniaNeural"):
    """Speak text via edge-tts + ffplay. Originally from MusicAssistant.py speak()"""
    import edge_tts

    filename = "/tmp/tts_output.mp3"
    try:
        print(f"  [TTS] {text}")
        tts = edge_tts.Communicate(text, voice)
        await tts.save(filename)

        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit",
             "-loglevel", "quiet", filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        print(f"  [TTS Error] {e}")
