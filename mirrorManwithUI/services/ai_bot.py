import asyncio
import os
import speech_recognition as sr
import json
from google import genai
from google.genai import types

from models import app_state
from config.settings import CUSTOM_PROMPT, GEMINI_MODEL, GEMINI_PROJECT_ID, ALSA_MIC_CARD
from controllers.websocket_manager import manager
from services.tts_service import speak_pygame


# ================= GEMINI CLIENT =================
import os
from config.settings import GEMINI_PROJECT_ID

gemini_client = None

def get_gemini_client():
    global gemini_client
    if gemini_client is not None:
        return gemini_client
        
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        # Use standard developer API Key
        gemini_client = genai.Client(api_key=api_key)
    else:
        # Fallback to Vertex AI
        try:
            gemini_client = genai.Client(
                vertexai=True,
                project=GEMINI_PROJECT_ID,
                location="global"
            )
        except Exception as e:
            print(f"⚠️ [Gemini Client] Failed to initialize Vertex AI client: {e}", flush=True)
            # Try initializing standard client as a final fallback
            gemini_client = genai.Client()
    return gemini_client


# ================= AI BOT =================
class SinhalaBot:
    def __init__(self):
        self.should_exit = False
        self.is_active = False
        self.is_speaking = False   # True while TTS audio is playing
        self.recognizer = sr.Recognizer()
        # Stores alternating user/model turns for the current conversation session.
        # Cleared at the start of every new wake-word activation.
        self.conversation_history: list[types.Content] = []
        self.MAX_HISTORY_TURNS = 10  # Keep last 10 exchanges (20 messages)

        # Microphone device index — set MIC_DEVICE_INDEX env var to override.
        # Otherwise we auto-resolve it based on the configured ALSA_MIC_CARD.
        _env_idx = os.getenv("MIC_DEVICE_INDEX", "").strip()
        if _env_idx.isdigit():
            self.mic_device_index = int(_env_idx)
        else:
            self.mic_device_index = self._resolve_mic_index(ALSA_MIC_CARD)
        print(f"[Bot] Mic device index: {self.mic_device_index} (Resolved from ALSA_MIC_CARD: '{ALSA_MIC_CARD}')", flush=True)

    def _resolve_mic_index(self, card_str: str):
        """Resolves a card string like 'plughw:2,0' or 'hw:2' to PyAudio device index."""
        import re
        if not card_str:
            return None
        match = re.search(r'(?:plughw|hw):(\d+),(\d+)', card_str)
        if not match:
            # Fall back to checking if the card string itself is just a number
            match = re.search(r'(?:plughw|hw):(\d+)', card_str)
        
        card_idx = match.group(1) if match else None
        
        try:
            mics = sr.Microphone.list_microphone_names()
            # 1. Direct match search
            for idx, name in enumerate(mics):
                name_lower = name.lower()
                # e.g. "hw:2,0" or "plughw:2,0"
                if card_str.lower() in name_lower:
                    return idx
                    
            # 2. Card number search (e.g. searching for card 2 or card_idx=2)
            if card_idx is not None:
                for idx, name in enumerate(mics):
                    name_lower = name.lower()
                    if f"hw:{card_idx}" in name_lower or f"card={card_idx}" in name_lower:
                        return idx
                        
            # 3. Fallback: Search for any USB microphone if we can't find specific ALSA card
            for idx, name in enumerate(mics):
                if "usb" in name.lower():
                    return idx
        except Exception:
            pass
        return None

    async def _recognize_best(self, audio_data):
        """Run English and Sinhala recognition in parallel and return the best result.
        
        The old sequential approach (English first → Sinhala fallback) was unreliable
        because Google's English recognizer returns garbled text for Sinhala speech
        instead of raising UnknownValueError, preventing the Sinhala path from ever running.
        Running both in parallel and picking the result that contains actual Sinhala
        Unicode characters is significantly more accurate.
        """
        async def try_lang(lang):
            try:
                return await asyncio.to_thread(
                    self.recognizer.recognize_google, audio_data, language=lang
                )
            except (sr.UnknownValueError, sr.RequestError):
                return None

        # Fire off both language recognitions at the same time
        en_text, si_text = await asyncio.gather(
            try_lang('en-US'),
            try_lang('si-LK')
        )

        # If Sinhala recognition returned actual Sinhala Unicode characters, prefer it
        if si_text and any('\u0d80' <= c <= '\u0dff' for c in si_text):
            print(f"?? You said (Sinhala): {si_text}")
            return si_text, True

        # If English recognition returned a result, use it
        if en_text:
            print(f"?? You said (English): {en_text}")
            return en_text, False

        # If only Sinhala returned something (no Sinhala chars, could be romanized)
        if si_text:
            print(f"?? You said (Sinhala): {si_text}")
            return si_text, True

        return "", False

    async def detect_wake_word(self):
        """Listen for hotwords without blocking the FastAPI server"""
        triggers = [
            "hey mirror", "hai mera", "hey me", "mera", "hi mirror",
            "a mirror", "8 mirror", "hey mira", "he mirror", "hey mirror",
            "mirror",  # broad fallback — catches most Google mis-transcriptions
        ]

        # Photo show triggers — exact phrases only
        photo_show_triggers = [
            "show my photos",
            "show photos",
        ]
        # Photo hide trigger — exact phrase only
        photo_hide_triggers = [
            "close photos",
        ]
        
        while not self.should_exit:
            try:
                print(f"[Bot] Opening mic (device_index={self.mic_device_index})...", flush=True)
                with sr.Microphone(device_index=self.mic_device_index) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    while not self.should_exit:
                        # Mic always listens — presence only gates which commands activate.
                        try:
                            print("🎤 Listening...", flush=True)
                            audio = await asyncio.to_thread(
                                self.recognizer.listen, source, timeout=3.0, phrase_time_limit=4.0
                            )
                        except sr.WaitTimeoutError:
                            continue  # Silence timeout — normal, just loop back
                        except Exception as e:
                            print(f"[Bot] ⚠️ Microphone read error: {e}. Re-opening device...", flush=True)
                            break

                        try:
                            is_sinhala_detected = False
                            try:
                                text = await asyncio.to_thread(self.recognizer.recognize_google, audio, language="en-US")
                                text = text.lower()
                            except sr.UnknownValueError:
                                text = await asyncio.to_thread(self.recognizer.recognize_google, audio, language="si-LK")
                                text = text.lower()
                                is_sinhala_detected = True

                            print(f"[Bot] Detected: '{text}'", flush=True)

                            from services import music_assistant
                            is_playing = music_assistant.is_music_playing()
                            is_paused = music_assistant.paused
                            is_mirror_wake_word = any(trig in text for trig in triggers)

                            # ── Photo commands (only when Mirror Man is NOT active) ──
                            if not self.is_active:
                                is_photo_show = any(trig in text for trig in photo_show_triggers)
                                is_photo_hide = any(trig in text for trig in photo_hide_triggers)
                                if is_photo_show:
                                    print("📸 Photo command: showing gallery", flush=True)
                                    await manager.broadcast(json.dumps({"type": "show_photos"}))
                                    continue
                                if is_photo_hide:
                                    print("📸 Photo command: hiding gallery", flush=True)
                                    await manager.broadcast(json.dumps({"type": "hide_photos"}))
                                    continue

                            # ── Mirror Man wake word — only activates when someone is present ──
                            if is_mirror_wake_word:
                                if not app_state.is_present:
                                    print("[Bot] Wake word heard but no one present — ignoring.", flush=True)
                                    continue
                                if is_playing and not is_paused:
                                    print("[Bot] Music is playing, ignoring wake word.", flush=True)
                                    continue
                                elif is_playing and is_paused:
                                    await asyncio.to_thread(self.speak, "Please stop the music to talk to me.")
                                    continue
                                else:
                                    print("✅ Wake word detected! Activating mirror...", flush=True)
                                    await manager.broadcast(json.dumps({"type": "mirror_show", "status": "active"}))
                                    self.is_active = True
                                    return

                            # ── Music commands — work regardless of presence ──
                            action, param, is_sinhala = music_assistant.parse_command(text, is_sinhala_detected)
                            if action != 'ignore':
                                print(f"[Bot] Music command: {action} ({param})", flush=True)
                                if action == 'play':
                                    await music_assistant.play_youtube_music(param, is_sinhala)
                                elif action == 'stop':
                                    await music_assistant.stop_music()
                                elif action == 'pause':
                                    await music_assistant.pause_music()
                                elif action == 'resume':
                                    await music_assistant.resume_music()
                                elif action == 'exit':
                                    await music_assistant.stop_music()

                        except sr.UnknownValueError:
                            pass  # No speech detected — normal
                        except sr.RequestError as e:
                            print(f"[Bot] ⚠️ Google Speech API error: {e}", flush=True)

            except Exception as e:
                print(f"[Bot] ⚠️ Mic open error: {e}. Reopening in 1s...", flush=True)
                await asyncio.sleep(1.0)

    async def run_session(self):
        """Continuous Conversation Session"""
        print("💬 Conversation Active. Say 'Goodbye' or 'Stop' to exit.", flush=True)
        consecutive_errors = 0
        shutdown_keywords = ["goodbye", "stop", "shut down", "exit", "bye", "ආයුබෝවන්"]

        while self.is_active:
            try:
                print(f"[Bot] Opening mic for session (device_index={self.mic_device_index})...", flush=True)
                with sr.Microphone(device_index=self.mic_device_index) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    while self.is_active:
                        print("\n👂 Listening...", flush=True)
                        # Show idle.mp4 while waiting for user speech
                        await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))

                        # Skip mic capture entirely while the mirror is speaking (prevents echo)
                        if self.is_speaking:
                            await asyncio.sleep(0.1)
                            continue

                        try:
                            audio_data = await asyncio.to_thread(
                                self.recognizer.listen, source, timeout=7.0, phrase_time_limit=15.0
                            )
                        except sr.WaitTimeoutError:
                            print("⏱ Listening timed out — looping back...", flush=True)
                            continue
                        except Exception as e:
                            print(f"[Bot] ⚠️ Microphone read error: {e}. Re-opening device...", flush=True)
                            break

                        try:
                            # Run English + Sinhala recognition in parallel for accurate detection
                            user_text, is_sinhala = await self._recognize_best(audio_data)

                            if not user_text or not user_text.strip():
                                print("?? No speech detected, ignoring...")
                                continue

                            if any(word in user_text.lower() for word in shutdown_keywords):
                                print("?? Shutdown command received.")
                                await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))
                                self.is_speaking = True
                                await asyncio.to_thread(self.speak, "Thank you, see you again!")
                                self.is_speaking = False
                                self.is_active = False
                                break

                            print("🤔 Mirror is thinking...")
                            await manager.broadcast(json.dumps({"type": "status", "state": "thinking"}))

                            # Build an explicit language instruction so Gemini never replies
                            # in the wrong language regardless of its general system prompt.
                            if is_sinhala:
                                lang_instruction = "IMPORTANT: The user spoke in Sinhala. You MUST reply ONLY in Sinhala script (සිංහල). Do NOT use English."
                            else:
                                lang_instruction = "IMPORTANT: The user spoke in English. You MUST reply ONLY in English. Do NOT use Sinhala."

                            # Build the user turn for this exchange
                            current_user_turn = types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_text(text=lang_instruction),
                                    types.Part.from_text(text=user_text)
                                ]
                            )

                            # Prepend the system prompt as a fixed first user turn, then
                            # append the rolling history + current message
                            system_turn = types.Content(
                                role="user",
                                parts=[types.Part.from_text(text=CUSTOM_PROMPT)]
                            )
                            # Cap history to the last MAX_HISTORY_TURNS exchanges
                            recent_history = self.conversation_history[-(self.MAX_HISTORY_TURNS * 2):]
                            contents = [system_turn] + recent_history + [current_user_turn]

                            response = await asyncio.to_thread(
                                get_gemini_client().models.generate_content,
                                model=GEMINI_MODEL,
                                contents=contents
                            )

                            if response.text:
                                print(f"🤖 Mirror: {response.text}")

                                # Save this exchange to conversation history
                                self.conversation_history.append(current_user_turn)
                                self.conversation_history.append(
                                    types.Content(
                                        role="model",
                                        parts=[types.Part.from_text(text=response.text)]
                                    )
                                )

                                await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))
                                self.is_speaking = True
                                await asyncio.to_thread(self.speak, response.text)
                                self.is_speaking = False
                                # Drain delay: give the speaker output time to fade before mic opens
                                await asyncio.sleep(1.0)
                                # After speaking, go back to idle (waiting for next input)
                                await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))
                                if "goodbye" in response.text.lower() or "bye" in response.text.lower():
                                    self.is_active = False
                                consecutive_errors = 0
                            else:
                                consecutive_errors += 1

                        except Exception as e:
                            print(f"? API Error: {e}")
                            consecutive_errors += 1

            except Exception as e:
                print(f"⚠️ Microphone open error: {e}", flush=True)
                consecutive_errors += 1
                if consecutive_errors >= 2:
                    self.is_active = False
                await asyncio.sleep(1.0)

            if consecutive_errors >= 2:
                self.is_active = False

    def speak(self, text):
        """High-quality TTS that dynamically selects voice based on language"""
        if any('\u0d80' <= c <= '\u0dff' for c in text):
            voice = "si-LK-ThiliniNeural"
        else:
            voice = "en-US-JennyNeural"
        speak_pygame(text, voice=voice)

    def _fallback_speak(self, text):
        from services.tts_service import fallback_speak
        fallback_speak(text)

    async def run(self):
        while not self.should_exit:
            if not app_state.is_present:
                await asyncio.sleep(1)
                continue
            await self.detect_wake_word()
            if self.is_active:
                # 1. Mirror man is visible (show_mirror already broadcast)
                #    Switch to talking video for greeting
                await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))

                # 2. Mirror speaks greeting (logic waits here until audio finishes)
                await asyncio.to_thread(self.speak, "Hello! How can I help you?")

                # 3. Back to idle before starting conversation
                await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))

                # 4. Conversation starts (history cleared for fresh session)
                self.conversation_history.clear()
                print(f"🧹 Conversation history cleared for new session.")
                await self.run_session()

                # 5. Session ended — hide mirror man, restore dashboard
                print("?? Returning to dashboard...")
                await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))
