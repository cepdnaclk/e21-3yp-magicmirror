import asyncio
import subprocess
import shutil
import os
import signal
import sys
import re
import threading
import time

import speech_recognition as sr
import edge_tts
import yt_dlp

# =========================
# CONFIG
# =========================

ALSA_MIC_CARD  = "plughw:2,0"
RECORD_SECONDS = 4
SAMPLE_RATE    = 16000
CHANNELS       = 1

VOICE = "en-GB-SoniaNeural"

# Wake words - ONLY these trigger actions
# Everything else is IGNORED
WAKE_WORDS = {
    'play': 'play',
    'stop': 'stop',
    'stop music': 'stop',
    'pause': 'pause',
    'pause music': 'pause',
    'resume': 'resume',
    'resume music': 'resume',
    'continue': 'resume',
    'continue music': 'resume',
    'exit': 'exit',
    'quit': 'exit',
    'mirror stop': 'stop',
    'mirror pause': 'pause',
    'mirror play': 'play',
    'mirror resume': 'resume',
    'mirror exit': 'exit',
}

ffplay_process = None
paused         = False
listening      = True


# =========================
# SUPPRESS ALSA SPAM
# =========================

def suppress_alsa():
    """Hide ALSA error messages."""
    try:
        from ctypes import cdll, c_char_p, c_int, CFUNCTYPE
        ERROR_HANDLER = CFUNCTYPE(None, c_char_p, c_int,
                                  c_char_p, c_int, c_char_p)
        def py_error_handler(filename, line, function, err, fmt):
            pass
        c_error_handler = ERROR_HANDLER(py_error_handler)
        asound = cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
    except Exception:
        pass

suppress_alsa()


# =========================
# TTS
# =========================

async def speak(text):
    """Speak text via edge-tts."""
    filename = "/tmp/tts_output.mp3"
    try:
        print(f"  [TTS] {text}")
        tts = edge_tts.Communicate(text, VOICE)
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

# =========================
# RECORD AUDIO
# =========================

