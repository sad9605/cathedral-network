#!/usr/bin/env python3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG = "logs/agentic_audit.json"

class AuditLogger:
    def __init__(self, log_path: str = AUDIT_LOG):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"AuditLogger initialized, writing to {self.log_path}")

    def log_action(self, trigger, action, risk_tier, context, result, approved_by):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "action",
            "trigger": trigger,
            "action": action,
            "risk_tier": risk_tier,
            "approved_by": approved_by,
            "result": str(result)[:500]
        }
        self._write_entry(entry)
        logging.info(f"Audit: {trigger} -> {action}")

    def log_event(self, event_type, details):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details
        }
        self._write_entry(entry)

    def log_error(self, trigger, action, error):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "error",
            "trigger": trigger,
            "action": action,
            "error": error
        }
        self._write_entry(entry)

    def _write_entry(self, entry):
        try:
            existing = []
            if self.log_path.exists():
                with open(self.log_path, 'r') as f:
                    existing = json.load(f)
            existing.append(entry)
            # Keep last 10,000
            if len(existing) > 10000:
                existing = existing[-10000:]
            with open(self.log_path, 'w') as f:
                json.dump(existing, f, indent=2, default=str)
            logging.debug(f"Wrote entry to {self.log_path}")
        except Exception as e:
            logging.error(f"Failed to write audit entry: {e}")
