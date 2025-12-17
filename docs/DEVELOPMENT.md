# Developer Guide (開発者向け情報)

## Architecture

Voice In combines a high-performance Rust audio core with a flexible Python UI.

- **rust_core**: A dedicated Rust module using `cpal` for low-latency audio capture and `hound` for WAV encoding. It handles device enumeration, sample rate detection, and Voice Activity Detection (VAD).
- **Python (src)**: Uses `PyQt6` for the GUI (Overlay, Settings, Tray). It consumes the `rust_core` via `maturin` bindings.
- **AI**: Integrates with Groq, Google Gemini, and `faster-whisper` for transcription and post-processing.

## Build Requirements

- **OS**: Linux (Ubuntu 22.04+ recommended), Windows 10/11, macOS
- **Python**: 3.12+
- **Rust**: Latest Stable
- **Tools**: `uv`, `maturin`, `pkg-config` (Linux), `libasound2-dev` (Linux)

## Setup for Development

```bash
# 1. Clone
git clone https://github.com/watawatan1984/voice-inn-linux.git
cd voice-inn-linux

# 2. Virtual Env & Tools
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv

# 3. Build Rust Extension & Install Deps
# This compiles rust_core and installs it into the venv
uv run maturin develop

# 4. Sync Python Deps
uv pip sync pyproject.toml
```

## Running from Source

```bash
uv run src/main.py
```

## Testing

```bash
# Verify Rust features
uv run verify_rust_features.py
```

## Release Logic (CI)

GitHub Actions workflow `.github/workflows/ci.yml` builds wheels for Linux, Windows, and macOS automatically on push to `main` or tags.

---
[Back to Main README](../README.md)
