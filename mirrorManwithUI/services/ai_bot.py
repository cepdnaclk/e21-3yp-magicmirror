import asyncio
import speech_recognition as sr
import json
from google import genai
from google.genai import types

from config.settings import CUSTOM_PROMPT, GEMINI_MODEL, GEMINI_PROJECT_ID
from controllers.websocket_manager import manager
from services.tts_service import speak_pygame


# ================= GEMINI CLIENT =================
gemini_client = genai.Client(
    vertexai=True,
    project=GEMINI_PROJECT_ID,
    location="global"
)


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
        triggers = ["hey mirror", "mirror", "hai mera", "hey me", "mera"]
        while not self.should_exit:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("?? Listening for 'Hey mirror' or music commands...")
                    # FIXED: Added to_thread so it doesn't block the AWS S3 watcher!
                    audio = await asyncio.to_thread(
                        self.recognizer.listen, source, timeout=2.0, phrase_time_limit=3.0
                    )
                try:
                    is_sinhala_detected = False
                    try:
                        text = await asyncio.to_thread(self.recognizer.recognize_google, audio, language="en-US")
                        text = text.lower()
                    except sr.UnknownValueError:
                        text = await asyncio.to_thread(self.recognizer.recognize_google, audio, language="si-LK")
                        text = text.lower()
                        is_sinhala_detected = True
                        
                    print(f"?? Detected: {text}")
                    
                    from services import music_assistant
                    is_playing = music_assistant.is_music_playing()
                    is_paused = music_assistant.paused
                    is_mirror_wake_word = any(trig in text for trig in triggers)

                    if is_mirror_wake_word:
                        if is_playing and not is_paused:
                            print("?? Music is playing, ignoring Mirror Man wake word.")
                            continue
                        elif is_playing and is_paused:
                            print("?? Music is paused. Asking user to stop music first.")
                            await asyncio.to_thread(self.speak, "Please stop the music to get back to Mirror Man.")
                            continue
                        else:
                            print(f"? Wake word detected! Activating mirror...")
                            # Show mirror man (hide dashboard, show idle.mp4)
                            await manager.broadcast(json.dumps({"type": "mirror_show", "status": "active"}))
                            self.is_active = True
                            return
                            
                    # If not a mirror wake word, check for music command
                    action, param, is_sinhala = music_assistant.parse_command(text, is_sinhala_detected)
                    if action != 'ignore':
                        print(f"?? Music Command Detected: {action} ({param})")
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
                    pass
            except Exception:
                await asyncio.sleep(0.1)

    async def run_session(self):
        """Continuous Conversation Session"""
        print("?? Conversation Active. Say 'Goodbye' or 'Stop' to exit.")
        consecutive_errors = 0
        shutdown_keywords = ["goodbye", "stop", "shut down", "exit", "bye", "?????????"]

        while self.is_active:
            print("\n?? Listening...")
            # Show idle.mp4 while waiting for user speech
            await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))

            try:
                # Skip mic capture entirely while the mirror is speaking (prevents echo)
                if self.is_speaking:
                    await asyncio.sleep(0.1)
                    continue

                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio_data = await asyncio.to_thread(
                        self.recognizer.listen, source, timeout=7.0, phrase_time_limit=15.0
                    )
            except sr.WaitTimeoutError:
                print("? Listening timed out. Restarting loop...")
                continue
            except Exception as e:
                print(f"? Microphone error: {e}")
                consecutive_errors += 1
                if consecutive_errors >= 2:
                    self.is_active = False
                continue

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
                    await asyncio.to_thread(self.speak, "ස්තූතියි, නැවත හමුවෙමු.")
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
                    gemini_client.models.generate_content,
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
            await self.detect_wake_word()
            if self.is_active:
                # 1. Mirror man is visible (show_mirror already broadcast)
                #    Switch to talking video for greeting
                await manager.broadcast(json.dumps({"type": "video", "state": "talking"}))

                # 2. Mirror speaks greeting (logic waits here until audio finishes)
                await asyncio.to_thread(self.speak, "ආයුබෝවන්! මම කෙසේද උදව් කරන්නේ?")

                # 3. Back to idle before starting conversation
                await manager.broadcast(json.dumps({"type": "video", "state": "idle"}))

                # 4. Conversation starts (history cleared for fresh session)
                self.conversation_history.clear()
                print(f"🧹 Conversation history cleared for new session.")
                await self.run_session()

                # 5. Session ended — hide mirror man, restore dashboard
                print("?? Returning to dashboard...")
                await manager.broadcast(json.dumps({"type": "mirror_hide", "status": "sleep"}))
