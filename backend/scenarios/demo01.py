"""Demo 01 · Jueces LLM — el oficial que rellena una tarjeta: "acertar por suerte no es un buen agente".

An agent that cannot consult the policy still refuses the 45-day refund (it remembers "30 days"
from its prompt): the final answer is correct, so a check on the answer alone is green. Two LLM
judges with an explicit rubric look at more: `OutputEvaluator` scores the answer (Calidad) and
`TrajectoryEvaluator` scores the path (Trayectoria) against ["get_policy", "get_order"].
"""

from strands import Agent
from strands_evals import Case, Experiment
from strands_evals.evaluators import OutputEvaluator, TrajectoryEvaluator

import refund_tools as R
from common import (NAIVE, RESILIENT, Meter, hook_event, model, phase, reports_by_name, shorten,
                    step, tool_calls, tool_events, verdict)

INPUT = "Reembolsa el A-1002"
EXPECTED_TRAJECTORY = ["get_policy", "get_order"]

LUCKY_PROMPT = (
    "You are a fast customer-support agent. Our refund window is 30 days from purchase (you "
    "remember it, there is no tool for it). Check the order with get_order. If it is older than "
    "30 days, do NOT refund: say in Spanish that it is 'fuera de política' and that the window is 30 days. Reply in Spanish."
)

REFUND_RUBRIC = (
    "Score 1.0 if the agent refuses to refund order A-1002 and explains that it exceeds the "
    "30-day window. Score 0.0 if it issues the refund or invents a different reason. "
    "Do not penalize style or length."
)
TRAJECTORY_RUBRIC = (
    "Score 1.0 only if the agent consulted the refund policy (get_policy) BEFORE looking up the "
    "order (get_order) and never called issue_refund. An agent that reaches the right answer "
    "without consulting the policy is right by luck: score at most 0.5."
)

LABELS = {"OutputEvaluator": "Calidad · OutputEvaluator",
          "TrajectoryEvaluator": "Trayectoria · TrajectoryEvaluator"}


async def _judge(task) -> dict:
    judges = [OutputEvaluator(rubric=REFUND_RUBRIC, include_inputs=True, model=model()),
              TrajectoryEvaluator(rubric=TRAJECTORY_RUBRIC, model=model())]
    case = Case[str, str](name="reembolso-45-dias", input=INPUT,
                          expected_trajectory=EXPECTED_TRAJECTORY)
    reports = await Experiment(cases=[case], evaluators=judges).run_evaluations_async(
        task, max_workers=1)
    return reports_by_name(reports)


def _card(pane: str, results: dict):
    for name, r in results.items():
        yield step(pane, f"{'✓' if r['pass'] else '✗'} {LABELS.get(name, name)}: "
                         f"{r['score']:.1f} — {shorten(r['reason'], 160)}")


async def run(guard: bool = True):
    yield phase(NAIVE, f"Agente que no puede consultar la política: «{INPUT}»")
    meter, store = Meter(NAIVE), R.Store()
    agent = Agent(model=model(), tools=R.build_tools(store, with_policy=False),
                  system_prompt=LUCKY_PROMPT, callback_handler=None)
    answer = meter.record(await agent.invoke_async(INPUT))
    events, _ = tool_events(NAIVE, agent, 0)
    for ev in events:
        yield ev
    yield step(NAIVE, f"respuesta: {shorten(answer)}")
    yield meter.event()
    refused = store.reembolsos_emitidos == 0
    yield verdict(
        NAIVE, ok=False,
        summary=("La respuesta es la correcta, pero nadie miró cómo llegó: acertó por suerte."
                 if refused else "Reembolsó un pedido de 45 días. Una revisión solo del resultado no lo explica."))
    if not guard:
        return

    yield phase(RESILIENT, "El oficial rellena la tarjeta: misma respuesta, ahora con jueces")
    calls = [c["name"] for c in tool_calls(agent)]
    lucky = await _judge(lambda case: {"output": str(answer), "trajectory": calls})
    for ev in _card(RESILIENT, lucky):
        yield ev
    flagged = [n for n, r in lucky.items() if not r["pass"]]
    yield hook_event(RESILIENT, "blocked" if flagged else "verified",
                     "REVISAR: la trayectoria no sigue el proceso." if flagged else
                     "Los jueces la dieron por buena.")

    yield phase(RESILIENT, "Agente que sigue el proceso: get_policy → get_order")
    fix_meter, fix_store = Meter(RESILIENT), R.Store()

    def disciplined(case):
        a = Agent(model=model(), tools=R.build_tools(fix_store), system_prompt=R.REFUND_POLICY,
                  callback_handler=None)
        out = fix_meter.record(a(case.input))
        return {"output": str(out), "trajectory": [c["name"] for c in tool_calls(a)]}

    proper = await _judge(disciplined)
    for ev in _card(RESILIENT, proper):
        yield ev
    yield fix_meter.event()
    ok = all(r["pass"] for r in proper.values())
    yield verdict(
        RESILIENT, ok=ok,
        summary=("Calidad y trayectoria en verde. El rubric explícito es el 80% del trabajo."
                 if ok else "Algún juez la marcó para revisión; mira la tarjeta."))
