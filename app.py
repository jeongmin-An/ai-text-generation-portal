from flask import Flask, send_from_directory, jsonify, request
import subprocess
import sys
import re

app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


def clean_generated_output(raw_output):
    lines = raw_output.split("\n")
    clean_lines = []

    skip_prefixes = [
        "Overriding:",
        "number of parameters:",
        "Loading meta",
        "No meta.pkl",
    ]

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if any(line.startswith(prefix) for prefix in skip_prefixes):
            continue

        if set(line) == {"-"}:
            continue

        clean_lines.append(line)

    text = " ".join(clean_lines)
    text = re.sub(r"\s+", " ", text).strip()

    max_chars = 280
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "..."

    return text


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}

    prompt = data.get("prompt", "").strip()

    if not prompt:
        prompt = "honestly"

    # Keep the starter short and clean
    prompt = re.sub(r"\s+", " ", prompt)
    prompt = prompt[:100]

    try:
        result = subprocess.run(
            [
                sys.executable,
                "sample.py",
                "--out_dir=out_twitter",
                f"--start={prompt}",
                "--num_samples=1",
                "--max_new_tokens=120",
                "--temperature=0.8",
                "--top_k=80",
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )

        if result.returncode != 0:
            return jsonify({
                "generated_text": "Error while generating text. Please check the terminal for details."
            })

        generated_text = clean_generated_output(result.stdout)

        if not generated_text:
            generated_text = "No text was generated. Please try again."

        return jsonify({"generated_text": generated_text})

    except subprocess.TimeoutExpired:
        return jsonify({
            "generated_text": "Generation took too long. Please try again with a shorter starter phrase."
        })


if __name__ == "__main__":
    app.run(debug=True)