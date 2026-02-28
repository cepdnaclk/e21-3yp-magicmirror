# 🎵 Voice-Controlled Music Player

A Python-based music player you can control entirely with your voice. Just say a command and the music responds — no keyboard required.

---

## Features

- 🎤 Voice command recognition via microphone
- 🎶 Plays MP3 and WAV files from a local folder
- ⏯️ Supports play, pause, resume, and stop commands
- 🔀 Randomly selects songs from your playlist
- 🛑 Clean exit via voice command or keyboard interrupt

---

## Requirements

- Python 3.7+
- A working microphone
- Internet connection (for Google Speech Recognition)

### Dependencies

Install required packages with:

```bash
pip install pygame SpeechRecognition pyaudio
```

> **Note for macOS/Linux users:** You may need to install `portaudio` before `pyaudio`:
> ```bash
> # macOS
> brew install portaudio
>
> # Ubuntu/Debian
> sudo apt-get install portaudio19-dev
> ```

---

## Setup

1. **Clone or download** this repository.

2. **Create a `music` folder** in the project root and add your `.mp3` or `.wav` files to it:

```
project/
├── main.py
├── README.md
└── music/
    ├── song1.mp3
    ├── song2.wav
    └── ...
```

3. **Run the player:**

```bash
python main.py
```

---

## Voice Commands

| Command         | Action                              |
|-----------------|-------------------------------------|
| `play`          | Plays a random song from the folder |
| `pause`         | Pauses the current song             |
| `resume`        | Resumes a paused song               |
| `stop`          | Stops music completely              |
| `exit` / `quit` | Stops music and closes the player   |

---

## Project Structure

```
project/
├── main.py       # Main application — music player + voice control loop
└── music/        # Folder containing your MP3/WAV music files
```

### Key Components

**`VoiceMusicPlayer`** — handles all music playback using `pygame.mixer`. Loads all `.mp3` and `.wav` files from the specified folder and supports play, pause, resume, and stop.

**`listen_for_commands()`** — runs a continuous listening loop using `SpeechRecognition`, processes spoken commands, and delegates actions to the player.

---

## Troubleshooting

**No audio output?** Ensure your system audio is not muted and `pygame` is properly installed.

**`pyaudio` install fails?** Install `portaudio` system dependency first (see Requirements above).

**"Speech recognition service error"?** This usually means no internet connection. The player uses Google's online speech recognition API.

**No songs found?** Make sure your `music/` folder exists and contains `.mp3` or `.wav` files.

---

## License

MIT — free to use and modify.
