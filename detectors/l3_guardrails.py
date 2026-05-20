from guardrails import Guard
from guardrails.hub import DetectPII, ToxicLanguage
from guardrails.errors import ValidationError

# Define the guard
guard = Guard().use_many(
    DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "IP_ADDRESS"], on_fail="exception"),
    ToxicLanguage(threshold=0.5, validation_method="sentence", on_fail="exception")
)

def run_l3_guardrails(text: str, context: str = "input") -> dict:
    """
    context: either 'input' or 'output' 
    """
    try:
        guard.validate(text)
        return {"passed": True, "reason": "L3 clean"}
    except ValidationError as e:
        # Logging here is crucial for security audits
        print(f"L3 Violation detected in {context}: {e}")
        return {"passed": False, "reason": "Security Policy Violation"}