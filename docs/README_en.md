# Voice In

**Your Voice, Everywhere.**

Voice In is a next-generation AI-powered voice dictation tool that works in any application on your PC.
Just hold the key and speak. Advanced AI understands your context, adds punctuation, fixes grammar, and types out perfect text instantly.

[日本語](../README.md) | [한국어](README_ko.md) | [中文](README_zh.md) | [Français](README_fr.md)

---

## ✨ Why Voice In?

- **Type Anywhere**: Notepad, Browser, Slack, Coding Editors... works in any active window.
- **More Than Just Dictation**: Removes filler words (like "um", "ah"), automatically formats text, and matches your tone.
- **Choose Your AI**: Ultra-fast cloud AI (Groq, Google Gemini) or privacy-focused local processing (Local Whisper).
- **Cross-Platform**: Primarily for Linux, with experimental support for Windows and macOS.

## 🚀 Getting Started

### 1. Download
Download the latest release for your OS from the [Releases](https://github.com/watawatan1984/voice-inn-linux/releases) page.

### 2. Install & Run
Run the downloaded executable.

> **Note**: On Linux, ensure the file has execution permissions.

### 3. Setup Wizard
The Setup Wizard will guide you on the first run:
1. **Select AI Provider**: Choose fast `Groq`, accurate `Gemini`, or offline `Local`.
2. **API Key**: Enter your free API key if using cloud providers.
3. **Microphone**: Select and test your input device.

## 🎙️ How to Use

It's extremely simple.

1. Click on the text field where you want to type.
2. **Hold down the `Left Alt` key** (or your configured hotkey).
3. Speak into your microphone. A microphone icon will appear.
4. Release the key when finished.
5. AI processes your speech and types it out automatically ✨

---

## ⚙️ Customization

Right-click the tray icon and select `Settings` for more options:

### 1. General

Basic configuration for the application environment.

- **AI Provider**:
  - `Groq`: Ultra-fast. Requires internet connection.
  - `Gemini`: High accuracy, better for long context. Requires internet.
  - `Local`: Process entirely on your PC. Privacy-focused & offline capable. (Downloads model on first use)
- **Gemini Model / Groq API Key**: Enter the key/model for your selected provider.
- **Input Device**: Select the microphone to use.
- **Input Gain**: Boost microphone volume (dB). Increase if your voice is too quiet.
- **Hold Key**: Change the key used for recording (Default: `Left Alt`).
- **Max Recording**: Maximum duration (seconds) per input. Automatically transcribes if exceeded.
- **Min Valid Duration**: Shorter sounds will be ignored to prevent accidental triggers.
- **Auto Paste**: If ON, automatically types the result. If OFF, only copies to clipboard.
- **Paste Delay**: Wait time (ms) before typing. Increase if the app types before focus is switched.
- **Language**: Switch the application language.

### 2. Prompts

Customize AI instructions to change transcription style.

- **Groq Whisper Prompt**: Provide context hints for valid speech recognition (e.g., "Medical transcription").
- **Refine System Prompt**: Rules for post-processing text. Instructions like "Translate to English" or "Summarize" go here.

### 3. Dictionary

Register frequently used words or fix common AI misinterpretations.

- **From**: The wrong word AI produces (e.g., "VoiceInn").
- **To**: The correct word (e.g., "Voice In").
- The app will strictly replace text based on these rules.

### 4. Local Whisper

Advanced settings when `Local` provider is selected.

- **Model Size**: Larger models (`large-v3`) are more accurate but slower and use more memory. `base` or `small` are faster.
- **Device**: Select `cuda` (NVIDIA GPU) or `cpu`.
- **Compute Type**: Precision level. `float16` is standard; try `int8` if you have limited memory.

---

## 🛠️ For Developers

For technical details and build instructions, please see [DEVELOPMENT.md](DEVELOPMENT.md).

Voice In is built with Rust (Audio Core) and Python (UI/AI Integration) and is open source.

---
**License**: MIT
