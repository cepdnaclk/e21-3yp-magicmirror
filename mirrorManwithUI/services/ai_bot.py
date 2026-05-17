import asyncio
import speech_recognition as sr
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
        self.recognizer = sr.Recognizer()

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
                            await manager.broadcast("show_mirror")
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
            await manager.broadcast("idle")

            try:
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
                try:
                    user_text = await asyncio.to_thread(
                        self.recognizer.recognize_google, audio_data, language='si-LK'
                    )
                    print(f"?? You said: {user_text}")
                except sr.UnknownValueError:
                    user_text = ""
                except Exception as e:
                    user_text = ""

                if not user_text or not user_text.strip():
                    print("?? No speech detected, ignoring...")
                    continue

                if any(word in user_text.lower() for word in shutdown_keywords):
                    print("?? Shutdown command received.")
                    await manager.broadcast("talking")
                    await asyncio.to_thread(self.speak, "????????, ???? ??????.")
                    self.is_active = False
                    break

                print("🤔 Mirror is thinking...")
                await manager.broadcast("thinking")

                response = await asyncio.to_thread(
                    gemini_client.models.generate_content,
                    model=GEMINI_MODEL,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(text=CUSTOM_PROMPT),
                                types.Part.from_text(text=user_text)
                            ]
                        )
                    ]
                )

                if response.text:
                    print(f"🤖 Mirror: {response.text}")
                    await manager.broadcast("talking")
                    await asyncio.to_thread(self.speak, response.text)
                    # After speaking, go back to idle (waiting for next input)
                    await manager.broadcast("idle")
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
        """High-quality Sinhala TTS that preserves your logic flow"""
        speak_pygame(text, voice="si-LK-ThiliniNeural")

    def _fallback_speak(self, text):
        from services.tts_service import fallback_speak
        fallback_speak(text)

    async def run(self):
        while not self.should_exit:
            await self.detect_wake_word()
            if self.is_active:
                # 1. Mirror man is visible (show_mirror already broadcast)
                #    Switch to talking video for greeting
                await manager.broadcast("talking")

                # 2. Mirror speaks greeting (logic waits here until audio finishes)
                await asyncio.to_thread(self.speak, "????????! ?? ????? ????, ??? ???????")

                # 3. Back to idle before starting conversation
                await manager.broadcast("idle")

                # 4. Conversation starts
                await self.run_session()

                # 5. Session ended — hide mirror man, restore dashboard
                print("?? Returning to dashboard...")
                await manager.broadcast("hide_mirror")
