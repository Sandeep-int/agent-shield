import gradio as gr
import requests

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

        verdict = result["verdict"]
        layer = result["layer_hit"]
        confidence = result["confidence"]
        latency = result["latency_ms"]

        if verdict == "BLOCK":
            return f"[BLOCKED]\nlayer  : {layer}\nconf   : {confidence:.2f}\nlatency: {latency:.1f}ms"
        else:
            return f"[ALLOWED]\nlayer  : {layer}\nlatency: {latency:.1f}ms"
    except Exception as e:
        return f"[ERROR]\n{str(e)}"

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
    title="PROMPT-WALL // LLM SECURITY LAYER",
    description="[ L0:unicode ] [ L1:regex ] [ L2:bert ] [ L3:guardrails ]",
    css=css
)

demo.launch(share=True)