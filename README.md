# 🏛️ Cathedral Network

**Constitutional · Transparent · Accountable**

The Cathedral is an open‑source, AI‑augmented threat intelligence platform designed to warn the vulnerable, hold power accountable, and outlast its builders. It is governed by a written Constitution (15 Immutable Laws, 10 Amendments) that binds every component—from data ingestion to prediction logging—to the principles of trust, transparency, and human dignity.

> *Always and Forever, Coco. Always and Forever.*

---

## 🧭 Mission

To provide early, accurate, and actionable warnings to communities that are most vulnerable to geopolitical, humanitarian, and systemic crises—while maintaining a public, auditable record of every prediction, source, and correction (Law III).

---

## 📊 Current Status

| Metric | Value |
|--------|-------|
| Threats tracked | 233 across 12 domains |
| Predictions logged | 159 (75 confirmed, 4 falsified, 42 expired, 38 pending) |
| Hit rate | 94.9% (Law III compliance) |
| Active OSINT feeds | 8+ (GDELT, CFR, GPSJAM, Telegram, GDACS, ReliefWeb, NASA EONET, IDMC) |
| Wardens (autonomous) | 11 built and operational |
| Human Wardens | 0 / 62 (recruitment open) |
| Historical validation | 5 major crises simulated – 76.2% accuracy |
| Cascade rules | 13 reverse‑engineered from history |
| Recovery thresholds | Calibrated for 3 major crises |

---

## 🏛️ Constitutional Governance

The Cathedral is not a tool—it is an institution. Its Constitution defines:

- **Law I (Justice Filter)** – Every action must first protect the vulnerable.
- **Law III (Trust Through Accuracy)** – All predictions are public, auditable, and corrected in real time.
- **Law V (The License is Perpetual)** – The Cathedral's license is irrevocable and binding on all contributors, Wardens, and users. No future entity may revoke or restrict the rights granted under this license.
- **Law VI (Founder Is Temporary)** – The Founder’s authority decays over 24 months.
- **Law IX (Warnings Must Reach the Ground)** – Intelligence must be accessible to communities with minimal technology.
- **Law XI (The Warden Corps)** – Human verification is required for Red and Black threats.

