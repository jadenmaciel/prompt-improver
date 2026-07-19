# Prompt Improver

A macOS desktop app that transforms rough prompts into structured, high-quality prompts for LLMs — instantly, offline, no API key required.

![Prompt Improver screenshot](docs/screenshot.png)

## Features

- **General & Coding modes** — context-aware improvements tailored to your use case
- **Model selector** — defaults to Claude Sonnet 4.6; also supports Gemini and GPT
- **Audience targeting** — General, Business, Student, Expert, and more
- **Tone & format controls** — Direct, Friendly, Academic, or Creative; output as prose, bullets, JSON, table, steps, or code
- **One-click copy** — copy the improved prompt straight to your clipboard
- **Fully offline** — all logic runs locally, no internet or API keys needed

## Requirements

- macOS 10.15+
- Python 3.12 with Tkinter

```bash
brew install python-tk@3.12
```

## Installation

```bash
git clone https://github.com/jadenmaciel/prompt-improver.git
cd prompt-improver
python3.12 -m venv venv
source venv/bin/activate
python -m pip install customtkinter
```

The classic Tkinter app uses only the Python standard library. The modern desktop app needs `customtkinter`. The web UI needs `streamlit`, and the test suite needs `pytest`:

```bash
python -m pip install streamlit pytest
```

## Running

```bash
source venv/bin/activate
python3.12 modern_app.py
```

Or use the classic Tkinter version (stdlib only, no dependencies):

```bash
python3.12 app.py
```

## Desktop App (macOS)

To launch with a double-click from your Desktop, create a native `.app` bundle:

```bash
mkdir -p ~/Desktop/"Prompt Improver.app"/Contents/MacOS
cat > ~/Desktop/"Prompt Improver.app"/Contents/MacOS/PromptImprover << 'EOF'
#!/bin/bash
cd /path/to/prompt-improver
source venv/bin/activate
exec python3.12 modern_app.py
EOF
chmod +x ~/Desktop/"Prompt Improver.app"/Contents/MacOS/PromptImprover
```

Replace `/path/to/prompt-improver` with your actual clone path. On first launch, right-click → **Open** to bypass the Gatekeeper warning.

## Project Structure

```
app.py            # Core logic + classic Tkinter UI (stdlib only)
modern_app.py     # Modern CustomTkinter UI (recommended)
streamlit_app.py  # Streamlit web UI alternative
tests/            # Pytest suite covering PromptAnalyzer and PromptBuilder
docs/             # Specs and design notes
```

## Tests

```bash
source venv/bin/activate
python -m pytest
```

## License

[MIT](LICENSE)