def record_audio(duration=None):
    """Record voice using arecord."""
    if duration is None:
        duration = RECORD_SECONDS

    output_file = "/tmp/voice_cmd.wav"

    if os.path.exists(output_file):
        os.remove(output_file)

    cmd = [
        "arecord",
        "-D", ALSA_MIC_CARD,
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", str(CHANNELS),
        "-d", str(duration),
        "-q",
        output_file
    ]

    try:
        subprocess.run(
            cmd,
            timeout=duration + 5,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            if size > 500:
                return output_file

    except Exception:
        pass

    return None


# =========================
# SPEECH TO TEXT
# =========================

def transcribe(wav_file):
    """Convert WAV to text using Google."""
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(wav_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.record(source)

        # Try English
        try:
            text = recognizer.recognize_google(
                audio, language="en-US"
            ).lower().strip()
            return text, False
        except sr.UnknownValueError:
            pass

        # Try Sinhala
        try:
            text = recognizer.recognize_google(
                audio, language="si-LK"
            ).strip()
            return text, True
        except sr.UnknownValueError:
            pass

        return None, False

    except sr.RequestError as e:
        print(f"  [API Error] {e}")
        return None, False
    except Exception as e:
        print(f"  [Error] {e}")
        return None, False

# =========================
# CHECK IF AUDIO HAS SPEECH
# =========================

def has_speech(wav_file):
    """
    Quick check if the WAV file has significant audio.
    Avoids sending silence to Google API.
    """
    try:
        import wave
        import struct
        import math

        with wave.open(wav_file, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            sample_count = len(frames) // 2  # 16-bit = 2 bytes
            if sample_count == 0:
                return False

            # Calculate RMS volume
            total = 0
            for i in range(0, len(frames), 2):
                if i + 1 < len(frames):
                    sample = struct.unpack('<h', frames[i:i+2])[0]
                    total += sample * sample

            rms = math.sqrt(total / sample_count)

            # If RMS > 500, there's likely speech
            # Adjust this value based on your environment
            has_audio = rms > 500
            if has_audio:
                print(f"  [Audio] Speech detected (RMS: {rms:.0f})")
            return has_audio

    except Exception:
        return True  # If check fails, try transcribing anyway

# =========================
# MUSIC CONTROL
# =========================

def is_music_playing():
    """Check if music is currently playing."""
    global ffplay_process
    return ffplay_process is not None and ffplay_process.poll() is None


async def play_youtube_music(song, is_sinhala=False):
    """Search YouTube and play music."""
    global ffplay_process, paused

    if is_music_playing():
        await stop_music(announce=False)

    song = song.strip() or "relaxing music"

    # Build search query
    if is_sinhala:
        if not any(w in song.lower() for w in
                   ['sinhala', 'sri lanka']):
            search_query = f"{song} sinhala song"
        else:
            search_query = song
    else:
        search_query = song

    print(f"  [Music] Searching: '{search_query}'")

    try:
        ydl_opts = {
            "default_search": "ytsearch",
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        loop = asyncio.get_event_loop()

        def fetch():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(
                    f"ytsearch1:{search_query}",
                    download=False
                )

        info = await loop.run_in_executor(None, fetch)

        if not info or "entries" not in info or not info["entries"]:
            await speak(f"Sorry, could not find {song}.")
            return

        entry = info["entries"][0]

        audio_url = entry.get("url")
        if not audio_url and "formats" in entry:
            for fmt in reversed(entry["formats"]):
                if fmt.get("acodec") != "none":
                    audio_url = fmt.get("url")
                    break

        if not audio_url:
            await speak("Could not get audio stream.")
            return

        title = entry.get("title", song)
        print(f"  [Music] ? Playing: {title}")

        short_title = title[:40] if len(title) > 40 else title
        await speak(f"Now playing {short_title}")

        ffplay_process = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit",
             "-loglevel", "quiet", audio_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        paused = False

    except Exception as e:
        print(f"  [Music Error] {e}")
        await speak("Error playing music.")
        ffplay_process = None


async def stop_music(announce=True):
    """Stop music."""
    global ffplay_process, paused

    if is_music_playing():
        try:
            pgid = os.getpgid(ffplay_process.pid)
            os.killpg(pgid, signal.SIGTERM)
            try:
                ffplay_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(pgid, signal.SIGKILL)
                ffplay_process.wait()
        except Exception:
            pass
        finally:
            ffplay_process = None
            paused = False
            print("  [Music] ? Stopped")
            if announce:
                await speak("Music stopped.")
    else:
        if announce:
            print("  [Music] Nothing playing")

async def pause_music():
    """Pause music."""
    global paused

    if is_music_playing() and not paused:
        try:
            os.killpg(os.getpgid(ffplay_process.pid), signal.SIGSTOP)
            paused = True
            print("  [Music] ? Paused")
            await speak("Music paused.")
        except Exception as e:
            print(f"  [Pause Error] {e}")
    elif paused:
        await speak("Already paused.")
    else:
        await speak("No music is playing.")


async def resume_music():
    """Resume music."""
    global paused

    if is_music_playing() and paused:
        try:
            os.killpg(os.getpgid(ffplay_process.pid), signal.SIGCONT)
            paused = False
            print("  [Music] ? Resumed")
            await speak("Music resumed.")
        except Exception as e:
            print(f"  [Resume Error] {e}")
    elif not paused and is_music_playing():
        await speak("Already playing.")
    else:
        await speak("No music to resume.")

# =========================
# COMMAND PARSING
# =========================

def parse_command(command, is_sinhala_detected=False):
    """
    Parse voice command. Only recognizes WAKE WORDS.
    Random speech is IGNORED.

    Returns: (action, song_name, is_sinhala)
             action = 'play', 'stop', 'pause', 'resume', 'exit', 'ignore'
    """
    if not command:
        return 'ignore', None, False

    cmd = command.lower().strip()

    # ============================================
    # RULE 1: Must start with a wake word
    # ============================================

    # Check for PLAY command
    # Must start with "play" keyword
    play_triggers = [
        'play me some', 'play me a', 'play me',
        'play some', 'play a', 'play the', 'play',
        'mirror play',
    ]

    for trigger in play_triggers:
        if cmd.startswith(trigger):
            song = cmd[len(trigger):].strip()

            # Check if Sinhala requested
            is_sinhala = is_sinhala_detected
            if any(w in song.lower() for w in
                   ['sinhala', 'sinhalese', 'sri lanka']):
                is_sinhala = True

            if not song:
                song = "relaxing music"

            return 'play', song, is_sinhala

    # Check for CONTROL commands
    # These are exact or near-exact matches
    control_commands = {
        'stop':           'stop',
        'stop music':     'stop',
        'stop playing':   'stop',
        'stop it':        'stop',
        'mirror stop':    'stop',

        'pause':          'pause',
        'pause music':    'pause',
        'pause it':       'pause',
        'mirror pause':   'pause',

        'resume':         'resume',
        'resume music':   'resume',
        'continue':       'resume',
        'continue music': 'resume',
        'mirror resume':  'resume',
        'unpause':        'resume',

        'exit':           'exit',
        'quit':           'exit',
        'goodbye':        'exit',
        'mirror exit':    'exit',
        'mirror quit':    'exit',
        'shut down':      'exit',
    }

    # Check exact match first
    if cmd in control_commands:
        return control_commands[cmd], None, False

    # Check if command STARTS with control word
    for keyword, action in control_commands.items():
        if cmd.startswith(keyword):
            return action, None, False

    # ============================================
    # RULE 2: If Sinhala detected and starts with
    #         known Sinhala play words
    # ============================================
    if is_sinhala_detected:
        sinhala_play = ['?????', '????', 'play']
        sinhala_stop = ['????', '??????', '???']

        for w in sinhala_stop:
            if w in command:
                return 'stop', None, False

        for w in sinhala_play:
            if w in command:
                song = command
                for sw in sinhala_play:
                    song = song.replace(sw, '').strip()
                return 'play', song or command, True

    # ============================================
    # RULE 3: IGNORE everything else
    # ============================================
    return 'ignore', None, False


# =========================
# MAIN LOOP
# =========================

async def main():
    print("=" * 55)
    print("   Magic Mirror - Voice Music Player")
    print(f"   Mic: {ALSA_MIC_CARD}")
    print("=" * 55)

    # Test mic
    print("\n  [Setup] Testing microphone...")
    result = subprocess.run(
        ["arecord", "-D", ALSA_MIC_CARD,
         "-f", "S16_LE", "-r", str(SAMPLE_RATE),
         "-c", "1", "-d", "1", "-q",
         "/tmp/mic_test.wav"],
        capture_output=True, timeout=5
    )

    if result.returncode == 0:
        size = os.path.getsize("/tmp/mic_test.wav")
        print(f"  [Setup] Mic OK ({size} bytes)")
        os.remove("/tmp/mic_test.wav")
    else:
        print("  [Setup] ERROR: Mic not working!")
        print(f"  Check: arecord -D {ALSA_MIC_CARD} -d 2 -f S16_LE -r {SAMPLE_RATE} -c 1 /tmp/t.wav")
        return

    print("\n" + "=" * 55)
    print("   HOW TO USE:")
    print("")
    print('   Say "play [song name]"  to play a song')
    print('   Say "play sinhala [name]" for Sinhala songs')
    print('   Say "stop"  to stop music')
    print('   Say "pause" to pause music')
    print('   Say "resume" to resume music')
    print('   Say "exit"  to quit')
    print("")
    print("   Normal conversation is IGNORED.")
    print("   Only wake commands trigger actions.")
    print("=" * 55)

    await speak(
        "Music player ready. "
        "Say play followed by a song name to start music. "
        "Say stop to stop. "
        "Normal conversation will be ignored."
    )

    while True:
        try:
            # Show status
            if is_music_playing():
                if paused:
                    status = "? PAUSED"
                else:
                    status = "? PLAYING"
            else:
                status = "? IDLE"

            print(f"\n  [{status}] Listening... "
                  f"(speak 'play/stop/pause/resume')")

            # Record audio
            wav_file = record_audio()

            if not wav_file:
                continue

            # Check if there's actual speech
            if not has_speech(wav_file):
                # Silent - skip transcription
                if os.path.exists(wav_file):
                    os.remove(wav_file)
                continue

            # Transcribe
            command, is_sinhala = transcribe(wav_file)

            # Cleanup
            if os.path.exists(wav_file):
                os.remove(wav_file)

            if not command:
                continue

            # Parse command - ONLY wake words trigger action
            action, param, sinhala = parse_command(
                command, is_sinhala
            )

            if action == 'ignore':
                # Not a music command - SKIP
                print(f"  [Ignored] '{command}' "
                      f"(not a music command)")
                continue

            # Valid command detected!
            print(f"  [Command] {action.upper()} "
                  f"| '{param}' | sinhala={sinhala}")

            if action == 'play':
                await play_youtube_music(param, sinhala)

            elif action == 'stop':
                await stop_music()

            elif action == 'pause':
                await pause_music()

            elif action == 'resume':
                await resume_music()

            elif action == 'exit':
                await stop_music(announce=False)
                await speak("Goodbye!")
                break

        except KeyboardInterrupt:
            print("\n  [System] Ctrl+C")
            await stop_music(announce=False)
            break

        except Exception as e:
            print(f"  [Error] {e}")
            await asyncio.sleep(1)



# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    # Check tools
    missing = [t for t in ['arecord', 'ffplay']
               if not shutil.which(t)]

    if missing:
        print(f"  [ERROR] Missing: {missing}")
        print("  Install: sudo apt install alsa-utils ffmpeg")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Shutdown.")
    finally:
        subprocess.run(
            ["pkill", "-f", "ffplay"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
