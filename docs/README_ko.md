# Voice In (보이스 인)

**당신의 목소리를, 모든 곳에.**

Voice In은 PC의 모든 애플리케이션에서 사용할 수 있는 차세대 AI 음성 입력 도구입니다.
키를 누른 채 말하기만 하면 됩니다. 최신 AI가 문맥을 이해하고, 구두점을 추가하며, 문법을 수정하여 완벽한 문장을 입력해 줍니다.

[日本語](../README.md) | [English](README_en.md) | [中文](README_zh.md) | [Français](README_fr.md)

---

## ✨ 왜 Voice In 인가요?

- **어디서나 입력**: 메모장, 브라우저, Slack, 코드 에디터 등 활성 창이라면 어디서든 입력 가능합니다.
- **단순한 받아쓰기가 아닙니다**: "음", "저" 같은 불필요한 단어를 제거하고, 문맥에 맞춰 문체를 자동으로 정리합니다.
- **AI 선택 가능**: 초고속 클라우드 AI(Groq, Google Gemini) 또는 개인정보 보호를 위한 로컬 처리(Local Whisper) 중 선택할 수 있습니다.
- **크로스 플랫폼**: Linux를 중심으로 Windows, macOS에서도 동작합니다.

## 🚀 시작하기

### 1. 다운로드
오른쪽 [Releases](https://github.com/watawatan1984/voice-inn-linux/releases) 페이지에서 사용 중인 OS에 맞는 최신 파일을 다운로드하세요.

### 2. 설치 및 실행
다운로드한 파일을 실행하세요.

> **참고**: Linux 환경에서는 파일에 실행 권한을 부여해야 할 수 있습니다.

### 3. 설정 (Setup Wizard)
처음 실행 시 설정 마법사가 열립니다.
1. **AI 제공자**: 빠른 `Groq`, 정확한 `Gemini`, 또는 오프라인 `Local` 중 선택하세요.
2. **API 키**: 클라우드 AI를 사용하는 경우, 무료 API 키를 발급받아 입력하세요.
3. **마이크 선택**: 사용할 마이크를 선택하고 테스트하세요.

## 🎙️ 사용법

사용법은 매우 간단합니다.

1. 글을 입력하고 싶은 곳(텍스트 박스 등)을 클릭합니다.
2. **`Left Alt` 키(또는 설정한 키)를 누른 채로** 말을 시작하세요.
3. 화면에 마이크 아이콘이 나타납니다.
4. 말을 마치면 키를 놓으세요.
5. AI가 문장을 정리하여 자동으로 입력합니다 ✨

---

## ⚙️ 상세 설정

트레이 아이콘을 우클릭하여 `Settings`를 열면 더 많은 설정이 가능합니다.

**Language (언어)**: 앱 언어 변경.

### 1. General (일반 설정)
기본 동작 환경 설정.
- **AI Provider**: `Groq` (초고속), `Gemini` (고정확도), `Local` (로컬 처리/오프라인).
- **Gemini Model / Groq API Key**: 키/모델 입력.
- **Input Device**: 마이크 선택.
- **Input Gain**: 입력 게인 (dB).
- **Hold Key**: 녹음 키 (기본: `Left Alt`).
- **Max Recording**: 최대 녹음 시간.
- **Min Valid Duration**: 최소 유효 시간.
- **Auto Paste**: 자동 붙여넣기 (ON/OFF).
- **Paste Delay**: 붙여넣기 지연 (ms).

### 2. Prompts (프롬프트)
AI 지시 사항 사용자 정의.
- **Groq Whisper Prompt**: 인식 힌트 (예: "의학 용어").
- **Refine System Prompt**: 텍스트 후처리 규칙 (예: "영어로 번역해").

### 3. Dictionary (사전)
- **From**: 오인식된 단어.
- **To**: 올바른 단어.

### 4. Local Whisper
- **Model Size**: 모델 크기 (`large-v3` 등).
- **Device**: `cuda` (GPU) 또는 `cpu`.
- **Compute Type**: 계산 정밀도 (`float16`, `int8`).

---

## 🛠️ 개발자용 (Technical Details)

기술적인 내용이나 소스 코드 빌드 방법은 [DEVELOPMENT.md](DEVELOPMENT.md)를 참조하세요.

Voice In은 Rust(오디오 코어)와 Python(UI/AI 통합)으로 구축된 오픈 소스 프로젝트입니다.

---
**License**: MIT
