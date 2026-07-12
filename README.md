# Document classifier agent interview

Build the instructions and tools for an agent that classifies lending documents
and finds the page boundaries inside combined submission packages.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add the temporary interview key to `.env`, then run:

```bash
python classify.py
```

The model is fixed in `agent.py`; choosing or configuring a model is not part of
the task. The initial `classify.py` is only a connectivity check and should
return a small JSON response before you begin.

## Data

Each source PDF in `data/pdfs` has cached OCR in `data/ocr` with the same stem:

```text
data/pdfs/example.pdf
data/ocr/example.json
```

The OCR file is a JSON array of strings, one layout-preserving string per page:

```json
[
  "OCR text for page one...",
  "OCR text for page two..."
]
```

No OCR service is called during the interview.

## Your task

Replace the connectivity check in `classify.py` with your document-classification
instructions and tools.

The `File` class already provides:

- `get_parsed_content()`
- `get_page_count()`
- `get_page_text(page_number)`
- `get_page_lines(page_number, count, from_end)`

The `Agent` class already handles the model/tool loop and parallel tool calls.
`Tool` bundles an OpenAI Responses function definition with an async handler.

Aim for correct document types and page boundaries on both short documents and
large combined packages without reading unnecessary document content.
