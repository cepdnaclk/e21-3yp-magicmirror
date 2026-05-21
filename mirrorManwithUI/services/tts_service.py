import os
import subprocess


# ================= TTS via edge-tts + pygame (used by SinhalaBot / main app) =================
def speak_pygame(text, voice="si-LK-ThiliniNeural"):
<<<<<<< HEAD
    """High-quality TTS that uses edge-tts + pygame for playback.
    Originally from main2.py SinhalaBot.speak()
    """
    try:
        import edge_tts
        import asyncio
        import pygame
        import tempfile
=======
    """High-quality TTS that uses edge-tts + pygame for English playback,
    and Google TTS (gTTS) for highly natural, smooth Sinhala playback.
    """
    try:
        import pygame
        import tempfile
        import io
>>>>>>> 7ba0e81460e52796aca50480eaeb7445046ac0df

        if not pygame.mixer.get_init():
            pygame.mixer.init()

<<<<<<< HEAD
=======
        # If it is a Sinhala voice request, use Google TTS (gTTS) - it is significantly smoother
        if voice.startswith("si-LK") or any('\u0d80' <= c <= '\u0dff' for c in text):
            from gtts import gTTS
            
            # Generate to a temporary file for stable Pygame playback
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_filename = fp.name
                
            tts = gTTS(text=text, lang='si')
            tts.save(temp_filename)
            
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            try:
                os.remove(temp_filename)
            except:
                pass
            return

        # For English, use edge-tts (already very smooth)
        import edge_tts
        import asyncio

>>>>>>> 7ba0e81460e52796aca50480eaeb7445046ac0df
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
<<<<<<< HEAD

    filename = "/tmp/tts_output.mp3"
=======
    import tempfile

    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, "tts_output_ffplay.mp3")
>>>>>>> 7ba0e81460e52796aca50480eaeb7445046ac0df
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
