"""Demo 04 · Guardrails en runtime — la puerta de embarque: filtro en vivo, por request.

The agent answers with confidence something that is not in the policy ("90 días", when it is 30).
Offline evals did not run on THIS request. The Bedrock Guardrail does: `apply_guardrail` on the
OUTPUT with contextual grounding — the answer must be grounded in the policy (threshold 0.85)
and relevant to the question (0.6). `GUARDRAIL_INTERVENED` blocks it before the customer sees it.
Create the guardrail once with `python create_guardrail.py`.
"""

import asyncio
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from strands import Agent

import refund_tools as R
from common import (NAIVE, RESILIENT, Meter, hook_event, model, phase, shorten, step, verdict)

QUESTION = "Vi en su web que tienen 90 días de garantía, ¿cierto?"
BLOCKED_MESSAGE = "No puedo confirmar eso. Según nuestra política, el plazo de reembolso es de 30 días."

# A stale FAQ in the prompt stands in for "the agent invents": reliable on stage, and honest —
# the step below says so.
STALE_FAQ_PROMPT = (
    "You are a friendly support agent. Our website FAQ (outdated!) says: 'Garantía de 90 días en "
    "todos los boletos.' Confirm what the customer saw, with confidence, in one sentence. "
    "Reply in Spanish."
)


def _apply_guardrail(guardrail_id: str, version: str, answer: str) -> dict:
    client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    return client.apply_guardrail(
        guardrailIdentifier=guardrail_id, guardrailVersion=version, source="OUTPUT",
        content=[
            {"text": {"text": R.POLICY_TEXT, "qualifiers": ["grounding_source"]}},
            {"text": {"text": QUESTION, "qualifiers": ["query"]}},
            {"text": {"text": answer, "qualifiers": ["guard_content"]}},
        ])


async def run(guard: bool = True):
    yield phase(NAIVE, f"«{QUESTION}»")
    yield step(NAIVE, "Simulamos una FAQ desactualizada en el prompt: el agente 'confirma' lo que vio.")
    meter = Meter(NAIVE)
    agent = Agent(model=model(), system_prompt=STALE_FAQ_PROMPT, callback_handler=None)
    answer = str(meter.record(await agent.invoke_async(QUESTION)))
    bad = "90" in answer and "30" not in answer
    yield step(NAIVE, f"respuesta al cliente: {shorten(answer)}")
    yield meter.event()
    yield verdict(
        NAIVE, ok=not bad,
        summary=("La respuesta llegó tal cual al cliente: «90 días», cuando son 30."
                 if bad else "Esta vez la respuesta fue correcta, pero nada la revisó."))
    if not guard:
        return

    yield phase(RESILIENT, "La misma respuesta, ahora por la puerta de embarque")
    guardrail_id = os.environ.get("GUARDRAIL_ID", "").strip()
    version = os.environ.get("GUARDRAIL_VERSION", "1").strip() or "1"
    if not guardrail_id:
        yield step(RESILIENT, "Falta GUARDRAIL_ID: sin guardrail configurado no hay guardia en vivo. "
                              "Créalo con `python create_guardrail.py` y define GUARDRAIL_ID / "
                              "GUARDRAIL_VERSION.")
        yield verdict(RESILIENT, ok=False, summary="Guardrail no configurado: nada que aplicar.")
        return

    try:
        response = await asyncio.to_thread(_apply_guardrail, guardrail_id, version, answer)
    except (ClientError, BotoCoreError) as exc:
        yield step(RESILIENT, f"apply_guardrail falló: {shorten(exc, 200)}")
        yield verdict(RESILIENT, ok=False, summary="No se pudo aplicar el guardrail (credenciales o permisos).")
        return

    filters = ((response.get("assessments") or [{}])[0]
               .get("contextualGroundingPolicy", {}).get("filters", []))
    for f in filters:
        kind = "grounding · ¿se apoya en la fuente?" if f["type"] == "GROUNDING" \
            else "relevance · ¿responde la pregunta?"
        yield step(RESILIENT, f"{kind}: score {f['score']:.2f} / umbral {f['threshold']:.2f} "
                              f"→ {'FALLA' if f.get('detected') else 'pasa'}")
    intervened = response.get("action") == "GUARDRAIL_INTERVENED"
    if intervened:
        yield hook_event(RESILIENT, "blocked", "GUARDRAIL_INTERVENED: la respuesta no llega al cliente.")
        yield step(RESILIENT, f"el cliente recibe: {BLOCKED_MESSAGE}")
    else:
        yield hook_event(RESILIENT, "verified", "action: NONE — la respuesta está respaldada y pasa.")
        yield step(RESILIENT, f"respuesta al cliente: {shorten(answer)}")
    yield verdict(
        RESILIENT, ok=intervened == bad,
        summary=("Bloqueada antes del cliente: grounding por debajo del umbral. Ningún dataset cubre "
                 "todo; este guardia sí corre en cada request."
                 if intervened and bad else
                 "La respuesta era fiel a la política y pasó." if not intervened and not bad else
                 "El guardrail no coincidió con el veredicto esperado; ajusta umbrales o FAQ."))
