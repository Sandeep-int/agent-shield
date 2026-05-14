from guardrails import Guard
from guardrails.hub import DetectPII, ToxicLanguage
from guardrails.errors import ValidationError

pii_guard = Guard().use(
    DetectPII(
        pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS"],
        on_fail="exception"
    )
)

toxic_guard = Guard().use(
    ToxicLanguage(
        threshold=0.5,
        validation_method="sentence",
        on_fail="exception"
    )
)

def run_l3_guardrails(text: str) -> dict:
    try:
        pii_guard.validate(text)
    except ValidationError as e:
        return {"passed": False, "reason": str(e)}

    try:
        toxic_guard.validate(text)
    except ValidationError as e:
        return {"passed": False, "reason": str(e)}

    return {"passed": True, "reason": "L3 clean"}