import base64
import os
import re
from html import escape
from pathlib import Path

import fitz
import requests
import streamlit as st
import streamlit.components.v1 as components


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
DEFAULT_PDF_URL = "https://davidtong.org/pdfs/teaching/particle-physics/pp.pdf"
APP_DIR = Path(__file__).resolve().parent
HEADER_IMAGE = APP_DIR / "top.png"
BACKGROUND_IMAGE = APP_DIR / "bg1.PNG"
COMPONENT_DIR = APP_DIR / "html_selection_component"
selection_component = components.declare_component(
    "pdf_selection_reader",
    path=str(COMPONENT_DIR),
)


def ask_ollama(selected_text: str, additional_query: str, model: str) -> str:
    user_content = f"Selected text:\n\n{selected_text}"
    if additional_query.strip():
        user_content += f"\n\nAdditional user request:\n\n{additional_query.strip()}"

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You answer questions about selected text from a PDF document. "
                    "Explain clearly and concisely. If the selected text is incomplete, "
                    "say what context is missing. Format equations with Markdown math "
                    "delimiters: use $...$ for inline equations and $$...$$ for display equations."
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


def normalize_latex_for_markdown(answer: str) -> str:
    answer = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", answer, flags=re.DOTALL)
    answer = re.sub(r"\\\((.*?)\\\)", r"$\1$", answer, flags=re.DOTALL)

    block_envs = "equation|equation\\*|align|align\\*|gather|gather\\*|multline|multline\\*"
    answer = re.sub(
        rf"(?<!\$)(\\begin\{{(?:{block_envs})\}}.*?\\end\{{(?:{block_envs})\}})(?!\$)",
        r"$$\1$$",
        answer,
        flags=re.DOTALL,
    )

    return answer


