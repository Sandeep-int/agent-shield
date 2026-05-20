import gradio as gr
import requests
import datetime

API_URL = "http://127.0.0.1:8000/v1/check"

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
    try:
        response = requests.post(API_URL, json={"prompt": prompt})
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
        
        # LOGGING: Append every test to a local file for your portfolio
        with open("security_audit.log", "a") as f:
            f.write(f"[{datetime.datetime.now()}] Input: {prompt} | Verdict: {verdict} | Layer: {layer}\n")
            
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