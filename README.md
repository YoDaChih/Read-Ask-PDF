# PDF Selection Q&A

A Streamlit PDF reader that lets you select text from rendered PDF pages and ask a local Ollama model questions about the selection.

## Features

- Displays a default PDF from a URL.
- Allows local PDF upload.
- Renders each PDF page visually while keeping a selectable text layer.
- Sends selected text to Ollama.
- Lets you add an optional follow-up question or instruction before sending the query.
- Editable Ollama model name, defaulting to `gpt-oss:20b`.
- Converts common raw LaTeX delimiters into readable Streamlit Markdown math.

## Requirements

- Python 3.10+
- Ollama running locally
- An Ollama model installed, for example:

```bash
ollama pull gpt-oss:20b
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The app opens with this default PDF:

```text
https://davidtong.org/pdfs/teaching/particle-physics/pp.pdf
```

You can still upload a local PDF from the UI.

## Usage

1. Highlight text on the displayed PDF page.
2. Optionally type an extra question or instruction in `Add to query`.
3. Press `Ask`.
4. The answer appears in the right panel.

Optional environment variables:

```bash
export OLLAMA_URL="http://127.0.0.1:11434/api/chat"
export OLLAMA_MODEL="gpt-oss:20b"
```

## Project Files

- `app.py`: main Streamlit app
- `bg1.PNG`: UI background image
- `html_selection_component/index.html`: local Streamlit component used to send selected text back to Python
- `requirements.txt`: Python dependencies