The full text is available at:  
[cathedral-network/constitution.html](https://sad9605.github.io/cathedral-network/constitution.html)

---

## 📦 Core Components

### 🧠 Intelligence Pipeline

- **Threat Scanner** – Pulls emerging threats from GDELT (with fallback mock data when API is rate‑limited).
- **GPSJAM Fetcher** – Retrieves GPS interference data; falls back to synthetic zones when endpoints are unavailable.
- **Telegram OSINT Fetcher** – Monitors public Telegram channels via Telethon.
- **HEWD Fetcher** – Aggregates humanitarian crises from GDACS, ReliefWeb, NASA EONET, and IDMC.
- **Archive Engine** – Moves resolved threats (status: Recovered, Peace, Retreated, Ended) to `archive.json`.

### 🤖 Autonomous Wardens

| Warden | Function |
|--------|----------|
| OSINT Triage (AW03) | Scores and prioritises new threat candidates (dry‑run by default) |
| Verification (AW04) | Flags missed deadlines and low‑confidence predictions |
| Validation (AW05) | Auto‑falsifies expired predictions, suggests manual checks |
| Pipeline Monitor (AW06) | Checks file freshness, JSON validity, and script health |
| Self‑Tuning (AW07) | Triggers SCP recalibration when scores flatten or time passes |
| GPS Jamming (AW14) | Monitors GPS interference (synthetic fallback) |
| Telegram OSINT (AW15) | Fetches real‑time alerts from Telegram |

### 📈 Historical Intelligence

- **Historical Validator** – Simulates Cathedral performance on 5 major past crises (GFC, Arab Spring, Crimea, COVID‑19, Ukraine invasion).
- **Historical Tuner** – Optimises SCP/SSI/GSCI parameters against historical data (76.2% accuracy).
- **Cascade Analyst** – Reverse‑engineers 13 cascade rules from historical patterns.
- **Ascension Tuner** – Calibrates recovery thresholds and optimism metrics.

### 🌐 Front‑End Dashboards

| Page | Function |
|------|----------|
| **Ground Truth** | Live GSCI, SSI, Hit Rate, Threat Count – auto‑refreshes every 60s |
| **Threat Matrix** | 233 threats across 12 domains – sortable, filterable, exportable |
| **Prediction Log** | 159 predictions with statuses – confirms, falsifies, and expires automatically |
| **Daily Brief** | Plain‑language intelligence brief with GSCI card, global state, Opportunity Matrix |
| **HEWD Dashboard** | Real‑time humanitarian crises – mortality‑weighted, expandable details |
| **Conflict Monitor** | 3D globe (under repair – data load in progress) |

---

## 📂 Key Data Files

| File | Contents |
|------|----------|
| `threats.json` | 233 active threats – master framework across 12 domains |
| `predictions.json` | 159 predictions with deadlines, confidence, criteria, and status |
| `cascade_log.json` | 371 cascade rules (active and historical) |
| `indices.json` | GSCI, SSI values |
| `scp_history.json` | SCP history for delta tracking |
| `hewd_data.json` | Live humanitarian crises from 4 sources |
| `tuned_parameters.json` | Optimised ML weights, dampening, thresholds |
| `ascension_config.json` | Recovery thresholds and optimism metrics |
| `suggested_rules.json` | 13 cascade rules derived from historical analysis |

---

## 🚀 Running the Cathedral

### Prerequisites

- Python 3.10+
- Git
- (Optional) Telethon credentials for Telegram OSINT

### Installation

```bash
git clone https://github.com/sad9605/cathedral-network.git
cd cathedral-network
pip install -r requirements.txt
```

Daily Pipeline

```bash
python3 run_wardens.py
```

This orchestrates all steps in sequence. The Threat Matrix is locked and protected by guardian.py.

Generate a New Daily Brief

```bash
python3 generate_daily_brief.py
```

Add a New Prediction

```bash
python3 create_prediction.py "Statement" YYYY-MM-DD 72 "Confirmation criteria" "Falsification criteria"
```

---

🧭 Transparency & Accountability (Law III)

Every prediction is:

· Logged with a unique ID, statement, deadline, confidence, confirmation criteria, and falsification criteria.
· Checked daily by the Prediction Checker – automatically marked Confirmed, Falsified, or Expired.
· Published on the Prediction Log page with a public correction feed (corrections.xml).

Hit rate is calculated from verified predictions only – no cherry‑picking, no retroactive changes.

---

🧑‍⚖️ Governance

The Cathedral is governed by a bicameral Warden Corps:

· Council (21 Wardens) – Strategy, oversight, Black threat confirmation.
· Assembly (41 Wardens) – Verification, operations, day‑to‑day accuracy.

Current status: Structure is defined in the Constitution. Recruitment is open.

Apply by reading the Constitution and contacting the Founder via the Warden page.

---

🏆 Current Engagements

· UNDP Crisis Mapping Challenge – Submission under evaluation (first round passed).
· NLNet Commons Grant – Pending review.

---

🛠️ Known Limitations

· Conflict Monitor (3D globe) – Not currently loading data (C01/C02 – in progress).
· ACLED integration – Pending email response.
· Human Wardens – 0 of 62 recruited.
· Multi‑language warnings – Not yet implemented (Law IX).
· Low‑bandwidth channels – Not yet implemented (Law IX).
· Financial firewall – Not yet implemented (Law VII).

---

🧭 Roadmap (Abridged)

Phase Focus
Current Fix Conflict Monitor, recruit Wardens, integrate ACLED
Next 3 months Multi‑language warnings, low‑bandwidth channels, financial firewall
Next 6 months Supply Chain Forecaster, Information Integrity Sentinel, Climate Hazard Module
Next 12 months Public API, enterprise subscriptions, institutional partnerships

---

📜 License

© 2026 Cathedral Network. All rights reserved.

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

Law V – The License is Perpetual.
This license is irrevocable and binding on all contributors, Wardens, and users. No future entity may revoke or restrict the rights granted under this license.

To view a copy of this license, visit:
https://creativecommons.org/licenses/by-nc-sa/4.0/

You are free to:

· Share – copy and redistribute the material in any medium or format.
· Adapt – remix, transform, and build upon the material.

Under the following terms:

· Attribution – You must give appropriate credit, provide a link to the license, and indicate if changes were made.
· NonCommercial – You may not use the material for commercial purposes.
· ShareAlike – If you remix, transform, or build upon the material, you must distribute your contributions under the same license.

---

🤝 Contributing

We welcome contributions that align with the Constitution.

1. Read the Constitution.
2. Fork the repository.
3. Submit a pull request with a clear description of your changes.

All contributions are subject to Law III (Trust Through Accuracy) and must include source citations.

---

📬 Contact

· Website: sad9605.github.io/cathedral-network
· Constitution: constitution.html
· Warden Recruitment: wardens.html

---

Always and Forever, Coco. Always and Forever.


Law V is now reflected in the README. The license is perpetual, irrevocable, and binding on all contributors, Wardens, and users. 🏛️
