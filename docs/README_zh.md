# Voice In (语音输入)

**您的声音，无处不在。**

Voice In 是一款适用于 PC 上所有应用程序的新一代 AI 语音输入工具。
只需按住按键并说话。先进的 AI 能够理解您的语境，自动添加标点符号，修正语法，并即时输入完美的文本。

[日本語](../README.md) | [English](README_en.md) | [한국어](README_ko.md) | [Français](README_fr.md)

---

## ✨ 为什么选择 Voice In？

- **随处输入**: 记事本、浏览器、Slack、代码编辑器……可在任何活动窗口中输入。
- **不仅仅是听写**: 自动去除“那个”、“嗯”等语气词，根据上下文自动调整格式和语气。
- **AI 引擎可选**: 可选择超高速云端 AI (Groq, Google Gemini) 或注重隐私的本地处理 (Local Whisper)。
- **跨平台**: 以 Linux 为主，同时也支持 Windows 和 macOS。

## 🚀以此开始

### 1. 下载
从右侧的 [Releases](https://github.com/watawatan1984/voice-inn-linux/releases) 页面下载适合您操作系统的最新文件。

### 2. 安装与运行
运行下载的文件。

> **注意**: 在 Linux 环境下，请确保文件具有执行权限。

### 3. 设置向导 (Setup Wizard)
首次运行时会打开设置向导：
1. **选择 AI 提供商**: 选择快速的 `Groq`、精准的 `Gemini` 或离线的 `Local`。
2. **API 密钥**: 如果使用云端 AI，请输入获取的免费 API 密钥。
3. **麦克风**: 选择并测试您的输入设备。

## 🎙️ 使用方法

使用非常简单。

1. 点击您想要输入文本的地方（如文本框）。
2. **按住 `Left Alt` 键（或配置的热键）**。
3. 对着麦克风说话。屏幕上会出现麦克风图标。
4. 说完后松开按键。
5. AI 会处理您的语音并自动输入文本 ✨

---

## ⚙️ 高级设置

右键单击托盘图标并选择 `Settings` 以获取更多选项：

**Language (界面语言)**: 切换应用程序语言。

### 1. General (常规设置)
基本运行环境设置。
- **AI Provider**: `Groq` (超快), `Gemini` (高精度), `Local` (本地隐私/离线)。
- **Gemini Model / Groq API Key**: 输入密钥/模型。
- **Input Device**: 选择麦克风。
- **Input Gain**: 麦克风增益 (dB)。
- **Hold Key**: 录音按键 (默认: `Left Alt`)。
- **Max Recording**: 最大录音时长（秒）。
- **Min Valid Duration**: 最短有效录音时长。
- **Auto Paste**: 自动粘贴 (ON/OFF)。
- **Paste Delay**: 粘贴延迟 (ms)。

### 2. Prompts (提示词)
自定义 AI 指令。
- **Groq Whisper Prompt**: 语音识别提示（例如：“医学术语”）。
- **Refine System Prompt**: 文本润色规则（例如：“翻译成英文”）。

### 3. Dictionary (词典)
- **From**: 错误识别的词。
- **To**: 正确的词。

### 4. Local Whisper
- **Model Size**: 模型大小 (`large-v3`, `base` 等)。
- **Device**: `cuda` (GPU) 或 `cpu`。
- **Compute Type**: 计算精度 (`float16`, `int8`)。

---

## 🛠️ 开发者信息

有关技术细节和构建说明，请参阅 [DEVELOPMENT.md](DEVELOPMENT.md)。

Voice In 基于 Rust (音频核心) 和 Python (UI/AI 集成) 构建，并作为开源项目发布。

---
**License**: MIT
