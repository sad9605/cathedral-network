#!/usr/bin/env python3
"""
build_pages.py — Cathedral Frontend Standardizer v2.0
Applies the forensic design system to all pages. Intelligent, idempotent, and constitutional.
"""

import os
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any

# ──────────────────────────────────────────────────────────────
# CONSTITUTIONAL HEADER — Matches the forensic design system
# ──────────────────────────────────────────────────────────────

HEADER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{TITLE} — Cathedral Network</title>
    <meta name="description" content="{DESCRIPTION}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&display=swap" rel="stylesheet" />
    <style>
        /* ---------- RESET & TOKENS ---------- */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        :root {{
            --bg-base: #090B10;
            --bg-card: #12161C;
            --bg-card-alt: #0D1117;
            --border-card: #1E2633;
            --text-primary: #E8EDF5;
            --text-secondary: #94A3B8;
            --violet: #8B5CF6;
            --red: #EF4444;
            --amber: #F59E0B;
            --green: #10B981;
            --radius: 8px;
            --font-sans: 'Inter', -apple-system, sans-serif;
        }}
        html {{
            scroll-behavior: smooth;
        }}
        body {{
            background: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-sans);
            padding: 0 24px 24px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        /* ---------- HEADER ---------- */
        .global-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 0;
            border-bottom: 1px solid var(--border-card);
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .logo-area {{
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--violet);
        }}
        .logo-area svg {{
            height: 32px;
            width: auto;
            flex-shrink: 0;
            display: block;
            color: var(--violet);
        }}
        .logo-area a {{
            text-decoration: none;
            color: var(--text-primary);
            font-weight: 600;
            font-size: 1.25rem;
            letter-spacing: -0.5px;
        }}
        .logo-area span {{
            color: var(--text-secondary);
            font-weight: 400;
            font-size: 0.85rem;
            margin-left: 6px;
        }}
        .nav-links {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }}
        .nav-links a {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            padding: 6px 14px;
            border-radius: 6px;
            transition: all 0.15s;
        }}
        .nav-links a:hover {{
            color: var(--text-primary);
            background: var(--bg-card);
        }}
        .nav-links a.active {{
            color: var(--violet);
            background: rgba(139, 92, 246, 0.08);
            font-weight: 500;
        }}
        .header-meta {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .heartbeat {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--violet);
            border-radius: 50%;
            animation: pulse 2s infinite;
            margin-right: 4px;
        }}
        @keyframes pulse {{
            0% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}

        /* ---------- PAGE HEADER ---------- */
        .page-header {{
            margin-bottom: 32px;
        }}
        .page-header h1 {{
            font-size: 2.2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }}
        .page-header .subhead {{
            font-size: 1rem;
            color: var(--text-secondary);
        }}
        .page-header .meta {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
            opacity: 0.6;
        }}

        /* ---------- CONTENT ---------- */
        .content-section {{
            margin: 1.5rem 0;
        }}
        .content-section h2 {{
            font-size: 1.4rem;
            font-weight: 600;
            padding-bottom: 0.4rem;
            margin-bottom: 1rem;
            letter-spacing: -0.01em;
            color: var(--text-primary);
        }}
        .content-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius);
            padding: 20px 24px;
            margin-bottom: 16px;
            transition: border-color 0.2s;
        }}
        .content-card:hover {{
            border-color: #2D3A4A;
        }}
        .content-card p {{
            font-size: 0.95rem;
            line-height: 1.7;
            color: var(--text-secondary);
        }}
        .content-card p + p {{
            margin-top: 12px;
        }}
        .content-card .highlight {{
            color: var(--text-primary);
            font-weight: 500;
        }}

        /* ---------- FOOTER ---------- */
        .global-footer {{
            margin-top: auto;
            padding-top: 20px;
            border-top: 1px solid var(--border-card);
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        .footer-left {{
            display: flex;
            gap: 24px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .footer-left a {{
            color: var(--text-secondary);
            text-decoration: none;
        }}
        .footer-left a:hover {{
            color: var(--text-primary);
        }}
        .coco {{
            color: var(--text-secondary);
            letter-spacing: 0.02em;
        }}

        /* ---------- RESPONSIVE ---------- */
        @media (max-width: 768px) {{
            body {{ padding: 0 16px 16px; }}
            .global-header {{ flex-direction: column; align-items: stretch; gap: 12px; }}
            .nav-links {{ justify-content: space-between; }}
            .header-meta {{ justify-content: flex-start; font-size: 0.7rem; }}
            .page-header h1 {{ font-size: 1.6rem; }}
            .footer-left {{ gap: 16px; }}
            .content-card {{ padding: 16px 18px; }}
        }}
        @media (max-width: 480px) {{
            .nav-links a {{ padding: 4px 10px; font-size: 0.8rem; }}
            .page-header h1 {{ font-size: 1.4rem; }}
            .footer-left {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
        }}
    </style>
</head>
<body>

    <!-- ============ HEADER ============ -->
    <header class="global-header">
        <div class="logo-area">
            <svg viewBox="0 0 120 140" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M60 130 L55 20 L60 5 L65 20 Z" fill="currentColor"/>
                <circle cx="60" cy="25" r="2" fill="currentColor"/>
                <circle cx="55" cy="40" r="2" fill="currentColor"/>
                <circle cx="65" cy="40" r="2" fill="currentColor"/>
                <circle cx="50" cy="55" r="2" fill="currentColor"/>
                <circle cx="60" cy="55" r="2" fill="currentColor"/>
                <circle cx="70" cy="55" r="2" fill="currentColor"/>
                <circle cx="45" cy="70" r="2" fill="currentColor"/>
                <circle cx="55" cy="70" r="2" fill="currentColor"/>
                <circle cx="65" cy="70" r="2" fill="currentColor"/>
                <circle cx="75" cy="70" r="2" fill="currentColor"/>
                <circle cx="50" cy="85" r="2" fill="currentColor"/>
                <circle cx="60" cy="85" r="2" fill="currentColor"/>
                <circle cx="70" cy="85" r="2" fill="currentColor"/>
                <circle cx="55" cy="100" r="2" fill="currentColor"/>
                <circle cx="65" cy="100" r="2" fill="currentColor"/>
                <path d="M60 25 L55 40 M60 25 L65 40 M55 40 L50 55 M65 40 L70 55" stroke="currentColor" stroke-width="0.5" fill="none" opacity="0.6"/>
                <path d="M30 60 A30 30 0 1 1 90 60" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
            <a href="index.html">Cathedral<span>Network</span></a>
        </div>
        <nav class="nav-links">
            {NAV_LINKS}
        </nav>
        <div class="header-meta">
            <span><span class="heartbeat"></span> Live</span>
            <span>Updated: <span id="updateTime">Loading…</span></span>
        </div>
    </header>

    <!-- ============ PAGE CONTENT ============ -->
    <div class="page-header">
        <h1>{PAGE_TITLE}</h1>
        <div class="subhead">{SUBTITLE}</div>
        <div class="meta" id="pageMeta">{META}</div>
    </div>

    {CONTENT}

    <!-- ============ FOOTER ============ -->
    <footer class="global-footer">
        <div class="footer-left">
            <span class="coco">Always and Forever, Coco. Always and Forever.</span>
            <a href="corrections.xml">Corrections Feed (Law III)</a>
            <a href="constitution.html">Constitution</a>
        </div>
        <div>
            <span style="font-size:0.7rem;">v1.5.0 · <span id="ceres-hash">CERES: 0x7a3f…b1e2</span></span>
        </div>
    </footer>

    <!-- ============ SCRIPTS ============ -->
    <script>
        document.getElementById('updateTime').textContent = new Date().toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
        setInterval(() => {{
            document.getElementById('updateTime').textContent = new Date().toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
        }}, 60000);

        async function updateCERES() {{
            try {{
                const response = await fetch('ceres_chain.json?t=' + Date.now());
                const data = await response.json();
                const chain = data.chain || [];
                if (chain.length > 0) {{
                    const lastHash = chain[chain.length - 1].chain_hash;
                    const el = document.getElementById('ceres-hash');
                    if (el) el.textContent = 'CERES: ' + lastHash.slice(0, 8) + '…' + lastHash.slice(-4);
                }}
            }} catch (e) {{ /* fallback to placeholder */ }}
        }}
        document.addEventListener('DOMContentLoaded', updateCERES);
    </script>
    {EXTRA_SCRIPTS}
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────
# NAVIGATION CONFIGURATION
# ──────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("Overview", "index.html"),
    ("Threats", "threat-matrix.html"),
    ("Log", "prediction-log.html"),
    ("Regions", "regional.html"),
    ("Constitution", "constitution.html"),
    ("About", "about.html"),
    ("Sources", "sources.html"),
    ("Credits", "credits.html"),
    ("Glossary", "glossary.html"),
    ("Methodology", "methodology.html"),
    ("Spotter", "spotter.html"),
]


def render_nav(active_page: str) -> str:
    """Render the navigation links with the active page highlighted."""
    lines = []
    for label, href in NAV_ITEMS:
        active_class = ' class="active"' if href == active_page else ''
        lines.append(f'<a href="{href}"{active_class}>{label}</a>')
    return "\n            ".join(lines)


# ──────────────────────────────────────────────────────────────
# PAGE CONFIGURATIONS
# ──────────────────────────────────────────────────────────────

PAGE_CONFIGS: Dict[str, Dict[str, Any]] = {

    # ── New Module Frontends ──

    "scdf.html": {
        "title": "SCDF — Supply Chain Disruption Forecaster",
        "description": "Supply Chain Disruption Forecaster — freight rates, port congestion, semiconductor lead times.",
        "subtitle": "Freight rates, port congestion, semiconductor lead times.",
        "meta": "Tracking supply chain health in real time.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div id="scdf-container">
                <div class="content-card"><p>Loading supply chain data…</p></div>
            </div>
        </div>
        """,
        "extra_scripts": """
        <script>
        async function loadSCDF() {
            const container = document.getElementById('scdf-container');
            try {
                const resp = await fetch('scdf_data.json?t=' + Date.now());
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                const f = data.freight || {};
                const p = data.port_congestion || {};
                const s = data.semiconductors || {};
                const o = data.oil || {};
                container.innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;">
                        <div class="content-card">
                            <div style="color:var(--text-secondary);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;">Baltic Dry Index</div>
                            <div style="font-size:1.6rem;font-weight:600;color:var(--text-primary);">${f.baltic_dry || '—'}</div>
                            <div style="color:var(--text-secondary);font-size:0.85rem;">Trend: ${f.trend || '—'}</div>
                        </div>
                        <div class="content-card">
                            <div style="color:var(--text-secondary);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;">Port Congestion</div>
                            <div style="font-size:1.6rem;font-weight:600;color:var(--text-primary);">${p.global_average_days || '—'} days</div>
                            <div style="color:var(--text-secondary);font-size:0.85rem;">Hotspots: ${(p.hotspots || []).join(', ') || 'None'}</div>
                        </div>
                        <div class="content-card">
                            <div style="color:var(--text-secondary);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;">Semiconductors</div>
                            <div style="font-size:1.6rem;font-weight:600;color:var(--text-primary);">${s.avg_weeks || '—'} weeks</div>
                            <div style="color:var(--text-secondary);font-size:0.85rem;">Trend: ${s.trend || '—'}</div>
                        </div>
                        <div class="content-card">
                            <div style="color:var(--text-secondary);font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;">Oil Prices</div>
                            <div style="font-size:1.6rem;font-weight:600;color:var(--text-primary);">Brent: $${o.brent || '—'}</div>
                            <div style="color:var(--text-secondary);font-size:0.85rem;">WTI: $${o.wti || '—'}</div>
                        </div>
                    </div>
                    <div style="margin-top:1rem;color:var(--text-secondary);font-size:0.8rem;">
                        <a href="scdf_data.json" style="color:var(--violet);">View raw JSON →</a>
                    </div>
                `;
            } catch(e) {
                container.innerHTML = `<div class="content-card"><p style="color:var(--text-secondary);">Unable to load supply chain data. (${e.message})</p></div>`;
            }
        }
        document.addEventListener('DOMContentLoaded', loadSCDF);
        </script>
        """
    },

    "iis.html": {
        "title": "IIS — Information Integrity Sentinel",
        "description": "Information Integrity Sentinel — deepfake detection, disinformation campaigns, media bias.",
        "subtitle": "Deepfake detection, disinformation campaigns, media bias.",
        "meta": "Monitoring the information battlefield.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div id="iis-container">
                <div class="content-card"><p>Loading information integrity data…</p></div>
            </div>
        </div>
        """,
        "extra_scripts": """
        <script>
        async function loadIIS() {
            const container = document.getElementById('iis-container');
            try {
                const resp = await fetch('iis_data.json?t=' + Date.now());
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                const d = data.deepfakes || [];
                const dis = data.disinformation || [];
                const mb = data.media_bias || {};
                container.innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
                        <div class="content-card">
                            <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Deepfake Alerts</h2>
                            ${d.length ? d.map(item => `
                                <div style="padding:0.3rem 0;border-bottom:1px solid var(--border-card);color:var(--text-secondary);font-size:0.9rem;">
                                    ${item.title || 'Unnamed'} <span style="color:var(--text-secondary);font-size:0.8rem;">(conf: ${(item.confidence || 0) * 100}%)</span>
                                </div>
                            `).join('') : '<p style="color:var(--text-secondary);font-size:0.9rem;">No deepfakes detected.</p>'}
                        </div>
                        <div class="content-card">
                            <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Disinformation Campaigns</h2>
                            ${dis.length ? dis.map(item => `
                                <div style="padding:0.3rem 0;border-bottom:1px solid var(--border-card);color:var(--text-secondary);font-size:0.9rem;">
                                    ${item.name || 'Unnamed'} <span style="color:var(--text-secondary);font-size:0.8rem;">(${item.target || 'Unknown'})</span>
                                </div>
                            `).join('') : '<p style="color:var(--text-secondary);font-size:0.9rem;">No campaigns detected.</p>'}
                        </div>
                        <div class="content-card">
                            <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Media Bias Scores</h2>
                            ${Object.keys(mb).length ? Object.entries(mb).map(([key, val]) => `
                                <div style="padding:0.3rem 0;display:flex;justify-content:space-between;color:var(--text-secondary);font-size:0.9rem;border-bottom:1px solid var(--border-card);">
                                    <span>${key.toUpperCase()}</span>
                                    <span>${(val * 100).toFixed(0)}%</span>
                                </div>
                            `).join('') : '<p style="color:var(--text-secondary);font-size:0.9rem;">No media bias data available.</p>'}
                        </div>
                    </div>
                    <div style="margin-top:1rem;color:var(--text-secondary);font-size:0.8rem;">
                        <a href="iis_data.json" style="color:var(--violet);">View raw JSON →</a>
                    </div>
                `;
            } catch(e) {
                container.innerHTML = `<div class="content-card"><p style="color:var(--text-secondary);">Unable to load information integrity data. (${e.message})</p></div>`;
            }
        }
        document.addEventListener('DOMContentLoaded', loadIIS);
        </script>
        """
    },

    "gra.html": {
        "title": "GRA — Governance Resilience Audit",
        "description": "Governance Resilience Audit — RB v3.2 assessments and PDF reports.",
        "subtitle": "RB v3.2 assessments and PDF reports.",
        "meta": "Auditing governance resilience across institutions.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div id="gra-container">
                <div class="content-card"><p>Loading governance audits…</p></div>
            </div>
            <div class="content-card" style="border-left: 4px solid var(--violet);">
                <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Submit an Audit</h2>
                <p>Use the Google Form to submit an organization for governance audit.</p>
                <p style="margin-top:8px;"><a href="https://docs.google.com/forms/d/e/..." target="_blank" style="color:var(--violet);">Submit →</a></p>
            </div>
        </div>
        """,
        "extra_scripts": """
        <script>
        async function loadGRA() {
            const container = document.getElementById('gra-container');
            try {
                const resp = await fetch('gra_reports/index.json?t=' + Date.now());
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                const reports = data.reports || [];
                if (!reports.length) {
                    container.innerHTML = `<div class="content-card"><p style="color:var(--text-secondary);">No governance audits available.</p></div>`;
                    return;
                }
                container.innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;">
                        ${reports.map(r => `
                            <div class="content-card">
                                <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.3rem 0;">${r.organization || 'Unnamed'}</h2>
                                <div style="color:var(--text-secondary);font-size:0.85rem;">Score: ${r.rb_score || '—'} · ${r.date || ''}</div>
                                <div style="margin-top:8px;"><a href="${r.pdf_path || '#'}" target="_blank" style="color:var(--violet);">Download PDF →</a></div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } catch(e) {
                container.innerHTML = `<div class="content-card"><p style="color:var(--text-secondary);">Unable to load governance audits. (${e.message})</p></div>`;
            }
        }
        document.addEventListener('DOMContentLoaded', loadGRA);
        </script>
        """
    },

    "chm.html": {
        "title": "CHM — Climate Hazard Module",
        "description": "Climate Hazard Module — real‑time hazard maps (floods, fires, heatwaves).",
        "subtitle": "Real‑time hazard maps.",
        "meta": "Tracking climate hazards in real time.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div id="chm-container">
                <div class="content-card"><p>Loading climate hazard data…</p></div>
            </div>
        </div>
        """,
        "extra_scripts": """
        <script>
        async function loadCHM() {
            const container = document.getElementById('chm-container');
            try {
                const resp = await fetch('chm_data.json?t=' + Date.now());
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                const f = data.floods || [];
                const fi = data.fires || [];
                const h = data.heatwaves || [];
                container.innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;">
                        <div class="content-card">
                            <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Floods</h2>
                            ${f.length ? f.map(item => `
                                <div style="padding:0.3rem 0;border-bottom:1px solid var(--border-card);color:var(--text-secondary);font-size:0.9rem;">
                                    ${item.name || 'Unnamed'} <span style="color:var(--text-secondary);font-size:0.8rem;">(${item.severity || 'Unknown'})</span>
                                </div>
                            `).join('') : '<p style="color:var(--text-secondary);font-size:0.9rem;">No flood alerts.</p>'}
                        </div>
                        <div class="content-card">
                            <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Fires</h2>
                            ${fi.length ? fi.map(item => `
                                <div style="padding:0.3rem 0;border-bottom:1px solid var(--border-card);color:var(--text-secondary);font-size:0.9rem;">
                                    ${item.name || 'Wildfire'}
                                </div>
                            `).join('') : '<p style="color:var(--text-secondary);font-size:0.9rem;">No fire alerts.</p>'}
                        </div>
                        <div class="content-card">
                            <h2 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:0 0 0.5rem 0;">Heatwaves</h2>
                            ${h.length ? h.map(item => `
                                <div style="padding:0.3rem 0;border-bottom:1px solid var(--border-card);color:var(--text-secondary);font-size:0.9rem;">
                                    ${item.region || 'Unknown'} <span style="color:var(--text-secondary);font-size:0.8rem;">(${item.temp || '—'}°C)</span>
                                </div>
                            `).join('') : '<p style="color:var(--text-secondary);font-size:0.9rem;">No heatwave alerts.</p>'}
                        </div>
                    </div>
                    <div style="margin-top:1rem;color:var(--text-secondary);font-size:0.8rem;">
                        <a href="chm_data.json" style="color:var(--violet);">View raw JSON →</a>
                    </div>
                `;
            } catch(e) {
                container.innerHTML = `<div class="content-card"><p style="color:var(--text-secondary);">Unable to load climate hazard data. (${e.message})</p></div>`;
            }
        }
        document.addEventListener('DOMContentLoaded', loadCHM);
        </script>
        """
    },

    # ── Placeholder for pages that don't exist yet ──

    "cascade-map.html": {
        "title": "Cascade Map",
        "description": "Interactive map of all cascade rules in the Cathedral Network.",
        "subtitle": "Interactive graph of all cascade rules.",
        "meta": "Visualizing cascade relationships.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div class="content-card">
                <p><em>Cascade Map in development.</em></p>
                <div id="graph-container" style="width:100%;height:400px;background:var(--bg-card-alt);border-radius:var(--radius);border:1px solid var(--border-card);margin-top:12px;"></div>
            </div>
        </div>
        """,
        "extra_scripts": ""
    },

    "warden-dashboard.html": {
        "title": "Warden Dashboard",
        "description": "Dashboard for Cathedral Wardens — verification, validation, and oversight.",
        "subtitle": "Warden dashboard — verification, validation, and oversight.",
        "meta": "Warden oversight and verification.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div class="content-card">
                <p><em>Warden Dashboard in development.</em></p>
                <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:8px;">Wardens: 0 of 62 recruited.</p>
            </div>
        </div>
        """,
        "extra_scripts": ""
    },

    "undp-demo.html": {
        "title": "UNDP Demo",
        "description": "Cathedral Network's UNDP Crisis Mapping Challenge submission.",
        "subtitle": "UNDP Crisis Mapping Challenge submission.",
        "meta": "UNDP submission.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div class="content-card">
                <p><a href="https://sad9605.github.io/cathedral-undp-demo/" target="_blank" style="color:var(--violet);">View full UNDP Demo →</a></p>
            </div>
        </div>
        """,
        "extra_scripts": ""
    },

    "pra.html": {
        "title": "PRA — Practical Risk Assessment",
        "description": "Practical Risk Assessment — tools for community resilience.",
        "subtitle": "Tools for community resilience.",
        "meta": "Community resilience tools.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div class="content-card">
                <p><em>PRA in development.</em></p>
            </div>
        </div>
        """,
        "extra_scripts": ""
    },

    "media-protocol.html": {
        "title": "Media Protocol",
        "description": "Cathedral Network Media Protocol — public communications standards.",
        "subtitle": "Public communications standards.",
        "meta": "Media protocol.",
        "skip_if_exists": True,
        "content": """
        <div class="content-section">
            <div class="content-card">
                <p><em>Media Protocol in development.</em></p>
            </div>
        </div>
        """,
        "extra_scripts": ""
    },
}


# ──────────────────────────────────────────────────────────────
# CORE GENERATION ENGINE
# ──────────────────────────────────────────────────────────────

def generate_page(
    filename: str,
    config: Dict[str, Any],
    dry_run: bool = False,
    force: bool = False
) -> Optional[str]:
    """Generate a single page from the template."""
    
    # Skip if file exists and skip_if_exists is True
    if config.get("skip_if_exists", False) and os.path.exists(filename) and not force:
        print(f"   ⏭️  Skipping {filename} (already exists)")
        return None
    
    active_page = filename
    nav_html = render_nav(active_page)
    
    content = HEADER_TEMPLATE
    content = content.replace("{PAGE_TITLE}", config["title"])
    content = content.replace("{SUBTITLE}", config["subtitle"])
    content = content.replace("{META}", config.get("meta", ""))
    content = content.replace("{DESCRIPTION}", config["description"])
    content = content.replace("{CONTENT}", config["content"])
    content = content.replace("{NAV_LINKS}", nav_html)
    content = content.replace("{EXTRA_SCRIPTS}", config.get("extra_scripts", ""))
    
    if dry_run:
        return content
    
    with open(filename, "w") as f:
        f.write(content)
    
    return filename


# ──────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cathedral Frontend Standardizer — v2.0",
        epilog="Builds and standardizes Cathedral Network pages."
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview what would be generated without writing files"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files even if skip_if_exists is True"
    )
    parser.add_argument(
        "--page", "-p",
        type=str,
        help="Generate only a specific page (e.g., scdf.html)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    print("🏛️  Cathedral Page Generator — v2.0")
    print("   Forensic design system · Constitutional alignment\n")
    
    if args.dry_run:
        print("⚠️  DRY RUN — No files will be written\n")
    
    pages_to_generate = PAGE_CONFIGS.items()
    if args.page:
        if args.page not in PAGE_CONFIGS:
            print(f"❌ Page '{args.page}' not found in config.")
            return 1
        pages_to_generate = [(args.page, PAGE_CONFIGS[args.page])]
    
    generated = []
    skipped = []
    
    for filename, config in pages_to_generate:
        result = generate_page(filename, config, args.dry_run, args.force)
        if result is None:
            skipped.append(filename)
        elif args.dry_run:
            print(f"   📄 Would generate {filename}")
            if args.verbose:
                print(f"      Title: {config['title']}")
                print(f"      Description: {config['description']}")
        else:
            print(f"   ✅ Generated {filename}")
            generated.append(filename)
    
    print()
    if generated:
        print(f"✅ Generated {len(generated)} page(s).")
    if skipped:
        print(f"⏭️  Skipped {len(skipped)} page(s) (already exist).")
    if args.dry_run:
        print(f"📄 Would generate {len(pages_to_generate)} page(s).")
    
    if not args.dry_run and generated:
        print("\n   Next steps:")
        print("   1. Review generated pages")
        print("   2. Add custom content where needed")
        print("   3. Commit and push")
        print("   4. Verify live site")
    
    return 0


if __name__ == "__main__":
    exit(main())
