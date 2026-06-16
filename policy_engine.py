from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional

class CockpitPolicy(BaseModel):
    """
    v2.1.0 Cockpit Policy Engine (Python): Deterministic Business Rules.
    [REMEDIATION SCAFFOLD] Use this to replace LLM-based arithmetic or date logic.
    """
    
    @staticmethod
    def is_eligible_for_return(purchase_date: date, return_days_limit: int = 30) -> bool:
        """Deterministic date logic to prevent LLM approximation errors."""
        today = date.today()
        diff = today - purchase_date
        return diff.days <= return_days_limit

    @staticmethod
    def calculate_discount(total: float, promo_code: str) -> float:
        """Deterministic pricing logic."""
        if promo_code == 'COCKPIT20':
            return total * 0.8
        return total

# Example Usage:
# from policy_engine import CockpitPolicy
# if CockpitPolicy.is_eligible_for_return(date(2024, 1, 1)):
#     pass