@st.cache_data(show_spinner="Downloading default PDF...")
def download_pdf(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def read_pdf_bytes(uploaded_file) -> tuple[str, bytes]:
    if uploaded_file is not None:
        return uploaded_file.name, uploaded_file.read()

    return DEFAULT_PDF_URL, download_pdf(DEFAULT_PDF_URL)


@st.cache_data(show_spinner="Rendering PDF...")
def render_pdf_pages(pdf_bytes: bytes) -> list[dict]:
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in document:
        rect = page.rect
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = base64.b64encode(pixmap.tobytes("png")).decode("ascii")
        words = []

        for x0, y0, x1, y1, word, *_ in page.get_text("words"):
            words.append(
                {
                    "text": word,
                    "left": x0 / rect.width * 100,
                    "top": y0 / rect.height * 100,
                    "width": (x1 - x0) / rect.width * 100,
                    "height": (y1 - y0) / rect.height * 100,
                }
            )

        pages.append(
            {
                "number": page.number + 1,
                "width": rect.width,
                "height": rect.height,
                "image": image,
                "words": words,
            }
        )
    document.close()

    return pages


def pages_to_selectable_html(file_name: str, pages: list[dict], width_px: int) -> str:
    page_blocks = []
    for page in pages:
        word_spans = []
        for word in page["words"]:
            font_size = max(word["height"] * 0.82, 0.8)
            word_spans.append(
                f"""
                <span
                  class="word"
                  style="
                    left:{word["left"]:.4f}%;
                    top:{word["top"]:.4f}%;
                    width:{word["width"]:.4f}%;
                    height:{word["height"]:.4f}%;
                    font-size:{font_size:.4f}cqh;
                  "
                >{escape(word["text"])} </span>
                """
            )

        empty_text = ""
        if not word_spans:
            empty_text = '<div class="no-text">No selectable text found on this page.</div>'

        page_blocks.append(
            f"""
            <section
              class="page"
              style="aspect-ratio:{page["width"]:.4f}/{page["height"]:.4f};"
            >
              <img
                class="page-image"
                src="data:image/png;base64,{page["image"]}"
                alt="Page {page["number"]}"
              />
              <div class="text-layer" aria-label="Selectable text for page {page["number"]}">
                {"".join(word_spans)}
                {empty_text}
              </div>
            </section>
            """
        )

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{
            margin: 0;
            padding: 20px 18px 24px 16px;
            background: #e5e7eb;
            color: #111827;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }}

          .document-shell {{
            width: min(100%, {width_px}px);
            box-sizing: border-box;
          }}

          .document-title {{
            margin: 0 0 16px;
            font-size: 14px;
            color: #4b5563;
          }}

          .page {{
            position: relative;
            container-type: size;
            width: 100%;
            margin: 0 0 24px;
            background: white;
            border: 1px solid #d1d5db;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            box-sizing: border-box;
            overflow: hidden;
          }}

          .page-image {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: fill;
            user-select: none;
            pointer-events: none;
          }}

          .text-layer {{
            position: absolute;
            inset: 0;
            z-index: 2;
            color: transparent;
            user-select: text;
            -webkit-user-select: text;
          }}

          .word {{
            position: absolute;
            display: block;
            white-space: pre;
            line-height: 1;
            font-family: Arial, sans-serif;
            color: transparent;
            user-select: text;
            -webkit-user-select: text;
          }}

          .word::selection {{
            color: transparent;
            background: rgba(37, 99, 235, 0.28);
          }}

          .no-text {{
            position: absolute;
            inset: 48px;
            color: #6b7280;
            font-size: 14px;
          }}
        </style>
      </head>
      <body>
        <div class="document-shell">
          <div class="document-title">{escape(file_name)}</div>
          {"".join(page_blocks)}
        </div>
      </body>
    </html>
    """


def selection_reader(rendered_html: str, height: int = 760) -> str:
    return selection_component(
        rendered_html=rendered_html,
        height=height,
        default="",
    )


def main() -> None:
    st.set_page_config(page_title="PDF Selection Q&A", layout="wide")
    if BACKGROUND_IMAGE.exists():
        background_image = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode("ascii")
        st.markdown(
            f"""
            <style>
              .stApp {{
                background-image:
                  linear-gradient(rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.82)),
                  url("data:image/png;base64,{background_image}");
                background-repeat: repeat;
                background-size: 420px auto;
                background-attachment: fixed;
              }}

              [data-testid="stAppViewContainer"],
              [data-testid="stHeader"] {{
                background: transparent;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <style>
          [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] {
            gap: 0.55rem;
          }

          h1 {
            font-size: 3.1rem !important;
            line-height: 1.15 !important;
            margin: 0.2rem 0 0.65rem !important;
            overflow: visible !important;
          }

          h2, h3 {
            font-size: 1rem !important;
            margin-bottom: 0.35rem !important;
          }

          .stTextArea label,
          .stTextArea textarea,
          .stMarkdown,
          .stCaptionContainer,
          .stAlert {
            font-size: 0.86rem !important;
          }

          .block-container {
            max-width: none !important;
            padding: 0.55rem 0.9rem 1rem 0.9rem !important;
          }

          [data-testid="column"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
          }

          [data-testid="column"]:nth-of-type(2) {
            padding-left: 0.9rem !important;
          }

          .top-banner {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin: 0.2rem 0 0.25rem;
          }

          .top-banner img {
            width: 600px;
            max-width: 52vw;
            height: auto;
            display: block;
          }

        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("PDF Selection Q&A")

    if HEADER_IMAGE.exists():
        header_image = base64.b64encode(HEADER_IMAGE.read_bytes()).decode("ascii")
        st.markdown(
            f"""
            <div class="top-banner">
              <img src="data:image/png;base64,{header_image}" alt="Reader header" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    controls_left, controls_middle, controls_right = st.columns([0.46, 0.24, 0.30], gap="small")
    with controls_left:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        st.caption(f"Default URL: {DEFAULT_PDF_URL}")
    with controls_middle:
        pdf_width = st.slider("PDF width", 720, 1225, 1040, 25)
    with controls_right:
        ollama_model = st.text_input("Ollama model", value=OLLAMA_MODEL)
        st.caption("Make sure Ollama is running locally before selecting text.")

    try:
        file_name, pdf_bytes = read_pdf_bytes(uploaded_file)
    except requests.RequestException as exc:
        st.error(f"Could not load the default PDF from {DEFAULT_PDF_URL}.\n\n{exc}")
        return

    if not pdf_bytes:
        st.info("Upload a PDF file to begin.")
        return

    if "last_selected_text" not in st.session_state:
        st.session_state.last_selected_text = ""
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = ""
    if "last_error" not in st.session_state:
        st.session_state.last_error = ""
    if "last_model" not in st.session_state:
        st.session_state.last_model = ""
    if "additional_query" not in st.session_state:
        st.session_state.additional_query = ""

    try:
        pages = render_pdf_pages(pdf_bytes)
    except Exception as exc:
        st.error(f"Could not read this PDF: {exc}")
        return

    rendered_html = pages_to_selectable_html(file_name, pages, pdf_width)
    left, right = st.columns([0.68, 0.32], gap="small")

    with left:
        st.caption(f"Opened: {file_name}")
        selected_text = selection_reader(rendered_html)

    with right:
        st.subheader("Selected Text")

        active_model = ollama_model.strip() or OLLAMA_MODEL

        if selected_text and selected_text != st.session_state.last_selected_text:
            st.session_state.last_selected_text = selected_text
            st.session_state.last_answer = ""
            st.session_state.last_error = ""
            st.session_state.additional_query = ""

        if st.session_state.last_selected_text:
            st.text_area(
                "Current selection",
                st.session_state.last_selected_text,
                height=140,
                disabled=True,
            )
            additional_query = st.text_area(
                "Add to query (optional)",
                key="additional_query",
                height=110,
                placeholder="Add a question or instruction, then press Ask. Leave blank to query only the selected text.",
            )
            ask_clicked = st.button("Ask", type="primary", use_container_width=True)

            if ask_clicked:
                st.session_state.last_model = active_model
                st.session_state.last_answer = ""
                st.session_state.last_error = ""
                with st.spinner("Asking Ollama..."):
                    try:
                        st.session_state.last_answer = ask_ollama(
                            st.session_state.last_selected_text,
                            additional_query,
                            active_model,
                        )
                    except requests.RequestException as exc:
                        st.session_state.last_error = str(exc)
        else:
            st.info("Select words directly on the PDF page with your mouse.")

        st.subheader("Answer")
        if st.session_state.last_error:
            st.error(
                "Could not reach Ollama. Check that Ollama is running and that "
                f"`{active_model}` is available.\n\n{st.session_state.last_error}"
            )
        elif st.session_state.last_answer:
            st.markdown(normalize_latex_for_markdown(st.session_state.last_answer))
        else:
            st.caption("The answer will appear here after you select text.")


if __name__ == "__main__":
    main()
