"""AgentCore Runtime entrypoint — one agent, five scenarios.

Invoke with `{"demo": "01", "guard": true}`. Each scenario is an async generator of events
(see common.py for the vocabulary); AgentCore streams them to the caller as SSE, and the Nuxt
frontend renders them into the two panes (sin esa capa / con esa capa).

Local:  python app.py            -> http://localhost:8080/invocations
Deploy: agentcore configure -e app.py && agentcore launch
"""

import os
import traceback

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from bedrock_agentcore import BedrockAgentCoreApp

from scenarios import demo00, demo01, demo02, demo03, demo04

SCENARIOS = {
    "00": demo00.run,
    "01": demo01.run,
    "02": demo02.run,
    "03": demo03.run,
    "04": demo04.run,
}

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload):
    demo = str(payload.get("demo", "01")).zfill(2)
    guard = bool(payload.get("guard", True))

    run = SCENARIOS.get(demo)
    if run is None:
        yield {"t": "error", "message": f"demo desconocida: {demo} (usa 00..04)"}
        return

    try:
        async for event in run(guard=guard):
            yield event
    except Exception as exc:  # a failed demo must say why, not hang the page
        yield {"t": "error", "message": f"{type(exc).__name__}: {exc}",
               "trace": traceback.format_exc()[-800:]}
    finally:
        yield {"t": "done"}


if __name__ == "__main__":
    app.run()
