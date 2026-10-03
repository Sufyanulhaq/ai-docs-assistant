# AI Docs Assistant

A chat assistant that answers questions from your own documentation, streams the answer as it is written, and shows exactly which passages each claim came from.

Python (FastAPI) backend, Next.js (TypeScript) front end. It works with Claude or OpenAI, and also runs with no API key at all in an offline mode.

The sample knowledge base is a set of help docs for **Fernhill Cloud, a fictional company** written for this demo. Drop your own markdown files into `docs/` to use it on real content.

## What it does

- Searches the docs with BM25 and passes only the relevant passages to the model
- Streams the answer token by token over server sent events
- Cites every claim as `[1]`, `[2]`, with clickable sources that open the exact passage
- Refuses to guess: a question with nothing relevant in the docs never reaches the model and gets an honest "could not find it" reply
- Handles short follow ups ("and for annual plans?") using the conversation history
- Rate limits, validates input, and keeps API keys on the server only

## Architecture

```
Browser (Next.js)  ->  /api/chat (Next route, streams through)  ->  FastAPI backend
                                                                      |
                                                       BM25 search over docs/*.md
                                                                      |
                                             relevance gate ->  Claude | OpenAI | offline
```

The browser never talks to the Python service directly. Next.js proxies the stream, so there is no CORS setup and the backend URL stays private.

## Run it

Built and tested with Python 3.13 and Node 22.

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # optional: add an API key here, it is loaded automatically
uvicorn app.main:app --port 8000
```

**Front end** (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

### Choosing how answers are written

| Mode | How to enable | Behaviour |
|---|---|---|
| Offline | nothing, this is the default | Quotes the most relevant passages from the docs with citations. No key, no cost. |
| Claude | set `ANTHROPIC_API_KEY` | Written answers. Default model `claude-opus-5-5`, change it with `ANTHROPIC_MODEL` (for example `claude-haiku-4-5` for a cheaper bot). |
| OpenAI | set `OPENAI_API_KEY` and `OPENAI_MODEL` | Written answers from the model you name. |

The header badge shows which mode is active. Settings come from `backend/.env` or from real environment variables, and real environment variables win.

### Use your own documents

1. Put `.md` or `.txt` files in `docs/`. Headings become the section names shown in citations.
2. Restart the backend, or set `ADMIN_TOKEN` and call `POST /api/reindex` with the header `X-Admin-Token`.
3. Change `COMPANY_NAME` so the assistant introduces itself correctly.

## API

`POST /api/chat` with `{"question": "...", "history": [{"role": "user", "content": "..."}]}` returns a `text/event-stream`:

| Event | Data |
|---|---|
| `sources` | list of `{id, file, title, section, snippet, score}`, sent first so the UI can show them immediately |
| `token` | `{"text": "..."}`, repeated |
| `done` | `{"grounded": true}` or `false` when nothing relevant was found |
| `error` | `{"message": "..."}`, safe to show to users |

Also: `GET /api/health`, `GET /api/sources`, `POST /api/reindex`.

## Design decisions

**BM25 instead of embeddings.** For a few hundred pages of docs, keyword search with good chunking is accurate, instant, free and easy to debug. The tests show 18 out of 18 sample questions finding the right document in the top three results. The cost is that it does not understand synonyms. If your content needs that, swap `retrieval.py` for an embedding index; nothing else changes.

**Chunking follows the document.** Text is split on headings, so every passage knows its section path (for example `Refunds and cancellation > Refund window`). Long sections are packed into passages under 900 characters with a small overlap.

**Two layers against made up answers.** First a cheap relevance gate: if no passage matches the question well enough, the model is never called. Second, the system prompt tells the model to use only the supplied passages, to cite them, to say so when they do not contain the answer, and to treat passage text as data rather than instructions.

**Follow ups borrow context carefully.** A short message like "and annual?" is combined with the previous question for searching, but only if the message itself contains a term the docs know. An off topic message ("tell me a joke") does not inherit the previous topic. This was a real bug found while testing in the browser, and it has a regression test.

**Provider code is isolated.** `providers/` has one small class per backend behind the same `stream()` interface. Provider errors become short user safe messages, so API details never reach the browser.

## Tests

```bash
cd backend && python -m pytest
```

58 tests cover chunking, retrieval accuracy on an 18 question evaluation set, the junk question filter, the streaming API, validation, rate limiting, admin protection, settings loading, and each provider using fake clients. No network or API key is needed.

## Honest limitations

- The Claude and OpenAI paths are covered by unit tests with fake clients. Run them once with your own key to confirm the live behaviour before relying on them.
- The relevance gate is a heuristic. Some off topic questions that share a word with the docs (for example "do you support a mobile app") pass it, and in offline mode they return loosely related passages. With a model attached, the grounding rules in the prompt handle these.
- Rate limiting is in memory and per server process. Use a shared store such as Redis if you run several instances, and put the app behind a proxy that sets the client address correctly.
- Refusals from the model are reported as an error message. Add the SDK's server side fallback option if you need automatic retries on another model.

## Project layout

```
backend/app/        FastAPI app, chunking, BM25 retrieval, prompts, providers
backend/tests/      pytest suite
frontend/           Next.js app (chat UI, streaming client, proxy routes)
docs/               sample knowledge base (fictional company)
```
