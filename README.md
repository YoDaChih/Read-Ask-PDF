# PDF Selection Q&A

A local Streamlit PDF reader that lets you select text from rendered PDF pages, ask Codex questions about the selection, and generate a multiple-choice quiz from the selected topic.

> **Local app notice:** this project is designed to run on your own machine with the Codex CLI installed and signed in. It is not a turnkey hosted web app unless the deployment environment can securely provide a working Codex CLI session.

> **Privacy notice:** selected PDF text and cropped figure images are sent to the configured Codex assistant for answers and quiz generation. Do not use sensitive, confidential, or private PDFs unless you are comfortable sending the selected content to that service.

## Features

- Displays a default PDF from a URL.
- Allows local PDF upload.
- Renders each PDF page visually while keeping a selectable text layer.
- Sends selected text to Codex.
- Lets you Shift+drag a box around a figure, diagram, chart, or equation to crop that region and send the image to Codex.
- Falls back to OCR (Tesseract) on the cropped region if Codex cannot accept images, so figure-picking still works.
- Lets you add an optional follow-up question or instruction before sending the query.
- Generates one interactive quiz question with four options after Q&A.
- Randomizes the displayed answer order for each generated quiz.
- Lets the user pick an answer, submit it, and see pass/fail plus the correct answer.
- Uses the configured Codex model from `app.py`.
- Converts common raw LaTeX delimiters into readable Streamlit Markdown math.
- Limits PDF size, page count, and rendered page dimensions to reduce accidental memory/CPU overload.

## Requirements

- Python 3.10+
- Codex CLI installed and signed in with ChatGPT
- (Optional) Tesseract OCR binary, for the figure OCR fallback:
  - macOS: `brew install tesseract`
  - Debian/Ubuntu: `sudo apt-get install tesseract-ocr`

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

Or use the included launcher, which checks that Streamlit and Codex are available:

```bash
./run_with_codex.sh
```

The app opens with this default PDF:

```text
https://davidtong.org/pdfs/teaching/particle-physics/pp.pdf
```

You can still upload a local PDF from the UI.

## Safety Limits

The app applies conservative local rendering limits:

- Maximum PDF size: 25 MB
- Maximum page count: 80 pages
- Very large rendered pages are rejected before image conversion

These limits are intended to keep public/shared demos from accidentally exhausting memory while rendering every page.

## Usage

1. Highlight text on the displayed PDF page, **or** hold `Shift` and drag a box around a figure to pick it as an image.
2. Optionally type an extra question or instruction in `Add to query`.
3. Press `Ask`.
4. The answer appears in the right panel.
5. Press `Create Quiz` to generate one multiple-choice quiz question for the selected topic.
6. Pick one answer and press `Submit Answer`.
7. The app shows pass/fail and reveals the correct answer.

## Project Files

- `app.py`: main Streamlit app
- `bg1.PNG`: UI background image
- `html_selection_component/index.html`: local Streamlit component used to send selected text back to Python
- `requirements.txt`: Python dependencies
