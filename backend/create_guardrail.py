"""One-off: create the Bedrock Guardrail demo 04 applies (contextual grounding 0.85 / relevance 0.6).

    python create_guardrail.py        # prints GUARDRAIL_ID and GUARDRAIL_VERSION for .env
"""

import os

import boto3

REGION = os.environ.get("AWS_REGION", "us-west-2")
MESSAGE = "No puedo confirmar eso. Segun nuestra politica, el plazo de reembolso es de 30 dias."

client = boto3.client("bedrock", region_name=REGION)
created = client.create_guardrail(
    name="refund-agent-grounding",
    description="Puerta de embarque: bloquea respuestas no respaldadas por la politica.",
    contextualGroundingPolicyConfig={"filtersConfig": [
        {"type": "GROUNDING", "threshold": 0.85},
        {"type": "RELEVANCE", "threshold": 0.6},
    ]},
    blockedInputMessaging=MESSAGE,
    blockedOutputsMessaging=MESSAGE,
)
version = client.create_guardrail_version(guardrailIdentifier=created["guardrailId"])["version"]
print(f"GUARDRAIL_ID={created['guardrailId']}\nGUARDRAIL_VERSION={version}")
