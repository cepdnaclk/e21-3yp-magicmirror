# 🤖 MirrorMan Persona

An AI-powered voice assistant with an animated face that responds in the same language you speak. Built with Google Gemini's Live Audio API, it displays an idle/talking video loop synced to the AI's speech output.

---

## Features

- 🎙️ Real-time microphone input with live audio streaming to Gemini
- 🔊 AI-generated voice responses played through your speakers
- 🎬 Animated face — switches between an idle and talking video loop based on AI speech state
- 🌍 Multilingual — automatically responds in the user's language
- ⚡ Async architecture for low-latency audio I/O

---

## Requirements

- Python 3.9+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- Two video files: `idle.mp4` and `talking.mp4` (looping face animations)

### Python Dependencies

Install all dependencies with:

```bash
pip install google-genai pyaudio opencv-python pygame numpy python-dotenv
```

> **Windows users:** You may need to install PyAudio via a pre-built wheel. Download from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) or use `pipwin install pyaudio`.

---

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/polyglotbot.git
   cd polyglotbot
   ```

2. **Create a `.env` file** in the project root:

   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Add your video files** to the project root:
   - `idle.mp4` — a looping animation for when the AI is listening
   - `talking.mp4` — a looping animation for when the AI is speaking

4. **Run the bot:**

   ```bash
   python main.py
   ```

---

## How It Works

| Component | Description |
|---|---|
| `VideoPlayer` | Runs in a separate thread, renders idle/talking video using Pygame + OpenCV |
| `SinhalaBot` | Manages async audio I/O and the Gemini Live session |
| `listen_mic` | Captures microphone audio, downsamples from 44100 Hz → ~14700 Hz, streams to Gemini |
| `play_speaker` | Plays back AI audio at 24000 Hz; updates video state to talking/idle |
| `send_loop` | Sends queued audio chunks to the Gemini session |
| `receive_loop` | Receives audio response data from Gemini and queues it for playback |

---

## Configuration

You can customize behavior by editing these constants at the top of `main.py`:

| Constant | Default | Description |
|---|---|---|
| `MODEL` | `gemini-2.5-flash-native-audio-preview-12-2025` | Gemini model to use |
| `CUSTOM_PROMPT` | `"Your name is PolyglotBot..."` | System prompt sent at session start |
| `HARDWARE_IN_RATE` | `44100` | Microphone sample rate |
| `HARDWARE_OUT_RATE` | `24000` | Speaker output sample rate |
| `CHUNK` | `1024` | Audio buffer chunk size |

---

## Troubleshooting

**No audio input/output:** Make sure your default system microphone and speakers are configured correctly. PyAudio uses system defaults.

**PyAudio install fails on Windows:** Use `pipwin` or download a pre-built `.whl` from the link above.

**Video not displaying correctly:** Ensure `idle.mp4` and `talking.mp4` are in the same directory as `main.py` and are valid video files.

**API errors:** Double-check your `GEMINI_API_KEY` in the `.env` file and ensure the model name is still valid in the [Google AI documentation](https://ai.google.dev/docs).

---

## License

MIT License — feel free to use and modify.
