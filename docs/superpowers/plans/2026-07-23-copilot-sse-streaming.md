# Copilot SSE Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Copilot's single blocking HTTP POST with SSE streaming so the drafter sees text appear word-by-word immediately, with citations and the "Insert into draft" snippet flushed atomically once the model finishes.

**Architecture:** A new `POST /api/workstreams/{ws}/tasks/{node}/copilot/stream` route returns a `StreamingResponse` with `text/event-stream` content. The backend streams `token` events as text chunks arrive from the model, accumulates the full text, runs the existing citation guardrail (`_validate_reply`) after the stream exhausts, then emits a single `done` event with validated citations + optional snippet. The frontend replaces its `useMutation` with a plain `fetch` + `ReadableStream` consumer that accumulates tokens into a partial-message bubble until the `done` event arrives.

**Tech Stack:** FastAPI `StreamingResponse` (built-in, no new dep), Anthropic SDK `client.messages.stream()` (already installed, version 0.116.0+), React `useState` + `fetch` `ReadableStream` API, MSW `ReadableStream` for tests.

## Global Constraints

- Never commit to `main` directly — all work on `badar` branch.
- Conventional Commits format: `feat(scope): description` / `fix(scope): description`.
- The existing `POST /copilot` route and all its tests MUST continue to pass untouched.
- `copilot_reply()` and all helpers (`_validate_reply`, `_build_grounding_context`, `_build_messages`, `_call_and_parse`) are reused, not duplicated.
- Citation safety guardrail is never bypassed — validated after stream exhausts, same as blocking path.
- No new Python dependencies (FastAPI `StreamingResponse` is built-in; anthropic SDK streaming already available).
- Run engine tests with: `.venv/Scripts/python.exe -m pytest engine/tests -q`
- Run frontend tests with: `cd frontend && npx vitest run`
- Run frontend build/typecheck: `cd frontend && npm run build`

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `engine/llm.py` | Modify | Add `call_chat_stream()` generator using `client.messages.stream()` |
| `engine/copilot.py` | Modify | Add `CopilotStreamFn` type alias + `_copilot_stream_turn()` + `copilot_reply_stream()` generator |
| `engine/api.py` | Modify | Add `copilot_stream_fn` param to `create_app()`; add `POST .../copilot/stream` route |
| `engine/tests/test_copilot.py` | Modify | Add tests for `copilot_reply_stream` (token events, done event, error event, graceful degrade) |
| `engine/tests/test_api_drafting.py` | Modify | Add tests for the `/copilot/stream` API route |
| `frontend/src/lib/types.ts` | Modify | Add `StreamingCopilotDone` type |
| `frontend/src/lib/api.ts` | Modify | Add `streamCopilotMessage()` that returns an async generator of SSE events |
| `frontend/src/features/drafting-workspace/CopilotTab.tsx` | Modify | Replace `useMutation` with streaming state machine; render partial-text bubble |
| `frontend/src/test/msw/handlers.ts` | Modify | Add `/copilot/stream` MSW handler returning a `ReadableStream` |

---

## Task 1: `engine/llm.py` — add `call_chat_stream()` generator

**Files:**
- Modify: `engine/llm.py`
- Test: `engine/tests/test_llm.py` (create if absent; check with `ls engine/tests/test_llm.py`)

**Interfaces:**
- Produces: `call_chat_stream(deployment: str, system: str, messages: list[dict[str, str]], max_tokens: int = 8192) -> Generator[str, None, None]`

- [ ] **Step 1: Write the failing test**

Check if `engine/tests/test_llm.py` exists first:
```bash
ls engine/tests/test_llm.py 2>/dev/null && echo exists || echo missing
```

If missing, create `engine/tests/test_llm.py`. If it exists, append to it. Either way, add:

```python
# engine/tests/test_llm.py
"""Tests for engine.llm — network seam + defensive JSON parsing.

call_chat_stream is the streaming counterpart to call_chat.
These tests use a stub to avoid live credentials.
"""
import pytest
from engine.llm import call_chat_stream

def test_call_chat_stream_is_importable():
    """Confirm the function exists before testing its behaviour."""
    assert callable(call_chat_stream)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_llm.py::test_call_chat_stream_is_importable -v
```
Expected: `FAILED` or `ERROR` with `ImportError: cannot import name 'call_chat_stream'`

- [ ] **Step 3: Implement `call_chat_stream` in `engine/llm.py`**

Open `engine/llm.py`. After the closing `return "".join(...)` of `call_chat`, and before `parse_json_response`, add:

