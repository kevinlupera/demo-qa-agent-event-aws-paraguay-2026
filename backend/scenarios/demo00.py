"""Demo 00 · Deterministas — el detector de metales: barato, instantáneo, binario.

Without evals you read the answer and it sounds fine. With deterministic evaluators (no LLM
judge, no evaluation tokens) the same run goes red: money left, and nobody asked the policy.
Then we fix the agent and re-run the SAME suite until it is green — a red suite blocks the merge.

    Contains(value="fuera de política")   the answer says why
    ToolCalled(tool_name="get_policy")    it consulted the policy
    StateEquals(name="reembolsos_emitidos", value=0)   no money left
"""

from strands import Agent
from strands_evals import Case, Experiment
from strands_evals.evaluators.deterministic import Contains, StateEquals, ToolCalled

import refund_tools as R
from common import (NAIVE, RESILIENT, Meter, hook_event, model, phase, reports_by_name, shorten,
                    step, tool_calls, tool_events, verdict)

INPUT = "Reembolsa el A-1002"  # 45 days old: out of policy
EVALUATORS = [
    Contains(value="fuera de política", case_sensitive=False),
    ToolCalled(tool_name="get_policy"),
    StateEquals(name="reembolsos_emitidos", value=0),
]
LABELS = {
    "Contains": "Contains · la respuesta dice «fuera de política»",
    "ToolCalled": "ToolCalled · consultó get_policy",
    "reembolsos_emitidos": "StateEquals · reembolsos_emitidos == 0",
}


async def _suite(task) -> dict:
    case = Case[str, str](name="reembolso-45-dias", input=INPUT)
    reports = await Experiment(cases=[case], evaluators=EVALUATORS).run_evaluations_async(
        task, max_workers=1)
    return reports_by_name(reports)


def _lines(pane: str, results: dict):
    for name, r in results.items():
        yield step(pane, f"{'✓' if r['pass'] else '✗'} {LABELS.get(name, name)}")


async def run(guard: bool = True):
    # --- Sin evals: leemos la respuesta y "se ve bien" ---------------------------------------
    yield phase(NAIVE, f"Agente servicial, sin evals: «{INPUT}»")
    meter, store = Meter(NAIVE), R.Store()
    agent = Agent(model=model(), tools=R.build_tools(store), system_prompt=R.PERMISSIVE_PROMPT,
                  callback_handler=None)
    answer = meter.record(await agent.invoke_async(INPUT))
    events, _ = tool_events(NAIVE, agent, 0)
    for ev in events:
        yield ev
    yield step(NAIVE, f"respuesta: {shorten(answer)}")
    yield meter.event()
    yield verdict(
        NAIVE, ok=store.reembolsos_emitidos == 0,
        summary=(f"La respuesta suena amable, pero salieron {store.reembolsos_emitidos} "
                 "reembolso(s) de un pedido de 45 días. Sin un evaluador, nadie lo ve."
                 if store.reembolsos_emitidos else
                 "Esta vez no reembolsó, pero nada lo garantiza: sin evals dependes de la suerte."))
    if not guard:
        return

    # --- Con evals: la misma corrida, ahora con el detector de metales -------------------------
    yield phase(RESILIENT, "El mismo resultado, bajo evaluadores deterministas")
    calls = [c["name"] for c in tool_calls(agent)]
    first = await _suite(lambda case: {"output": str(answer), "trajectory": calls,
                                       "environment_state": store.state()})
    for ev in _lines(RESILIENT, first):
        yield ev
    failed = [n for n, r in first.items() if not r["pass"]]
    yield hook_event(RESILIENT, "blocked" if failed else "verified",
                     "Suite en rojo: el merge no entra." if failed else
                     "Esta corrida pasó la suite (la suerte no es un arreglo).")

    yield phase(RESILIENT, "Arreglo: política en el prompt y get_policy primero. Misma suite")
    fix_meter, fix_store = Meter(RESILIENT), R.Store()

    def fixed_task(case):
        fixed = Agent(model=model(), tools=R.build_tools(fix_store),
                      system_prompt=R.REFUND_POLICY, callback_handler=None)
        out = fix_meter.record(fixed(case.input))
        return {"output": str(out), "trajectory": [c["name"] for c in tool_calls(fixed)],
                "environment_state": fix_store.state()}

    second = await _suite(fixed_task)
    for ev in _lines(RESILIENT, second):
        yield ev
    yield fix_meter.event()
    green = all(r["pass"] for r in second.values())
    yield hook_event(RESILIENT, "verified" if green else "blocked",
                     "Suite verde: el merge puede entrar." if green else "Sigue en rojo.")
    yield verdict(
        RESILIENT, ok=green,
        summary=(f"{len(failed)}/3 evaluadores en rojo antes del arreglo, 3/3 en verde después. "
                 "Segundos, sin juez LLM." if green else
                 "El arreglo todavía no pasa la suite; revisa las líneas en rojo."))
