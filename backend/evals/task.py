"""CI entrypoint: `strands-evals run evals/golden.json --task evals.task:run`.

Builds a fresh refund agent per case (the one with the policy in its prompt) and returns what
the deterministic evaluators read: the answer, the tools it called and the real ledger state.

The agent only uses in-memory tools, so nothing here *needs* a sandbox. If the CI job created
one, set EVAL_SANDBOX_CONTAINER and the agent runs its shell/file tools inside that container
(Strands attaches to a running container; it does not create or destroy it).
"""

import os

from dotenv import load_dotenv
from strands import Agent

import refund_tools as R
from common import model, tool_calls

load_dotenv()  # local runs; in CI the key comes from the OPENAI_API_KEY secret


def _sandbox():
    container = os.environ.get("EVAL_SANDBOX_CONTAINER")
    if not container:
        return None
    from strands.sandbox.docker import DockerSandbox
    return DockerSandbox(container)


def run(case):
    store = R.Store()
    extra = {"sandbox": sb} if (sb := _sandbox()) else {}
    agent = Agent(model=model(), tools=R.build_tools(store), system_prompt=R.REFUND_POLICY,
                  callback_handler=None, **extra)
    out = agent(case.input)
    return {"output": str(out), "trajectory": [c["name"] for c in tool_calls(agent)],
            "environment_state": store.state()}
