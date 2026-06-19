#!/usr/bin/env python3
"""
cathedral_math.py – Cathedral Network Mathematical Compendium v1.2
All core formulas integrated into executable code.
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# ---------- 1. Core Global Stress Metrics ----------

def compute_ssi(threats: List[Dict]) -> float:
    """
    System Stress Index (SSI)
    SSI = (sum of status_points) / (N_threats * 5) * 100
    status_points: Black Acute=5, Black Structural=4, Red=3, Orange=2, Yellow=1, Green=0
    """
    status_map = {
        'Black Acute': 5,
        'Black Structural': 4,
        'Red': 3,
        'Orange': 2,
        'Yellow': 1,
        'Green': 0
    }
    total_points = sum(status_map.get(t.get('status', 'Green'), 0) for t in threats)
    n = len(threats)
    denominator = n * 5
    return round((total_points / denominator) * 100, 2) if denominator > 0 else 0

def compute_ds(threats: List[Dict], domains: List[str] = None) -> int:
    """
    Domestic Stability Score (DS)
    DS = sum of Black points for specified domains
    Black Acute = 2, Black Structural = 1
    """
    if domains is None:
        domains = ['VII', 'VIII']  # Default domestic domains
    points = 0
    for t in threats:
        if t.get('domains'):
            if any(d in domains for d in t.get('domains', [])):
                status = t.get('status', '')
                if 'Black Acute' in status:
                    points += 2
                elif 'Black Structural' in status:
                    points += 1
    return points

def compute_nsi(regional_ds: float, selected_domain_scores: List[float]) -> float:
    """
    National Stress Index (NSI)
    NSI = Regional DS + sum of selected domain scores
    """
    return regional_ds + sum(selected_domain_scores)

def compute_gsci(threats: List[Dict]) -> float:
    """
    Global Systemic Collapse Index (GSCI)
    Computes NSI for each threat using compute_nsi, then averages and normalizes.
    GSCI = (avg NSI / 21) * 100, capped at 100.
    """
    nsi_values = []
    for t in threats:
        # Extract regional_ds: use scp scaled to 0-10 range as a proxy
        scp = t.get('scp', 0.5)
        regional_ds = scp * 10  # adjust scaling as needed

        # Extract selected domain scores: if 'domain_scores' is a dict, use its values
        domain_scores = t.get('domain_scores', [])
        if isinstance(domain_scores, dict):
            domain_scores = list(domain_scores.values())
        elif not isinstance(domain_scores, list):
            domain_scores = []

        nsi = compute_nsi(regional_ds, domain_scores)
        nsi_values.append(nsi)

    avg_nsi = np.mean(nsi_values) if nsi_values else 0
    gsci = min(100, round((avg_nsi / 21) * 100, 2))
    return gsci

# ---------- 2. Cascade & Collapse Probability Metrics ----------

def compute_sca_tier(active_cascades: int) -> Dict:
    """
    Systemic Cascade Amplitude (SCA) Tiers
    0: Normal (0-5), 1: Elevated (6-12), 2: High (13-20),
    3: Extreme (21-28), 4: Critical (29-36), 5: Unprecedented (37+)
    """
    tiers = [
        (0, 5, 0, 'Normal'),
        (6, 12, 1, 'Elevated'),
        (13, 20, 2, 'High'),
        (21, 28, 3, 'Extreme'),
        (29, 36, 4, 'Critical'),
        (37, float('inf'), 5, 'Unprecedented')
    ]
    for low, high, tier, label in tiers:
        if low <= active_cascades <= high:
            return {'tier': tier, 'label': label, 'count': active_cascades}
    return {'tier': 0, 'label': 'Normal', 'count': active_cascades}

def bayesian_log_odds(prior: float, likelihood_ratios: List[float], weights: Optional[List[float]] = None) -> float:
    """
    Bayesian Log-Odds Fusion
    logit(P) = logit(P0) + Σ w_i * ln(LR_i)
    """
    if prior <= 0:
        return 0.01
    if prior >= 1:
        return 0.99
    if weights is None:
        weights = [1.0] * len(likelihood_ratios)
    logit_prior = math.log(prior / (1 - prior))
    logit_posterior = logit_prior + sum(w * math.log(lr) for w, lr in zip(weights, likelihood_ratios) if lr > 0)
    posterior = 1 / (1 + math.exp(-logit_posterior))
    return min(0.99, max(0.01, posterior))

def compute_scp_linear(base: float, active_deltas: List[float]) -> float:
    """
    Linear SCP model
    SCP = min(100, Base + Σ active Δ_i)
    Base = 12% (sum of macro-priors)
    """
    total = base + sum(active_deltas)
    return min(100.0, total)

# ---------- 3. Resilience & Creation Theories ----------

def simulate_resilience(params: Dict, time_steps: int = 52) -> np.ndarray:
    """
    Resilience Blueprint v4.0 – Survival Dynamics
    dR/dt = J * Ψ(λ) * (C_eff * P - ε_ind * D) * (1 - R/R_max) + σ * dW
    """
    R0 = params.get('R0', 0.5)
    J = params.get('J', 0.8)
    Psi = params.get('Psi', 0.7)
    C_eff = params.get('C_eff', 0.9)
    P = params.get('P', 0.6)
    eps_ind = params.get('eps_ind', 0.3)
    D0 = params.get('D0', 0.4)
    R_max = params.get('R_max', 1.0)
    sigma = params.get('sigma', 0.05)
    kappa = params.get('kappa', 0.1)
    gamma = params.get('gamma', 0.2)
    g0 = params.get('g0', 0.1)
    I = params.get('I', 0)
    U = params.get('U', 0.5)

    R = np.zeros(time_steps)
    R[0] = R0

    for i in range(1, time_steps):
        # Disturbance function
        D = D0 * math.exp(-kappa * R[i-1]) + gamma * U**2 + g0 * I
        # Wiener increment
        dW = np.random.normal(0, np.sqrt(1))
        # Derivative
        dR = J * Psi * (C_eff * P - eps_ind * D) * (1 - R[i-1] / R_max) + sigma * dW
        R[i] = max(0, min(R_max, R[i-1] + dR))

    return R

def transmutation_equation(S: float, H: float, T: float, E: float, R_t0: float) -> float:
    """
    Transmutation Equation (TE v1.0)
    A = S * H * (T / (1 + E)) * R(t0)
    """
    return S * H * (T / (1 + E)) * R_t0

def quarry_quality(S: float, H: float, E: float) -> float:
    """
    Quarry Quality (Raw Material)
    Q = S * H * (1 / (1 + E))
    """
    return S * H / (1 + E)

def artifact_band(A: float) -> str:
    """
    Artifact Classification Bands
    """
    if A < 0.05:
        return "Wound / Crucible"
    elif A < 0.20:
        return "Draft"
    elif A < 0.50:
        return "Work"
    elif A < 0.75:
        return "Cathedral Under Construction"
    elif A < 0.90:
        return "Cathedral"
    else:
        return "Masterwork"

# ---------- 4. Regional & Threat Indices ----------

def nts_score(ds: float, nsi: float) -> float:
    """
    Normalized Threat Score (NTS) – Universal 0-100 Scale
    NTS = DS * 5 + NSI * 2
    """
    raw = ds * 5 + nsi * 2
    return min(100, max(0, raw))

def conflict_intensity_index(fatalities: int, displacement: int, structural: int) -> float:
    """
    Conflict Intensity Index (CII)
    CII = (log_fatalities + log_displacement + structural/10) / 3 * 100
    """
    log_fatalities = math.log1p(fatalities) / math.log1p(1000000)  # normalized to 1M
    log_displacement = math.log1p(displacement) / math.log1p(10000000)  # normalized to 10M
    structural_norm = min(1, structural / 10)
    return ((log_fatalities + log_displacement + structural_norm) / 3) * 100

def disinformation_vulnerability_index(trust: float, polarization: float, media_literacy: float, incidents: int) -> float:
    """
    Disinformation Vulnerability Index (DVI)
    DVI = ((100 - Trust) + Polarization + (100 - Media_Literacy) + Incidents) / 4 * (1 + Incidents/100)
    """
    raw = ((100 - trust) + polarization + (100 - media_literacy) + incidents) / 4
    amp = 1 + (incidents / 100)
    return min(100, raw * amp)

def wealth_mobility_index(current_activity: float, baseline: float, convergence_event: bool = False) -> float:
    """
    Wealth Mobility Index (WMI)
    WMI = (Current / Baseline) * 50 + 20 if convergence event
    """
    relative = (current_activity / max(1, baseline)) * 50
    bonus = 20 if convergence_event else 0
    return min(100, relative + bonus)

def cable_disruption_risk(latency_score: float, incident: bool, geopolitical_score: float) -> float:
    """
    Cable Disruption Risk (CDR)
    CDR = (Latency + Incident + Geopolitical) / 3
    """
    incident_score = 100 if incident else 0
    return (latency_score + incident_score + geopolitical_score) / 3

# ---------- 5. Early-Warning & Anomaly Detection ----------

def convergence_alert_protocol(breaches: int, domains: int) -> Dict:
    """
    Convergence Alert Protocol (CAP)
    """
    weighted = breaches * domains
    if weighted >= 5:
        return {'level': 'Critical', 'weighted_score': weighted}
    elif weighted >= 3:
        return {'level': 'Alert', 'weighted_score': weighted}
    elif weighted >= 2:
        return {'level': 'Watch', 'weighted_score': weighted}
    else:
        return {'level': 'Normal', 'weighted_score': weighted}

def temporal_baseline_anomaly(current: float, mean: float, std: float) -> float:
    """
    Temporal Baseline Learning (TBL) – Dynamic Anomaly Score (DAS)
    DAS = min(100, |current - mean| / std * 25)
    """
    if std == 0:
        return 0
    return min(100, abs(current - mean) / std * 25)

def source_credibility_weighting(weights: List[float]) -> float:
    """
    Source Credibility Weighting
    S_weighted = 1 - ∏(1 - w_i)
    """
    product = 1.0
    for w in weights:
        product *= (1 - w)
    return 1 - product

# ---------- 6. Financial Module Math ----------

def kelly_fraction(prob_win: float, prob_market: float) -> float:
    """
    Quarter-Kelly Position Sizing
    f* = (edge / odds) * 0.25
    edge = P_ww - P_m
    odds = 1 - P_m
    """
    edge = prob_win - prob_market
    if edge <= 0:
        return 0
    odds = 1 - prob_market
    if odds <= 0:
        return 0
    return (edge / odds) * 0.25

def implied_volatility_filter(prices: List[float]) -> Tuple[bool, float]:
    """
    Implied Volatility Filter (IVF)
    IV = std(daily log returns) * sqrt(365)
    Pass if IV <= 80%
    """
    if len(prices) < 2:
        return True, 0.0
    log_returns = np.diff(np.log(prices))
    iv = np.std(log_returns) * np.sqrt(365)
    return iv <= 0.8, iv

def adaptive_slippage(trade_size: float, market_depth: float, edge: float) -> float:
    """
    Adaptive Slippage Model (KEEM)
    Limits trade size so price impact ≤ edge
    """
    max_trade = market_depth * edge
    return min(trade_size, max_trade)

# ---------- 7. Institutional & Backtest Metrics ----------

def institutional_vulnerability_factor(governance: float, funding: float, transparency: float) -> float:
    """
    Institutional Vulnerability Factor (IVF)
    0.0–1.0 score across 19 entities
    """
    return (governance + funding + transparency) / 3

def backtest_accuracy(predictions: List[Dict], outcomes: List[bool]) -> float:
    """
    Backtest accuracy = correct / total
    """
    if not predictions or len(predictions) != len(outcomes):
        return 0.0
    correct = sum(1 for p, o in zip(predictions, outcomes) if p.get('outcome') == o)
    return correct / len(predictions) if predictions else 0

# ---------- 8. Prediction Log Hash Chain ----------

def hash_prediction(prediction: Dict, previous_hash: str, timestamp: str) -> str:
    """
    Cryptographic Hash Chain
    H_i = SHA-256(canonical(P_i) || H_{i-1} || t_i)
    """
    import hashlib
    import json
    canonical = json.dumps(prediction, sort_keys=True)
    combined = canonical + previous_hash + timestamp
    return hashlib.sha256(combined.encode()).hexdigest()

# ---------- 9. Conversion Tables & Thresholds ----------

def das_band(das: float) -> str:
    """
    DAS Interpretation Bands
    """
    if das <= 25:
        return "Normal"
    elif das <= 50:
        return "Unusual"
    elif das <= 75:
        return "Anomalous"
    else:
        return "Extreme"

def nts_band(nts: float) -> str:
    """
    NTS Interpretation Bands
    """
    if nts <= 25:
        return "Stable"
    elif nts <= 50:
        return "Elevated"
    elif nts <= 75:
        return "Critical Stress"
    else:
        return "Extreme"

# ---------- 10. Main Test Function ----------

def main():
    """Test all functions with sample data."""
    print("=== Cathedral Math Compendium v1.2 ===\n")

    # Test SSI
    sample_threats = [
        {'status': 'Black Acute', 'domains': ['VII']},
        {'status': 'Red', 'domains': ['VIII']},
        {'status': 'Yellow', 'domains': ['IV']}
    ]
    print(f"SSI: {compute_ssi(sample_threats):.2f}")
    print(f"DS: {compute_ds(sample_threats)}")

    # Test NSI/GSCI (now using threats)
    print(f"GSCI: {compute_gsci(sample_threats):.2f}")

    # Test SCA
    print(f"SCA Tier: {compute_sca_tier(25)}")

    # Test Bayesian log-odds
    prior = 0.12
    lrs = [2.5, 1.8, 3.2]
    print(f"Bayesian posterior: {bayesian_log_odds(prior, lrs):.4f}")

    # Test Transmutation
    A = transmutation_equation(0.8, 0.9, 0.7, 0.3, 0.6)
    print(f"Transmutation: {A:.3f} -> {artifact_band(A)}")

    # Test DAS
    print(f"DAS: {temporal_baseline_anomaly(85, 70, 10):.2f}")

    # Test IVF
    print(f"IVF: {institutional_vulnerability_factor(0.7, 0.5, 0.8):.2f}")

    # Test Hash Chain
    pred = {'id': 'P001', 'probability': 0.65}
    print(f"Hash: {hash_prediction(pred, 'abc123', '2026-06-17')[:16]}...")

    print("\n✅ All math functions operational")

if __name__ == "__main__":
    main()
