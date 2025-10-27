# Desktop AI Assistant

A privacy-first desktop automation assistant that learns from your actions and suggests automations using local AI.

## 🎯 Features

- **Screen Recording**: Captures periodic screenshots of your desktop activity
- **Event Tracking**: Monitors mouse clicks, keyboard input, and window switches
- **OCR Integration**: Extracts text from clicked elements using Tesseract OCR
- **Audio Transcription**: Records and transcribes audio using Whisper
- **Pattern Detection**: Identifies repetitive workflows using rule-based analysis
- **AI-Powered Suggestions**: Uses local LLM (Ollama) to suggest automation opportunities
- **Privacy-First**: Everything runs locally - no cloud dependencies

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Tesseract OCR installed
- Ollama installed and running

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd desktop_assistant
```

2. Install dependencies:
```bash
uv sync
```

3. Pull Ollama model:
```bash
ollama pull tinyllama
```

4. Run the application:
```bash
uv run python src/gui/main_window.py
```

## 📖 Usage

1. **Set Recording Duration**: Enter the duration in seconds (default: 60)
2. **Click "Start Recording"**: The app will capture your desktop activity
3. **Interact Normally**: Click, type, and use keyboard shortcuts as you normally would
4. **Stop Recording**: Click "Stop Recording" when done
5. **View Suggestions**: The app will analyze your activity and display automation suggestions

## 🏗️ Architecture

- `src/recorder/`: Screen, audio, and event recorders
- `src/analyzer/`: Activity analysis and pattern detection
- `src/llm/`: Local LLM integration (Ollama)
- `src/gui/`: CustomTkinter-based user interface

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **GUI**: CustomTkinter
- **OCR**: Tesseract (Optical Character Recognition)
- **Audio Transcription**: faster-whisper
- **LLM**: Ollama (local)
- **Screenshots**: mss
- **Event Tracking**: pynput

## 🎬 Demo

[Link to demo video]

## 📝 Project Information

Built for Hackathon: “The AGI Assistant”, October 2025