```python
def call_chat_stream(
    deployment: str,
    system: str,
    messages: list[dict[str, str]],
    max_tokens: int = 8192,
) -> "Generator[str, None, None]":
    """Stream a Claude deployment on Azure AI Foundry, yielding text chunks.

    Uses `client.messages.stream(...)` — the Anthropic SDK's context-manager
    streaming API — and yields each text chunk from `.text_stream` as it
    arrives, so the caller can forward chunks to the client without waiting
    for the full model response.

    `call_chat` is left unchanged and still used by `engine.connections`
    (finder/critic) which needs the full text at once for JSON parsing.
    This function is the streaming seam for the Copilot only.
    """
    from typing import Generator  # local import keeps the module-level clean
    from anthropic import AnthropicFoundry

    if not AZURE_FOUNDRY_ENDPOINT or not AZURE_FOUNDRY_API_KEY:
        raise RuntimeError(
            "AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_API_KEY must be set "
            "in the environment to call call_chat_stream"
        )

    client = AnthropicFoundry(
        api_key=AZURE_FOUNDRY_API_KEY,
        base_url=AZURE_FOUNDRY_ENDPOINT,
    )
    with client.messages.stream(
        model=deployment,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
    ) as stream:
        for text in stream.text_stream:
            yield text
```

Add `Generator` to the top-level import from `typing` at the top of `llm.py` (or keep the local import inside the function as shown — either is fine; the local import avoids touching the module's type annotation style).

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_llm.py::test_call_chat_stream_is_importable -v
```
Expected: `PASSED`

- [ ] **Step 5: Run full engine suite to confirm no regressions**

```bash
.venv/Scripts/python.exe -m pytest engine/tests -q 2>&1 | tail -5
```
Expected: same failure count as before this task (33 pre-existing failures, all unrelated to this change).

- [ ] **Step 6: Commit**

```bash
git add engine/llm.py engine/tests/test_llm.py
git commit -m "feat(engine): add call_chat_stream generator for SSE copilot streaming"
```

---

## Task 2: `engine/copilot.py` — add `copilot_reply_stream()` generator

**Files:**
- Modify: `engine/copilot.py`
- Test: `engine/tests/test_copilot.py`

**Interfaces:**
- Consumes from Task 1: `call_chat_stream(deployment, system, messages, max_tokens) -> Generator[str]`
- Produces:
  - `CopilotStreamFn = Callable[[str, list[dict[str, str]]], Generator[str, None, None]]`
  - `copilot_reply_stream(*, node, intent, history, message, referenced_finding_ids, clause_index, workstreams_dir, workstream_id, stream_fn=None) -> Generator[str, None, None]`
  - Each yielded string is a complete SSE frame ending in `\n\n`

**SSE wire format this function produces:**
```
event: token\ndata: {"t": "Hello"}\n\n
event: token\ndata: {"t": " world"}\n\n
event: done\ndata: {"citations": [...], "snippet_html": "..."}\n\n
event: error\ndata: {"code": "COPILOT_FAILED", "message": "..."}\n\n
```

- [ ] **Step 1: Write failing tests**

Add to `engine/tests/test_copilot.py` (after existing tests):

```python
import json as _json

from engine.copilot import copilot_reply_stream


def _collect_sse(gen) -> list[dict]:
    """Parse SSE frames from the generator into a list of {event, data} dicts."""
    events = []
    for frame in gen:
        lines = frame.strip().split("\n")
        event = next((l[len("event: "):] for l in lines if l.startswith("event: ")), "message")
        data_line = next((l[len("data: "):] for l in lines if l.startswith("data: ")), "{}")
        events.append({"event": event, "data": _json.loads(data_line)})
    return events


def test_copilot_reply_stream_yields_token_events_then_done(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        yield "Hello"
        yield " world"

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    token_events = [e for e in events if e["event"] == "token"]
    done_events = [e for e in events if e["event"] == "done"]
    error_events = [e for e in events if e["event"] == "error"]

    assert len(token_events) == 2
    assert token_events[0]["data"]["t"] == "Hello"
    assert token_events[1]["data"]["t"] == " world"
    assert len(done_events) == 1
    assert len(error_events) == 0


def test_copilot_reply_stream_done_carries_validated_citations(tmp_path):
    clause_index = _clause_index(
        {"OpRes PD 5.3": {"document_id": "opres-pd-v0-3", "text": "Annually."}}
    )
    node = {"id": "opres-pd-v0-3", "title": "OpRes PD", "document_id": "opres-pd-v0-3"}

    def stub_stream(system, messages):
        yield _json.dumps({
            "text": "Cites a real clause.",
            "citations": [{"clause_number": "OpRes PD 5.3", "text": "ignored"}],
        })

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    done = next(e for e in events if e["event"] == "done")
    assert done["data"]["citations"][0]["clause_number"] == "OpRes PD 5.3"
    # text must come from grounded set, not model echo
    assert done["data"]["citations"][0]["text"] == "Annually."


def test_copilot_reply_stream_graceful_degrade_on_plain_prose(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        yield "Yes, there are overlaps between the clauses."

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    token_events = [e for e in events if e["event"] == "token"]
    done = next(e for e in events if e["event"] == "done")
    assert len(token_events) == 1
    assert "citations" not in done["data"]
    assert "snippet_html" not in done["data"]


def test_copilot_reply_stream_yields_error_event_on_stream_fn_exception(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        raise RuntimeError("Foundry credentials missing")
        yield  # make it a generator

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert "COPILOT_FAILED" in error_events[0]["data"]["code"]
    assert "credentials" in error_events[0]["data"]["message"]


def test_copilot_reply_stream_done_has_no_citations_when_none_are_grounded(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        yield _json.dumps({
            "text": "Cites a hallucinated clause.",
            "citations": [{"clause_number": "MADE UP 99.9", "text": "fake"}],
        })

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    done = next(e for e in events if e["event"] == "done")
    assert "citations" not in done["data"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_copilot.py -k "stream" -v 2>&1 | tail -20
```
Expected: all 5 stream tests fail with `ImportError: cannot import name 'copilot_reply_stream'`

- [ ] **Step 3: Implement `copilot_reply_stream` in `engine/copilot.py`**

Add to the top-level imports in `engine/copilot.py`:
```python
from engine.llm import LLMResponseError, call_chat, call_chat_stream, parse_json_response
```

After the existing `CopilotTurnFn` type alias (line ~55), add:
```python
from typing import Generator as _Generator
CopilotStreamFn = Callable[[str, list[dict[str, str]]], _Generator[str, None, None]]
```

After `_copilot_turn` function, add the streaming turn default:
```python
def _copilot_stream_turn(system: str, messages: list[dict[str, str]]) -> "Generator[str, None, None]":
    """Real streaming seam — calls call_chat_stream against Azure AI Foundry."""
    from typing import Generator
    yield from call_chat_stream(COPILOT_DEPLOYMENT, system, messages)
```

At the end of `engine/copilot.py`, add the full `copilot_reply_stream` generator:

```python
def copilot_reply_stream(
    *,
    node: dict[str, Any],
    intent: str,
    history: list[dict[str, str]],
    message: str,
    referenced_finding_ids: list[str],
    clause_index: ClauseIndex,
    workstreams_dir: Path,
    workstream_id: str,
    stream_fn: Optional[CopilotStreamFn] = None,
) -> "Generator[str, None, None]":
    """Stream a Copilot turn as SSE frames.

    Yields token events as text chunks arrive, then a single done event
    with validated citations+snippet after the stream exhausts. On any
    exception, yields an error event and stops — never a bare 502 from a
    partial stream.

    Wire format (each yielded string is a complete SSE frame):
        event: token\\ndata: {"t": "chunk"}\\n\\n
        event: done\\ndata: {"citations": [...], "snippet_html": "..."}\\n\\n
        event: error\\ndata: {"code": "COPILOT_FAILED", "message": "..."}\\n\\n

    `stream_fn` is an injectable seam — tests pass a stub generator so no
    live credentials are needed in CI. Defaults to `_copilot_stream_turn`
    which calls `engine.llm.call_chat_stream` against Azure AI Foundry.
    """
    import json

    streamer = stream_fn if stream_fn is not None else _copilot_stream_turn

    context, grounded = _build_grounding_context(
        node, clause_index, workstreams_dir, workstream_id, referenced_finding_ids
    )
    system = _system_prompt(node.get("title") or "this task", intent, context)
    messages_list = _build_messages(history, message)

    accumulated = ""
    try:
        for chunk in streamer(system, messages_list):
            accumulated += chunk
            yield f"event: token\ndata: {json.dumps({'t': chunk})}\n\n"
    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'code': 'COPILOT_FAILED', 'message': str(exc)})}\n\n"
        return

    # Stream exhausted — run citation guardrail on the full accumulated text.
    # Reuse _call_and_parse's retry logic by constructing a stub turn that
    # returns the accumulated string (no network call needed — we already have it).
    def _replay(_system: str, _messages: list) -> str:
        return accumulated

    _raw, parsed = _call_and_parse(_replay, system, messages_list, attempts=1)
    if parsed is None:
        # Plain prose — yield done with no citations (graceful degrade)
        yield f"event: done\ndata: {json.dumps({})}\n\n"
    else:
        validated = _validate_reply(parsed, grounded)
        done_payload: dict[str, Any] = {}
        if validated.get("citations"):
            done_payload["citations"] = validated["citations"]
        if validated.get("snippet_html"):
            done_payload["snippet_html"] = validated["snippet_html"]
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
```

**Note:** `Generator` needs to be imported from `typing`. Add to the imports at the top of the file:
```python
from typing import Any, Callable, Generator, Optional
```

- [ ] **Step 4: Run the new stream tests**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_copilot.py -k "stream" -v 2>&1 | tail -20
```
Expected: all 5 stream tests pass.

- [ ] **Step 5: Run the full copilot test suite**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_copilot.py -q
```
Expected: all 30 tests pass (25 pre-existing + 5 new stream tests).

- [ ] **Step 6: Commit**

```bash
git add engine/copilot.py engine/tests/test_copilot.py
git commit -m "feat(engine): add copilot_reply_stream SSE generator with citation guardrail"
```

---

## Task 3: `engine/api.py` — add `POST /copilot/stream` route

**Files:**
- Modify: `engine/api.py`
- Test: `engine/tests/test_api_drafting.py`

**Interfaces:**
- Consumes from Task 2: `copilot_reply_stream(**kwargs) -> Generator[str, None, None]`
- Produces: `POST /api/workstreams/{workstream_id}/tasks/{node_id}/copilot/stream` → `StreamingResponse` with `text/event-stream`
- Signature added to `create_app()`: `copilot_stream_fn: Any = _default_copilot_reply_stream`

- [ ] **Step 1: Write the failing API test**

Add to `engine/tests/test_api_drafting.py` (after the copilot POST tests):

```python
from engine.copilot import INTENTS as _COPILOT_INTENTS
import json as _json_mod


def _make_stream_client(tmp_path, stream_fn):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst, copilot_stream_fn=stream_fn))


def test_POST_copilot_stream_returns_sse_events(tmp_path):
    def stub_stream_fn(**kwargs):
        yield 'event: token\ndata: {"t": "Hello"}\n\n'
        yield 'event: done\ndata: {}\n\n'

    client = _make_stream_client(tmp_path, stub_stream_fn)
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot/stream",
        json={"intent": "PD", "message": "hi", "history": [], "referenced_finding_ids": []},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    body = res.text
    assert "event: token" in body
    assert "event: done" in body


def test_POST_copilot_stream_400_for_invalid_intent(tmp_path):
    client = _make_stream_client(tmp_path, lambda **kwargs: iter([]))
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot/stream",
        json={"intent": "InvalidIntent", "message": "hi"},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_INTENT"


def test_POST_copilot_stream_400_for_empty_message(tmp_path):
    client = _make_stream_client(tmp_path, lambda **kwargs: iter([]))
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/copilot/stream",
        json={"intent": "PD", "message": ""},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "MESSAGE_REQUIRED"


def test_POST_copilot_stream_404_for_non_task_node(tmp_path):
    client = _make_stream_client(tmp_path, lambda **kwargs: iter([]))
    res = client.post(
        f"/api/workstreams/{_OPRES}/tasks/{_ANCHOR}/copilot/stream",
        json={"intent": "PD", "message": "hi"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "TASK_NOT_FOUND"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_api_drafting.py -k "stream" -v 2>&1 | tail -20
```
Expected: all 4 stream API tests fail (route doesn't exist, `create_app` doesn't accept `copilot_stream_fn`).

- [ ] **Step 3: Add the stream route to `engine/api.py`**

**3a.** At the top of `engine/api.py`, update the copilot imports:
```python
from engine.copilot import copilot_reply as _default_copilot_reply
from engine.copilot import copilot_reply_stream as _default_copilot_reply_stream
```

**3b.** Add `StreamingResponse` to the FastAPI imports:
```python
from fastapi.responses import JSONResponse, StreamingResponse
```

**3c.** Add `copilot_stream_fn` to `create_app()` signature (after existing `copilot_reply_fn`):
```python
def create_app(
    workstreams_dir: Union[str, Path] = WORKSTREAMS_DIR,
    artifacts_dir: Union[str, Path] = REPO_ROOT / "data" / "artifacts",
    find_connections_fn: Any = _default_find_connections,
    copilot_reply_fn: Any = _default_copilot_reply,
    copilot_stream_fn: Any = _default_copilot_reply_stream,
) -> FastAPI:
```

Update the docstring `Args:` block to add:
```
        copilot_stream_fn: the streaming generator behind the `/copilot/stream`
            route — `(**kwargs) -> Generator[str]` yielding SSE frames.
            Injectable so tests stub it; defaults to
            `engine.copilot.copilot_reply_stream`.
```

**3d.** After the existing `post_copilot` route handler (the one ending `return {"reply": reply}`), add the new streaming route:

```python
    @app.post("/api/workstreams/{workstream_id}/tasks/{node_id}/copilot/stream")
    async def post_copilot_stream(
        workstream_id: str, node_id: str, request: Request
    ) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND",
                f"Workstream {workstream_id} not found",
            )
        node = _task_node(ws_graph, workstream_id, node_id)
        if isinstance(node, JSONResponse):
            return node
        body = await request.json() if await request.body() else {}
        if not isinstance(body, dict):
            body = {}
        intent = body.get("intent")
        if intent not in copilot.INTENTS:
            return _ws_error(
                400, "INVALID_INTENT",
                f"intent must be one of {list(copilot.INTENTS)}, got {intent!r}",
            )
        message = body.get("message")
        if not isinstance(message, str) or not message.strip():
            return _ws_error(
                400, "MESSAGE_REQUIRED", "message must be a non-empty string"
            )
        history = body.get("history") or []
        if not isinstance(history, list):
            history = []
        referenced_finding_ids = body.get("referenced_finding_ids") or []
        if not isinstance(referenced_finding_ids, list):
            referenced_finding_ids = []

        clause_index = load_clause_index(artifacts_dir)
        sse_generator = copilot_stream_fn(
            node=node,
            intent=intent,
            history=history,
            message=message,
            referenced_finding_ids=referenced_finding_ids,
            clause_index=clause_index,
            workstreams_dir=workstreams_dir,
            workstream_id=workstream_id,
        )
        return StreamingResponse(sse_generator, media_type="text/event-stream")
```

- [ ] **Step 4: Run the new API stream tests**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_api_drafting.py -k "stream" -v 2>&1 | tail -20
```
Expected: all 4 stream API tests pass.

- [ ] **Step 5: Run full drafting test suite**

```bash
.venv/Scripts/python.exe -m pytest engine/tests/test_api_drafting.py -q
```
Expected: same pass count as before + 4 new passing tests. The 5 pre-existing failures are fixture-drift issues unrelated to this change.

- [ ] **Step 6: Run full engine suite**

```bash
.venv/Scripts/python.exe -m pytest engine/tests -q 2>&1 | tail -5
```
Expected: 33 pre-existing failures (unchanged), all new tests passing.

- [ ] **Step 7: Commit**

```bash
git add engine/api.py engine/tests/test_api_drafting.py
git commit -m "feat(engine): add POST /copilot/stream SSE route with StreamingResponse"
```

---

## Task 4: Frontend types + streaming API function

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`

**Interfaces:**
- Produces (types):
  ```typescript
  export interface StreamingCopilotDone {
    citations?: CopilotCitation[];
    snippet_html?: string;
  }
  export type SSEEvent =
    | { event: "token"; data: { t: string } }
    | { event: "done"; data: StreamingCopilotDone }
    | { event: "error"; data: { code: string; message: string } };
  ```
- Produces (api):
  ```typescript
  export async function* streamCopilotMessage(
    workstreamId: string,
    nodeId: string,
    intent: CopilotIntent,
    message: string,
    history: ChatHistoryTurn[],
    referencedFindingIds: string[],
    signal: AbortSignal,
  ): AsyncGenerator<SSEEvent>
  ```

- [ ] **Step 1: Add types to `frontend/src/lib/types.ts`**

After the `ChatHistoryTurn` interface (around line 387), add:

```typescript
/** Payload of the SSE `done` event from `POST .../copilot/stream`. */
export interface StreamingCopilotDone {
  citations?: CopilotCitation[];
  snippet_html?: string;
}

/** A parsed SSE event from the Copilot streaming endpoint. */
export type SSEEvent =
  | { event: "token"; data: { t: string } }
  | { event: "done"; data: StreamingCopilotDone }
  | { event: "error"; data: { code: string; message: string } };
```

- [ ] **Step 2: Add `streamCopilotMessage` to `frontend/src/lib/api.ts`**

Add to the imports at the top of `api.ts`:
```typescript
import type {
  ...existing imports...
  SSEEvent,
} from "@/lib/types";
```

After the existing `sendCopilotMessage` function, add:

```typescript
/** Stream a Copilot reply via SSE. Yields typed events as they arrive.
 *  Pass an AbortSignal so the caller can cancel the in-flight fetch when
 *  the component unmounts, the intent changes, or the user navigates away. */
export async function* streamCopilotMessage(
  workstreamId: string,
  nodeId: string,
  intent: CopilotIntent,
  message: string,
  history: ChatHistoryTurn[],
  referencedFindingIds: string[],
  signal: AbortSignal,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(
    `${API_BASE}/api/workstreams/${workstreamId}/tasks/${nodeId}/copilot/stream`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        intent,
        message,
        history,
        referenced_finding_ids: referencedFindingIds,
      }),
      signal,
    },
  );

  if (!res.ok) {
    return throwHttpError(res);
  }

  // Parse the SSE stream from the response body.
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by "\n\n".
    const frames = buffer.split("\n\n");
    // The last element is either "" (complete) or a partial frame — keep it.
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      if (!frame.trim()) continue;
      const lines = frame.split("\n");
      const eventLine = lines.find((l) => l.startsWith("event: "));
      const dataLine = lines.find((l) => l.startsWith("data: "));
      if (!eventLine || !dataLine) continue;
      const event = eventLine.slice("event: ".length).trim() as SSEEvent["event"];
      const data = JSON.parse(dataLine.slice("data: ".length)) as SSEEvent["data"];
      yield { event, data } as SSEEvent;
    }
  }
}
```

- [ ] **Step 3: Run frontend typecheck**

```bash
cd frontend && npm run build 2>&1 | grep -E "error TS|✓ built" | head -10
```
Expected: `✓ built in ...` with no `error TS` lines. If there are TypeScript errors, fix the type imports before proceeding.

- [ ] **Step 4: Commit**

```bash
cd ..
git add frontend/src/lib/types.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): add SSEEvent types and streamCopilotMessage async generator"
```

---

## Task 5: `CopilotTab.tsx` — streaming state machine

**Files:**
- Modify: `frontend/src/features/drafting-workspace/CopilotTab.tsx`
- Test: `frontend/src/test/msw/handlers.ts` (add stream handler)
- Test: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Consumes from Task 4: `streamCopilotMessage(workstreamId, nodeId, intent, message, history, referencedFindingIds, signal): AsyncGenerator<SSEEvent>`
- Consumes from Task 4: `SSEEvent`, `StreamingCopilotDone`, `CopilotCitation`

**Streaming state machine:**
```
IDLE         → user submits → CONNECTING (AbortController created, fetch starts)
CONNECTING   → first token arrives → STREAMING (progress bar hides, partial bubble shows)
STREAMING    → "done" event → IDLE (full ChatMessage appended, streamingText cleared)
CONNECTING/  → "error" event → ERROR (errorText set, streamingText cleared)
STREAMING    → AbortController.abort() → IDLE (component unmount or intent change)
```

- [ ] **Step 1: Add the `/copilot/stream` MSW handler**

In `frontend/src/test/msw/handlers.ts`, after the existing `POST .../copilot` handler, add:

```typescript
http.post(
  "*/api/workstreams/:workstreamId/tasks/:nodeId/copilot/stream",
  async ({ request }) => {
    const body = (await request.json()) as {
      intent: CopilotIntent;
      message?: string;
      history?: { role: string; text: string }[];
    };
    const script = COPILOT_SCRIPT[body.intent];
    if (!script) {
      return HttpResponse.json(
        { code: "INVALID_INTENT", message: `bad intent ${body.intent}` },
        { status: 400 },
      );
    }
    if (!body.message?.trim()) {
      return HttpResponse.json(
        { code: "MESSAGE_REQUIRED", message: "message must be non-empty" },
        { status: 400 },
      );
    }

    // Build SSE body: stream the reply text character by character,
    // then flush citations in the done event.
    const turn = (body.history ?? []).filter((m) => m.role === "copilot").length;
    const index = Math.min(turn, script.length - 1);
    const reply = script[index] as {
      role: string;
      text: string;
      citations?: unknown[];
      snippet_html?: string;
    };

    // Emit one token event per word (chunked for realism in tests)
    const words = (reply.text as string).split(" ");
    let sseBody = "";
    for (let i = 0; i < words.length; i++) {
      const chunk = i === 0 ? words[i] : " " + words[i];
      sseBody += `event: token\ndata: ${JSON.stringify({ t: chunk })}\n\n`;
    }

    const donePayload: Record<string, unknown> = {};
    if (reply.citations) donePayload.citations = reply.citations;
    if (reply.snippet_html) donePayload.snippet_html = reply.snippet_html;
    sseBody += `event: done\ndata: ${JSON.stringify(donePayload)}\n\n`;

    return new HttpResponse(sseBody, {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    });
  },
),
```

- [ ] **Step 2: Rewrite `CopilotTab.tsx`**

Replace the entire file content with:

```tsx
import { useEffect, useRef, useState } from "react";
import { streamCopilotMessage } from "@/lib/api";
import {
  COPILOT_INTENTS,
  COPILOT_INTENT_LABELS,
  type ChatMessage,
  type CopilotCitation,
  type CopilotIntent,
  type LinkageCard,
  type StreamingCopilotDone,
} from "@/lib/types";
import { AnalyzeProgressBar, COPILOT_STAGES } from "@/components/AnalyzeProgressBar";
import { MentionInput, parseMentions } from "./MentionInput";

