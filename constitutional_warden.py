# constitutional_warden.py
import json, re, sys
from datetime import datetime

class ConstitutionalWarden:
    def __init__(self):
        self.violations = []
        self.passed = []

    def audit_conflict_data(self, path="conflict_data.json"):
        """Law I & Amendment I: Vulnerable prioritization check"""
        try:
            with open(path) as f:
                data = json.load(f)
            for c in data.get("conflicts", []):
                # Check for vulnerability weighting (Primary vs Secondary)
                if "vulnerability_score" not in c:
                    self.violations.append(f"LAW I/AMEND I: Conflict {c['id']} missing vulnerability weighting (Primary/Secondary/Tertiary)")
                if "population_density" not in c and c.get("intensity", 0) > 7:
                    self.violations.append(f"LAW IX: Conflict {c['id']} high intensity but no civilian proximity data (low-bandwidth warning flag)")
        except FileNotFoundError:
            self.violations.append("LAW I: conflict_data.json missing - cannot warn the vulnerable")

    def audit_daily_brief(self, path="daily-brief.html"):
        """Law III: Trust through accuracy (Sources, Confidence, Disclaimers)"""
        try:
            with open(path, "r") as f:
                html = f.read()
            # Check for confidence intervals
            if "confidence" not in html.lower() and "%" not in html:
                self.violations.append("LAW III: No confidence intervals or margins of error found in Daily Brief")
            # Check for source attribution
            if "source" not in html.lower() and "acled" not in html.lower() and "gdelt" not in html.lower():
                self.violations.append("LAW III: No explicit source citations found in Daily Brief")
            # Check for State Media disclaimer (Law III)
            if "state-owned" not in html.lower() and "disclaimer" not in html.lower():
                self.violations.append("LAW III: Missing 'State Media' disclaimer for state-sourced data")
            # Check for actionable guidance (Law IX)
            if "what to do" not in html.lower() and "action" not in html.lower():
                self.violations.append("LAW IX: Warning lacks actionable guidance for affected communities")
        except FileNotFoundError:
            self.violations.append("LAW III: daily-brief.html missing - public log empty")

    def audit_predictions(self, path="prediction_log.html"):
        """Law III & Amendment V: Immutable ledger + signatures"""
        try:
            with open(path, "r") as f:
                html = f.read()
            # Check for cryptographic signature placeholders (Amendment V)
            if "-----BEGIN SIGNATURE-----" not in html and "0x" not in html:
                self.violations.append("AMEND V: Prediction log entries missing cryptographic signatures (not immutable)")
            # Check for correction log (Law III)
            if "correction" not in html.lower() and "amended" not in html.lower():
                self.violations.append("LAW III: No correction/retraction history found in prediction log")
        except FileNotFoundError:
            self.violations.append("AMEND V: prediction_log.html missing - no audit trail")

    def audit_financial_firewall(self, path="cathedral_system.py"):
        """Law VII: Chinese Wall between financial and warning"""
        try:
            with open(path, "r") as f:
                code = f.read()
            # Check if financial fetchers are segregated
            if "yfinance" in code and "conflict" in code:
                if "FIREWALL_SEGREGATION" not in code:
                    self.violations.append("LAW VII: Financial and warning systems are mixed without explicit firewall isolation")
        except FileNotFoundError:
            pass # Skip if not applicable

    def run_all(self):
        print("🏛️  Constitutional Compliance Audit Running...")
        self.audit_conflict_data()
        self.audit_daily_brief()
        self.audit_predictions()
        self.audit_financial_firewall()

        if self.violations:
            print("\n❌ CONSTITUTIONAL VIOLATIONS FOUND:")
            for v in self.violations:
                print(f"  - {v}")
            # Fail the pipeline so we don't push non-compliant data
            sys.exit(1)
        else:
            print("\n✅ ALL CLEAR: Cathedral complies with all audited Constitutional Laws.")
            sys.exit(0)

if __name__ == "__main__":
    Warden = ConstitutionalWarden()
    Warden.run_all()
