#!/usr/bin/env python3
"""
causal_cartographer.py – Causal Cartographer for Cathedral Network
Extracts causal relationships from OSINT text and generates candidate cascade rules.
Uses Gemini API (or fallback rule‑based).
"""

import json
import re
import os
from datetime import datetime, timezone

# ── Try to import Gemini ──
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ── Config ──
GEMINI_MODEL = "gemini-1.5-flash"
FALLBACK_RULES = [
    {"source": "C01", "target": "C11", "delta": 0.2},
    {"source": "C11", "target": "C03", "delta": 0.15},
    {"source": "C01", "target": "G30", "delta": 0.1},
    {"source": "C03", "target": "C139", "delta": 0.15},
    {"source": "B02", "target": "C77", "delta": 0.1},
    {"source": "C10", "target": "D01", "delta": 0.1},
    {"source": "C10", "target": "I10", "delta": 0.15},
]

def load_existing_rules():
    try:
        with open("cascade_rules.json", "r") as f:
            data = json.load(f)
            return data.get("rules", [])
    except:
        return []

def extract_with_gemini(text):
    """Use Gemini to extract causal relationships."""
    if not GENAI_AVAILABLE:
        return None
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set. Using fallback.")
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""
    You are the Causal Cartographer for the Cathedral Network.
    Given the following OSINT text, extract cause‑effect relationships.
    For each relationship, identify:
    - Source (the cause)
    - Target (the effect)
    - Delta (strength of causality, 0.1–0.3)
    - Confidence (0–100%)

    Return ONLY a JSON array of objects with fields: source, target, delta, confidence, description.
    If no relationships found, return an empty array.

    Text:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        # Extract JSON from response
        json_str = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_str:
            return json.loads(json_str.group())
        else:
            return None
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return None

def extract_with_fallback(text):
    """Rule‑based fallback extraction."""
    # Simple pattern matching for known triggers
    candidates = []
    patterns = [
        (r"Hormuz|Strait.*closure", "C01", "C11", 0.2),
        (r"oil.*price.*spike|Brent.*\d+", "C11", "C03", 0.15),
        (r"famine|hunger|food.*crisis", "C03", "C139", 0.15),
        (r"ebola|outbreak|pandemic", "B02", "C77", 0.1),
        (r"deepfake|disinformation|misinfo", "C10", "I10", 0.15),
        (r"election.*integrity|voter.*fraud", "C10", "D01", 0.1),
        (r"drought|water.*crisis|river.*flow", "C43", "C13", 0.15),
        (r"TSMC|semiconductor|chip.*shortage", "C121", "C39", 0.2),
        (r"Taiwan.*blockade|PLA.*exercises", "C15", "C39", 0.2),
        (r"Nile.*GERD|Ethiopia.*dam", "C76", "C33", 0.15),
        (r"cartel.*violence|homicide.*surge", "C85", "C61", 0.1),
    ]
    for pattern, source, target, delta in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            candidates.append({
                "source": source,
                "target": target,
                "delta": delta,
                "confidence": 65,
                "description": f"Extracted from text: {text[:100]}..."
            })
    return candidates

def main():
    print("🧠 Causal Cartographer running...")

    # Load existing rules to avoid duplicates
    existing_rules = load_existing_rules()
    existing_pairs = {(r.get("source"), r.get("target")) for r in existing_rules}

    # Read input text (from file or stdin)
    text = ""
    try:
        with open("osint_input.txt", "r") as f:
            text = f.read()
    except FileNotFoundError:
        print("⚠️ osint_input.txt not found. Using hardcoded sample.")
        text = """
        The Strait of Hormuz closure continues to disrupt oil supply, causing Brent crude to spike above $150.
        Famine conditions in Sudan are worsening as conflict blocks humanitarian access.
        TSMC's 3nm capacity is fully booked, exacerbating the global chip shortage.
        H5N1 avian influenza has been detected in dairy cattle across 20 US states.
        Deepfake campaigns are targeting the upcoming US midterm elections.
        """

    candidates = []
    # Try Gemini first
    if GENAI_AVAILABLE and os.environ.get("GEMINI_API_KEY"):
        candidates = extract_with_gemini(text) or []
    # If Gemini fails, use fallback
    if not candidates:
        candidates = extract_with_fallback(text)

    # Filter out duplicates
    new_rules = []
    for c in candidates:
        pair = (c.get("source"), c.get("target"))
        if pair not in existing_pairs:
            new_rules.append({
                "source": c["source"],
                "target": c["target"],
                "delta": min(c.get("delta", 0.15), 0.3),
                "condition": "always",
                "description": c.get("description", "Auto‑generated by Causal Cartographer"),
                "confidence": c.get("confidence", 60),
                "status": "proposed",
                "generated_at": datetime.now(timezone.utc).isoformat()
            })
            existing_pairs.add(pair)

    if new_rules:
        # Append to cascade_rules.json
        with open("cascade_rules.json", "r") as f:
            data = json.load(f)
        data["rules"].extend(new_rules)
        with open("cascade_rules.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Added {len(new_rules)} new candidate cascade rules.")
        for r in new_rules:
            print(f"   - {r['source']} → {r['target']} (delta {r['delta']})")
    else:
        print("ℹ️ No new rules generated.")

if __name__ == "__main__":
    main()