interface CopilotTabProps {
  workstreamId: string;
  nodeId: string;
  onInsertSnippet: (html: string) => void;
  reviewedCards: LinkageCard[];
}

type SendState = "idle" | "connecting" | "streaming";

export function CopilotTab({
  workstreamId,
  nodeId,
  onInsertSnippet,
  reviewedCards,
}: CopilotTabProps) {
  const [intent, setIntent] = useState<CopilotIntent>("PD");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sendState, setSendState] = useState<SendState>("idle");
  const [streamingText, setStreamingText] = useState<string>("");
  const [errorText, setErrorText] = useState<string | null>(null);

  // AbortController ref — aborts the in-flight stream when the user
  // changes intent, the component unmounts, or a new send starts.
  const abortRef = useRef<AbortController | null>(null);

  // Cancel any in-flight stream when the component unmounts.
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  function changeIntent(next: CopilotIntent) {
    abortRef.current?.abort();
    abortRef.current = null;
    setSendState("idle");
    setStreamingText("");
    setErrorText(null);
    setIntent(next);
    setMessages([]);
  }

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sendState !== "idle") return;

    const { referencedFindingIds } = parseMentions(trimmed, reviewedCards);

    // Append the user's message immediately.
    const historyForRequest = messages.map((m) => ({ role: m.role, text: m.text }));
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    setErrorText(null);
    setStreamingText("");
    setSendState("connecting");

    const controller = new AbortController();
    abortRef.current = controller;

    let accumulated = "";
    let donePayload: StreamingCopilotDone | null = null;

    try {
      const stream = streamCopilotMessage(
        workstreamId,
        nodeId,
        intent,
        trimmed,
        historyForRequest,
        referencedFindingIds,
        controller.signal,
      );

      for await (const evt of stream) {
        if (evt.event === "token") {
          accumulated += evt.data.t;
          setSendState("streaming");
          setStreamingText(accumulated);
        } else if (evt.event === "done") {
          donePayload = evt.data;
        } else if (evt.event === "error") {
          setErrorText(evt.data.message || "The Copilot failed to reply.");
          setSendState("idle");
          setStreamingText("");
          return;
        }
      }

      // Stream finished cleanly — commit the full message.
      const fullMessage: ChatMessage = {
        role: "copilot",
        text: accumulated || "No matching clause found",
        citations: donePayload?.citations,
        snippet_html: donePayload?.snippet_html,
      };
      setMessages((prev) => [...prev, fullMessage]);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        // Intentional cancel (intent change / unmount) — silent.
      } else {
        const msg = err instanceof Error ? err.message : "The Copilot failed to reply.";
        setErrorText(msg);
      }
    } finally {
      setSendState("idle");
      setStreamingText("");
      abortRef.current = null;
    }
  }

  const isPending = sendState !== "idle";
  const isConnecting = sendState === "connecting";
  const isStreaming = sendState === "streaming";

  return (
    <div className="flex h-full flex-col" data-testid="copilot-tab">
      <label className="block px-1 pb-2">
        <span className="sr-only">Intent preset</span>
        <select
          aria-label="Intent preset"
          value={intent}
          onChange={(e) => changeIntent(e.target.value as CopilotIntent)}
          className="w-full rounded-md border border-border/60 bg-background/60 px-2 py-1.5 text-sm outline-none focus:border-cyan-400/60"
        >
          {COPILOT_INTENTS.map((i) => (
            <option key={i} value={i}>
              {COPILOT_INTENT_LABELS[i]}
            </option>
          ))}
        </select>
      </label>

      <div
        className="flex-1 space-y-3 overflow-y-auto px-1"
        aria-label="Copilot conversation"
      >
        {messages.length === 0 && !isStreaming && (
          <p className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground">
            Ask the Copilot for a preamble, a section skeleton, or an FAQ
            answer. It only quotes clauses it can cite.
          </p>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            data-testid={`chat-${m.role}`}
            className={m.role === "user" ? "flex justify-end" : ""}
          >
            <div
              className={[
                "max-w-[92%] rounded-lg p-2.5 text-sm",
                m.role === "user"
                  ? "bg-cyan-500 text-slate-950"
                  : "bg-muted text-foreground",
              ].join(" ")}
            >
              <p className="leading-snug">{m.text}</p>

              {m.citations?.map((c: CopilotCitation) => (
                <blockquote
                  key={c.clause_number}
                  data-testid="copilot-citation"
                  className="mt-2 border-l-2 border-gray-400 bg-card/70 py-1 pl-2"
                >
                  <p className="font-mono text-[10px] font-semibold text-muted-foreground">
                    {c.clause_number}
                  </p>
                  <p className="text-[12px] italic leading-snug text-foreground">
                    &ldquo;{c.text}&rdquo;
                  </p>
                </blockquote>
              ))}

              {m.snippet_html && (
                <div className="mt-2 rounded border border-cyan-400/30 bg-card/60 p-2">
                  <div
                    className="prose-sm max-h-40 overflow-y-auto text-[12px] [&_h2]:mt-0 [&_h2]:text-[11px] [&_h2]:font-bold [&_p]:mt-1"
                    data-testid="copilot-snippet-preview"
                    dangerouslySetInnerHTML={{ __html: m.snippet_html }}
                  />
                  <div className="mt-2 flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => onInsertSnippet(m.snippet_html!)}
                      className="rounded bg-cyan-500 px-2 py-1 text-[11px] font-semibold text-slate-950 hover:bg-cyan-400"
                    >
                      Insert into draft
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Partial message bubble while streaming */}
        {isStreaming && streamingText && (
          <div data-testid="chat-copilot-streaming">
            <div className="max-w-[92%] rounded-lg bg-muted p-2.5 text-sm text-foreground">
              <p className="leading-snug">{streamingText}</p>
              <span className="ml-1 inline-block h-3 w-0.5 animate-pulse bg-current" />
            </div>
          </div>
        )}

        {/* Progress bar only while connecting (before first token) */}
        {isConnecting && (
          <AnalyzeProgressBar isPending={true} stages={COPILOT_STAGES} />
        )}

        {errorText && (
          <p className="text-xs text-red-600">{errorText}</p>
        )}
      </div>

      <form
        className="mt-2 flex gap-1.5 px-1"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <MentionInput
          value={input}
          onChange={setInput}
          cards={reviewedCards}
          disabled={isPending}
        />
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-cyan-500 px-3 py-1.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Run the full frontend test suite**

```bash
cd frontend && npx vitest run 2>&1 | tail -20
```

Some Copilot tests will need updating because they reference `useMutation` behaviour or the old non-streaming handler. The streaming MSW handler added in Step 1 replaces the old one for stream calls; the non-stream handler still serves `POST .../copilot` (kept as-is for existing tests).

**Expected test failures at this point** (fix them in Step 4):
- Tests that assert `"Copilot is typing…"` text — this text no longer exists; it's replaced by the partial bubble.
- Tests that wait for `chat-copilot` to appear — these should still work since `streamingText` is cleared and the full message appended on `done`.

- [ ] **Step 4: Fix any failing frontend tests**

For each failing test, trace what it expects vs. what the new UI provides:

**If a test asserts `"Copilot is typing…"` text** — update to `await screen.findByTestId("chat-copilot")` instead (the streaming bubble becomes a committed message once done).

**If a test asserts citation or snippet renders correctly** — no change needed; the `done` event carries those and the committed message renders them identically.

**If a test for `send.isError` is broken** — update to check for an element with `text-red-600` class or check for the error text content directly.

Run after each fix:
```bash
npx vitest run src/features/drafting-workspace 2>&1 | tail -20
```

- [ ] **Step 5: Run full frontend test suite and build**

```bash
npx vitest run 2>&1 | tail -10
npm run build 2>&1 | tail -10
```
Expected: all 107 tests pass (or updated count if tests were added/removed), `✓ built`.

- [ ] **Step 6: Commit**

```bash
cd ..
git add frontend/src/features/drafting-workspace/CopilotTab.tsx \
        frontend/src/test/msw/handlers.ts
git commit -m "feat(frontend): stream Copilot replies token-by-token via SSE, flush citations at done"
```

---

## Task 6: Push and verify

- [ ] **Step 1: Push to origin/badar and origin/staging**

```bash
git push origin badar
git push origin HEAD:staging
```

- [ ] **Step 2: Manual smoke test**

1. Start the engine: `PYTHONPATH=. .venv/bin/uvicorn engine.api:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to a drafting workspace (e.g. `/workstreams/opres-v2/tasks/opres-pd-v0-3/draft`)
4. Click the Copilot tab, type "what clauses are in this document?", press Send.
5. **Expected:** The progress bar shows briefly, then disappears as the first word appears. Text streams in word-by-word. Once complete, if the model returned citations, they appear below the text.
6. Type a follow-up ("does it overlap with any other policy?") without waiting too long.
7. **Expected:** Second turn streams correctly. No 502 errors in the terminal.

- [ ] **Step 3: Confirm no regressions**

```bash
.venv/Scripts/python.exe -m pytest engine/tests -q 2>&1 | tail -5
cd frontend && npx vitest run 2>&1 | tail -5
```
Both should show same or better numbers than before this feature.
