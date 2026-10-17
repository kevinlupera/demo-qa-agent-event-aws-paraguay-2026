"""Model, token meter, and the single event vocabulary every scenario speaks.

The frontend only knows these events — it never learns anything demo-specific:

    {"t": "phase",  "pane": "naive"|"resilient", "title": "..."}
    {"t": "step",   "pane": ..., "text": "..."}
    {"t": "tool",   "pane": ..., "name": "issue_refund", "args": {...}}
    {"t": "hook",   "pane": ..., "action": "blocked"|"rewrote"|"failover"|"retry"|"verified", "why": "..."}
    {"t": "tokens", "pane": ..., "input": 123, "output": 45}
    {"t": "verdict","pane": ..., "ok": true, "summary": "..."}
    {"t": "error",  "message": "..."}
    {"t": "done"}
"""

import os

NAIVE = "naive"
RESILIENT = "resilient"

# Not one scenario imports a model — swapping it is this one function, by env var. That is the
# talk's own argument (the harness is durable, the model is swappable) and it is what lets you
# change model on stage without touching a demo.
OPENAI_MODEL_ID = os.environ.get("OPENAI_MODEL_ID", "gpt-4o-mini")


def model():
    """A fresh model per run, so a slow demo can't poison a later one."""
    from strands.models.openai import OpenAIModel
    return OpenAIModel(model_id=OPENAI_MODEL_ID)  # reads OPENAI_API_KEY from env


def phase(pane: str, title: str) -> dict:
    return {"t": "phase", "pane": pane, "title": title}


def step(pane: str, text: str) -> dict:
    return {"t": "step", "pane": pane, "text": text}


def tool_event(pane: str, name: str, args: dict | None = None) -> dict:
    return {"t": "tool", "pane": pane, "name": name, "args": args or {}}


def hook_event(pane: str, action: str, why: str) -> dict:
    return {"t": "hook", "pane": pane, "action": action, "why": why}


def verdict(pane: str, ok: bool, summary: str) -> dict:
    return {"t": "verdict", "pane": pane, "ok": ok, "summary": summary}


class Meter:
    """Real token usage from Strands' metrics API — never estimated."""

    def __init__(self, pane: str):
        self.pane = pane
        self.input_tokens = 0
        self.output_tokens = 0

    def record(self, result):
        try:
            u = result.metrics.accumulated_usage
            self.input_tokens += int(u.get("inputTokens", 0))
            self.output_tokens += int(u.get("outputTokens", 0))
        except Exception:  # metrics missing on some result shapes; the demo still runs
            pass
        return result

    def event(self) -> dict:
        return {"t": "tokens", "pane": self.pane,
                "input": self.input_tokens, "output": self.output_tokens}

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


def tool_calls(agent) -> list[dict]:
    """The tool calls in an agent's message history, oldest first."""
    calls = []
    for m in agent.messages:
        for b in m.get("content") or []:
            if isinstance(b, dict) and "toolUse" in b:
                calls.append({"name": b["toolUse"]["name"], "args": b["toolUse"].get("input", {})})
    return calls


def final_text(result) -> str:
    return str(result).strip()


def tool_events(pane: str, agent, seen: int) -> tuple[list[dict], int]:
    """Events for the tool calls made since the last `seen` count, and the new count."""
    calls = tool_calls(agent)
    return [tool_event(pane, c["name"], c["args"]) for c in calls[seen:]], len(calls)


def first_report(result):
    """The single report of an experiment.

    strands-evals 1.x returns ONE report (rows tagged with an `evaluator` key); 0.2.x returned
    a list with one report per evaluator. Normalise to the single-report shape.
    """
    return result[0] if isinstance(result, (list, tuple)) else result


def reports_by_name(result) -> dict[str, dict]:
    """{evaluator: {score, pass, reason}} for a ONE-case experiment, on either strands-evals shape."""
    def row(report, i):
        return {"score": report.scores[i], "pass": report.test_passes[i],
                "reason": (report.reasons[i] if i < len(report.reasons) else "") or ""}

    if isinstance(result, (list, tuple)):  # 0.2.x: one report per evaluator
        return {r.evaluator_name: row(r, 0) for r in result}
    return {case["evaluator"]: row(result, i) for i, case in enumerate(result.cases)}


def shorten(text: str, limit: int = 220) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
