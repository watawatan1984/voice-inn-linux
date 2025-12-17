# Voice In

**Your Voice, Everywhere.**

Voice In is a next-generation AI-powered voice dictation tool that works in any application on your PC.
Just hold the key and speak. Advanced AI understands your context, adds punctuation, fixes grammar, and types out perfect text instantly.

[日本語](../README.md) | [한국어](README_kr.md) | [中文](README_zh.md) | [Français](README_fr.md)

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

- **VAD Settings**: Adjust sensitivity for detecting speech.
- **Prompt Engineering**: Instruct the AI to "translate to Spanish" or "summarize as bullet points".
- **Dictionary**: Add custom words or technical terms for better recognition.

---

## 🛠️ For Developers

For technical details and build instructions, please see [DEVELOPMENT.md](DEVELOPMENT.md).

Voice In is built with Rust (Audio Core) and Python (UI/AI Integration) and is open source.

---
**License**: MIT
