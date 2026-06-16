#!/usr/bin/env python3
"""
Simple state tracker for Agentic Warden – prevents duplicate actions
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

class StateTracker:
    def __init__(self, state_path: str = "logs/warden_state.json"):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self):
        with open(self.state_path, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

    def already_acted(self, trigger: str, context: dict, cooldown_hours: int = 24) -> bool:
        """Returns True if this trigger+key has been acted on within cooldown period"""
        # Create a unique key from trigger + relevant context fields
        key = trigger
        if "report_id" in context:
            key += f"_{context['report_id']}"
        elif "threat_id" in context:
            key += f"_{context['threat_id']}"
        elif "timestamp" in context:
            # For daily triggers, use the date only, not the full timestamp
            date = context['timestamp'][:10] if isinstance(context['timestamp'], str) else str(context['timestamp'])[:10]
            key += f"_{date}"
        else:
            key += "_once"  # only act once ever

        if key not in self.data:
            return False

        last_acted = datetime.fromisoformat(self.data[key])
        now = datetime.now(timezone.utc)
        if now - last_acted < timedelta(hours=cooldown_hours):
            return True
        return False

    def mark_acted(self, trigger: str, context: dict):
        key = trigger
        if "report_id" in context:
            key += f"_{context['report_id']}"
        elif "threat_id" in context:
            key += f"_{context['threat_id']}"
        elif "timestamp" in context:
            date = context['timestamp'][:10] if isinstance(context['timestamp'], str) else str(context['timestamp'])[:10]
            key += f"_{date}"
        else:
            key += "_once"
        self.data[key] = datetime.now(timezone.utc).isoformat()
        self._save()
