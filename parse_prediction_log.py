#!/usr/bin/env python3
"""
parse_prediction_log.py – extract all resolved predictions (confirmed + falsified)
from prediction-log.html and create historical_predictions.json.
Confirmed predictions get default probability 0.9 (you can edit later).
Falsified predictions use the probability found in the description.
"""

import re
from bs4 import BeautifulSoup
import json

def parse_html():
    with open("prediction-log.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    predictions = []

    # ---- Confirmed predictions ----
    confirmed_header = soup.find("h2", string=re.compile("Confirmed"))
    if confirmed_header:
        table = confirmed_header.find_next("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:  # skip header
                cells = row.find_all("td")
                if len(cells) >= 2:
                    pred_id = cells[0].get_text(strip=True)
                    # For confirmed, assign default probability 0.9
                    # You can later edit the JSON to change this per prediction
                    predictions.append({
                        "prediction_id": pred_id,
                        "predicted_probability": 0.9,
                        "outcome": True,
                        "deadline": cells[2].get_text(strip=True) if len(cells) > 2 else "unknown"
                    })

    # ---- Falsified predictions ----
    falsified_header = soup.find("h2", string=re.compile("Falsified"))
    if falsified_header:
        table = falsified_header.find_next("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:  # skip header
                cells = row.find_all("td")
                if len(cells) >= 4:
                    pred_id = cells[0].get_text(strip=True)
                    desc = cells[1].get_text(strip=True)
                    # Extract probability from description (e.g., "72% prob")
                    prob_match = re.search(r'(\d+(?:\.\d+)?)%', desc)
                    if prob_match:
                        prob = float(prob_match.group(1)) / 100.0
                    else:
                        # fallback: search whole row
                        row_text = row.get_text()
                        prob_match2 = re.search(r'(\d+(?:\.\d+)?)%', row_text)
                        if prob_match2:
                            prob = float(prob_match2.group(1)) / 100.0
                        else:
                            prob = 0.7   # default for falsified if no probability found
                    predictions.append({
                        "prediction_id": pred_id,
                        "predicted_probability": prob,
                        "outcome": False,
                        "deadline": cells[2].get_text(strip=True) if len(cells) > 2 else "unknown"
                    })

    # ---- Manually add P39 if missing (it is falsified with 5%) ----
    existing_ids = [p["prediction_id"] for p in predictions]
    if "P39" not in existing_ids:
        predictions.append({
            "prediction_id": "P39",
            "predicted_probability": 0.05,
            "outcome": False,
            "deadline": "8 Jun 2026"
        })

    # ---- Write output ----
    with open("historical_predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    print(f"Extracted {len(predictions)} resolved predictions (confirmed + falsified).")
    print("Confirmed predictions use default probability 0.9. Edit historical_predictions.json to fine-tune.")

if __name__ == "__main__":
    parse_html()
