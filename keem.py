#!/usr/bin/env python3
"""
keem.py – Financial Module for Cathedral Network
Implements: Quarter-Kelly, IVF, Adaptive Slippage
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple

def kelly_fraction(prob_win: float, prob_market: float) -> float:
    """
    Quarter-Kelly Position Sizing
    f* = (edge / odds) * 0.25
    edge = P_ww - P_m
    odds = 1 - P_m
    """
    edge = prob_win - prob_market
    if edge <= 0:
        return 0.0
    odds = 1 - prob_market
    if odds <= 0:
        return 0.0
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
    if edge <= 0:
        return 0.0
    max_trade = market_depth * edge
    return min(trade_size, max_trade)

def risk_caps(position_size: float, bankroll: float, total_exposure: float) -> Dict:
    """
    Apply risk caps:
    - Max 2% per position
    - Max 5% total exposure (KEEM/CEEM)
    - Max 10% total (SEEM)
    """
    per_position_cap = bankroll * 0.02
    total_cap = bankroll * 0.05
    absolute_cap = bankroll * 0.10
    
    adjusted = min(position_size, per_position_cap, total_cap - total_exposure)
    
    return {
        'position_cap': per_position_cap,
        'total_cap': total_cap,
        'absolute_cap': absolute_cap,
        'adjusted_size': max(0, adjusted),
        'over_cap': adjusted < position_size
    }

def compute_odds(prob_market: float) -> float:
    """
    Compute decimal odds from market probability.
    """
    return 1.0 / max(0.01, prob_market) if prob_market > 0 else 100.0

def expected_value(prob_win: float, odds: float) -> float:
    """
    Expected value of a bet.
    EV = P_win * odds - (1 - P_win)
    """
    return prob_win * odds - (1 - prob_win)

def shannon_entropy(prob_win: float) -> float:
    """
    Shannon entropy (uncertainty measure).
    """
    if prob_win <= 0 or prob_win >= 1:
        return 0.0
    return -prob_win * math.log2(prob_win) - (1 - prob_win) * math.log2(1 - prob_win)

if __name__ == "__main__":
    # Test with sample data
    print("=== KEEM Financial Module ===\n")
    
    # Kelly fraction
    prob_win = 0.65
    prob_market = 0.50
    kelly = kelly_fraction(prob_win, prob_market)
    print(f"Quarter-Kelly: {kelly:.4f}")
    
    # IVF
    prices = [100, 102, 101, 103, 98, 99, 101]
    passed, iv = implied_volatility_filter(prices)
    print(f"IVF: {iv*100:.1f}% -> {'PASS' if passed else 'FAIL'}")
    
    # Adaptive slippage
    slippage = adaptive_slippage(1000, 50000, 0.02)
    print(f"Adaptive slippage limit: {slippage:.2f}")
    
    # Risk caps
    caps = risk_caps(1000, 50000, 2000)
    print(f"Risk caps: {caps}")
    
    # Expected value
    odds = compute_odds(prob_market)
    ev = expected_value(prob_win, odds)
    print(f"Expected value: {ev:.3f}")
    
    print("\n✅ KEEM module operational")
