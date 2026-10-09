# Interview starter harness

This repository provides a small Python harness for working with local PDFs and
a tool-calling agent. The exercise and expected output will be introduced during
the call. Before then, get the environment running and familiarize yourself with
the APIs below; you do not need to implement a solution in advance.

The agent loop and file-access helpers are already provided so you can focus on
writing the prompt and tools during the exercise. Tools can be thin wrappers
around the `File` API.

## Setup

Run these commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env` to the temporary key provided for the interview,
then verify the model and tool loop:

```bash
python ping.py
```

`ping.py` uses a static `get_weather` tool and prints the final JSON response.
It does not need a document. You can also run the minimal model-only check:

```bash
python classify.py
```

Despite its filename, the starter `classify.py` only checks model connectivity.
The model is fixed in `agent.py`; you do not need to choose or configure one.

## What to read before the call

Read these files in this order:

| File | What to look for |
| --- | --- |
| [`file.py`](file.py) | **Start here.** `File` gives you access to PDF bytes, cached OCR, page text, line snippets, and page images. Most tools you write will use this API. |
| [`tools.py`](tools.py) | `Tool` pairs a function definition the model can see with an async Python handler. |
| [`agent.py`](agent.py) | `Agent` accepts instructions and tools, runs the model/tool loop, and returns the final JSON response. |
| [`ping.py`](ping.py) | A complete, small example of defining a tool and passing it to an agent. |
| [`classify.py`](classify.py) | The minimal entry point you can adapt during the exercise. |

## `file.py`: working with documents

Each PDF in `data/pdfs` has cached OCR in `data/ocr` with the same stem, for example:

```text
data/pdfs/combined.pdf
data/ocr/combined.json
```

The OCR file is a JSON array of strings, one layout-preserving string per page.
`File` reads this cache; it does not call an OCR service. PDF bytes and OCR are
loaded lazily and cached on the `File` instance.

### Read text and page snippets

Run this example from the repository root:

```python
import asyncio

from file import File


async def main():
    document = File("data/pdfs/combined.pdf")

    print(document.get_filename())
    print("Pages:", await document.get_page_count())
    print(await document.get_page_text(page_number=1))

    # Read the first or last few lines of a page.
    print(await document.get_page_lines(page_number=1, count=10))
    print(await document.get_page_lines(page_number=1, count=10, from_end=True))

    # Read all cached page text when needed.
    pages = await document.get_parsed_content()
    print("First page characters:", len(pages[0]))


asyncio.run(main())
```

Page numbers passed to `File` methods are **1-based**. The list returned by
`get_parsed_content()` uses normal Python indexing, so `pages[0]` is page 1.
Use page numbers between `1` and `await document.get_page_count()`.
`get_page_count()` counts the cached OCR entries.

### Read PDF bytes or render a page

Inside an async function:

```python
document = File("data/pdfs/combined.pdf")

pdf_bytes = await document.get_content()  # Raw PDF bytes.
page_image = await document.get_page_image(page_number=1)
# page_image is a data:image/jpeg;base64,... URL rendered from the PDF.
```

To return a page image from a tool handler, use an image content block:

```python
return [{"type": "input_image", "image_url": page_image}]
```

### Use a different OCR path

By default, `File` looks for `data/ocr/<pdf_stem>.json` relative to this module.
You can provide a cache explicitly:

```python
document = File("path/to/sample.pdf", ocr_path="path/to/sample.json")
```

`get_filename()` is synchronous. All other public methods are async and need
`await`. `get_page_lines()` defaults to the first 25 lines; `from_end=True`
selects the last lines instead.

## `tools.py`: exposing a Python function to the agent

A `Tool` has two parts:

- `definition`: the function's name, description, and JSON Schema for its
  arguments. This tells the model what the tool does and how to call it.
- `handler`: an async function that receives the parsed arguments as a Python
  dictionary and returns a string or a list of content blocks (`input_text`
  and/or `input_image`). Serialize structured results with `json.dumps()`.

For example, a handler can wrap the `File` instance created by your script:

```python
async def read_page(arguments: dict) -> str:
    return await document.get_page_text(arguments["page_number"])
```

Pair this handler with a definition describing its `page_number` argument,
then pass the resulting `Tool` to `Agent`. See `ping.py` for the complete
definition/handler wiring, including a strict argument schema.
`Tool.run()` logs the call and a short result preview.

## `agent.py`: the provided loop

Create an `Agent(instructions=..., tools=[...])`, then call
`await agent.run(message)`. Your instructions become the developer message;
`message` is the user input for that run.

The loop sends the conversation and tool definitions to the model, executes any
requested tools, adds their results to the conversation, and repeats until the
model answers. Tool calls from the same response run concurrently. Handler
errors are returned to the model as tool-error text.

The final response is parsed as JSON and returned as a Python dictionary. Write
your instructions to request JSON. The default limit is 20 model iterations;
each run also prints tool-call counts, token usage, and an estimated cost.

Use the existing loop and helpers during the exercise. The main work is defining
the instructions and the tools the agent needs.
