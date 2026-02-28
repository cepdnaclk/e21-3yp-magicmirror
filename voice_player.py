import os
import random
import pygame
import speech_recognition as sr

# =======================
# MUSIC PLAYER
# =======================

class VoiceMusicPlayer:
    def __init__(self, music_folder="music"):
        pygame.mixer.init()
        self.music_folder = music_folder
        self.playlist = self.load_playlist()
        self.current_song = None
        self.is_paused = False

    def load_playlist(self):
        songs = []
        for file in os.listdir(self.music_folder):
            if file.endswith(".mp3") or file.endswith(".wav"):
                songs.append(file)
        return songs

    def play_music(self):
        if not self.playlist:
            print("No songs found.")
            return

        if pygame.mixer.music.get_busy() and not self.is_paused:
            print("Music already playing.")
            return

        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("Resumed music.")
            return

        self.current_song = random.choice(self.playlist)
        path = os.path.join(self.music_folder, self.current_song)

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        print(f"Playing: {self.current_song}")

    def pause_music(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_paused = True
            print("Music paused.")

    def stop_music(self):
        pygame.mixer.music.stop()
        self.is_paused = False
        print("Music stopped completely.")

# =======================
# VOICE CONTROL
# =======================

def listen_for_commands(player):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎤 Voice-controlled music player started.")
    print("Say: play music, pause, resume, stop, or exit")

    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Listening...")
                audio = recognizer.listen(source)

            command = recognizer.recognize_google(audio).lower()
            print("You said:", command)

            # COMMANDS
            if "play" in command:
                player.play_music()

            elif "pause" in command:
                player.pause_music()

            elif "resume" in command:
                player.play_music()

            elif "stop" in command:
                player.stop_music()

            elif "exit" in command or "quit" in command:
                player.stop_music()
                print("Exiting player.")
                break

        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")

        except sr.RequestError:
            print("Speech recognition service error.")

        except KeyboardInterrupt:
            break

# =======================
# MAIN
# =======================

if __name__ == "__main__":
    player = VoiceMusicPlayer("music")
    listen_for_commands(player)