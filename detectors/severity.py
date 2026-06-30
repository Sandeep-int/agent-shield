def get_severity(layer: str, confidence: float = None) -> str:
    """
    Map detection layer + confidence to severity level.
    Returns None for ALLOW/pass-through (no threat detected).
    """
    if layer == "COMPREHENSIVE_PASS":
        return None
    if layer == "L1_VIGIL_SIGNATURE":
        return "HIGH"
    if layer == "L2_ONNX_MODEL":
        if confidence is not None and confidence > 0.9:
            return "HIGH"
        return "MEDIUM"
    if layer in ("L2_TIMEOUT_BLOCK", "L2_ERROR_BLOCK"):
        return "MEDIUM"
    if layer == "L3_MDEBERTA":
        return "MEDIUM"
    if layer == "L4_CUSTOM_RULES":
        return "HIGH"
    if layer == "L5_ADVISORY_ASYNC":
        return "LOW"
    return "MEDIUM"
