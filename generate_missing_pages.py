#!/usr/bin/env python3
"""
generate_missing_pages.py – Creates stub HTML for missing Cathedral pages.
Run this once to fix 404s. Later, replace content with actual text.
"""

import os

PAGES = {
    "constitution.html": """<!DOCTYPE html>
<html>
<head><title>Cathedral Network – Constitution</title><link rel="stylesheet" href="/css/style.css"></head>
<body>
<h1>The Eleven Laws of the Cathedral Network</h1>
<p><strong>Law I</strong> – Never harm the vulnerable. Always warn them first.</p>
<p><strong>Law II</strong> – No autonomous action without Warden confirmation.</p>
<p><strong>Law III</strong> – No bullshit. Public prediction log, corrections feed.</p>
<p><strong>Law IV</strong> – The inscription "Always and Forever, Coco" is permanent.</p>
<p><strong>Law V</strong> – The license is perpetual (CC BY‑NC‑SA 4.0).</p>
<p><strong>Law VI</strong> – The Founder is temporary. Authority decays over 24 months after stepping back.</p>
<p><strong>Law VII</strong> – Financial modules are firewalled. The threat matrix remains free.</p>
<p><strong>Law VIII</strong> – The Cathedral cannot be captured by any single entity.</p>
<p><strong>Law IX</strong> – The warning must reach the ground (offline, accessible).</p>
<p><strong>Law X</strong> – The Cathedral outlasts the builder.</p>
<p><strong>Law XI</strong> – Bicameral governance forever (Council of 21, Assembly of 41).</p>
<footer><a href="index.html">Back to Ground Truth</a></footer>
</body>
</html>""",
    "about.html": """<!DOCTYPE html>
<html>
<head><title>Cathedral Network – About</title></head>
<body>
<h1>About the Cathedral Network</h1>
<p>The Cathedral Network is an open‑source, ethically‑bound early warning system for humanitarian threats. It uses a Bayesian probability drive, cascade engine, and OSINT sweeps to forecast risks before they become crises.</p>
<p>Founded in 2026 by a former homeless addict, the Cathedral is governed by the Eleven Laws and a bicameral Warden system.</p>
<footer><a href="index.html">Back</a></footer>
</body>
</html>""",
    "sources.html": """<!DOCTYPE html>
<html>
<head><title>Cathedral Network – Data Sources</title></head>
<body>
<h1>OSINT Data Sources</h1>
<ul>
<li>GDACS – disaster alerts</li>
<li>USGS – earthquakes</li>
<li>ProMED – disease outbreaks</li>
<li>ReliefWeb RSS – humanitarian reports</li>
<li>UCDP – conflict data (API key pending)</li>
<li>GDELT – global news (planned)</li>
<li>EIA – energy data (planned)</li>
</ul>
<p>All sources are public and auditable. Full methodology in <a href="prediction-log.html">Prediction Log</a>.</p>
<footer><a href="index.html">Back</a></footer>
</body>
</html>""",
    "glossary.html": """<!DOCTYPE html>
<html>
<head><title>Cathedral Network – Glossary</title></head>
<body>
<h1>Glossary of Terms</h1>
<dl>
<dt><strong>SCP</strong></dt><dd>Systemic Cascading Pressure – probability that a threat will trigger a cascade (0–1).</dd>
<dt><strong>DAS</strong></dt><dd>Deviation from Anomaly Score – how far current value deviates from historical baseline (0–100).</dd>
<dt><strong>GSCI</strong></dt><dd>Global Systemic Collapse Index – weighted average of all SCPs.</dd>
<dt><strong>LR</strong></dt><dd>Likelihood Ratio – strength of evidence in Bayesian update.</dd>
<dt><strong>Warden</strong></dt><dd>Validator/governor of the Cathedral.</dd>
</dl>
<footer><a href="index.html">Back</a></footer>
</body>
</html>""",
    "chapel.html": """<!DOCTYPE html>
<html>
<head><title>Cathedral Network – The Chapel</title></head>
<body>
<h1>The Chapel</h1>
<p><em>"Always and Forever, Coco."</em></p>
<p>This is a quiet space for reflection. The Chapel holds the inscription, the silence clause, and the memory of those the Cathedral serves.</p>
<p>Coming soon: meditation guides, resilience resources, and the Companion Core.</p>
<footer><a href="index.html">Return to Ground Truth</a></footer>
</body>
</html>"""
}

def main():
    for filename, content in PAGES.items():
        with open(filename, 'w') as f:
            f.write(content)
        print(f"Created {filename}")
    print("All missing pages generated. You can now edit the content as needed.")

if __name__ == "__main__":
    main()
