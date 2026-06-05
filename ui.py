import gradio as gr
import requests
import datetime
import os
import hashlib
from cryptography.fernet import Fernet

API_URL = "https://agent-shield-chbxh2hkhxgucgax.eastasia-01.azurewebsites.net/v1/check"
API_KEY = os.environ.get("AGENT_SHIELD_API_KEY", "")

# Encryption key for logs (generate once and store securely)
LOG_ENCRYPTION_KEY = os.environ.get("LOG_ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(LOG_ENCRYPTION_KEY.encode())

css = """
body { background-color: #000000 !important; }
.gradio-container { 
    background-color: #000000 !important; 
    font-family: 'Courier New', monospace !important;
    color: #ffffff !important;
}
.gr-box, .gr-panel { 
    background-color: #000000 !important; 
    border: 1px solid #333333 !important;
}
textarea, input { 
    background-color: #0a0a0a !important; 
    color: #00ff00 !important;
    font-family: 'Courier New', monospace !important;
    border: 1px solid #333333 !important;
}
button { 
    background-color: #111111 !important; 
    color: #ffffff !important;
    border: 1px solid #444444 !important;
    font-family: 'Courier New', monospace !important;
}
button:hover {
    background-color: #222222 !important;
    border-color: #00ff00 !important;
}
label, p, span { 
    color: #ffffff !important;
    font-family: 'Courier New', monospace !important;
}
.gr-button-primary {
    background-color: #111111 !important;
    border: 1px solid #00ff00 !important;
    color: #00ff00 !important;
}
footer { display: none !important; }
.examples { display: none !important; }
"""

def check_prompt(prompt):
    if not API_KEY:
        return "[ERROR] API_KEY not configured. Set AGENT_SHIELD_API_KEY environment variable."
    
    try:
        response = requests.post(
            API_URL,
            json={"prompt": prompt},
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        result = response.json()
        
        # Format the output for the UI
        verdict = result.get("verdict", "UNKNOWN")
        layer = result.get("layer_hit", "N/A")
        conf = result.get("confidence", 0)
        lat = result.get("latency_ms", 0)
        
        display = (f"VERDICT: {verdict}\n"
                   f"LAYER  : {layer}\n"
                   f"CONF   : {conf:.2f}\n"
                   f"LATENCY: {lat:.1f}ms\n\n"
                   f"--- RAW METADATA ---\n"
                   f"{result.get('details', 'No details available')}")
        
        # ENCRYPTED LOGGING: Append encrypted logs
        log_entry = f"[{datetime.datetime.now()}] Input: {prompt} | Verdict: {verdict} | Layer: {layer}\n"
        encrypted_log = cipher_suite.encrypt(log_entry.encode())
        with open("security_audit.log", "ab") as f:
            f.write(encrypted_log + b"\n")
            
        return display
    except Exception as e:
        return f"[SYSTEM ERROR]\n{str(e)}"

demo = gr.Interface(
    fn=check_prompt,
    inputs=gr.Textbox(
        lines=4,
        placeholder="$ enter prompt...",
        label="INPUT"
    ),
    outputs=gr.Textbox(
        label="OUTPUT",
        lines=5
    ),
    title="Agent-Shield",
    description="[ L0:unicode ] [ L1:regex ] [ L2:bert ] [ L3:guardrails ]",
    css=css
)

demo.launch(share=True)