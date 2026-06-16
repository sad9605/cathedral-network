#!/usr/bin/env python3
"""
Agentic Warden with GovAgent integration
"""

import logging
import threading
import signal
import sys
from datetime import datetime, timezone, timedelta

from .policy import Policy
from .actions import ActionExecutor
from .escalation import EscalationHandler
from .audit import AuditLogger
from .state import StateTracker
from .govagent_wrapper import GovAgentWrapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AgenticWarden:
    def __init__(self, policy_path="config/agentic_policy.json", govagent_path="govagent_policy.yaml"):
        self.policy = Policy(policy_path)
        self.executor = ActionExecutor()
        self.escalation = EscalationHandler()
        self.audit = AuditLogger()
        self.state = StateTracker()
        self.govagent = GovAgentWrapper(govagent_path)
        self.active = True
        self.pending_escalations = {}
        logging.info("Agentic Warden initialized with GovAgent")

    def act_on_trigger(self, trigger: str, context: dict, cooldown_hours: int = 24):
        if not self.active:
            logging.warning("Warden inactive")
            return None

        if self.state.already_acted(trigger, context, cooldown_hours):
            logging.info(f"Skipping {trigger} – already acted within {cooldown_hours}h")
            return None

        mapping = self.policy.get_mapping(trigger)
        if not mapping:
            logging.debug(f"No mapping for {trigger}")
            return None

        action = mapping.get("action")
        risk_tier = mapping["risk_tier"]
        tier_config = self.policy.get_tier_config(risk_tier)

        self.state.mark_acted(trigger, context)

        # Check GovAgent first
        if not self.govagent.check_tool(action, {"scope": risk_tier.lower()}):
            self.audit.log_event("govagent_blocked", {"trigger": trigger, "action": action})
            logging.warning(f"GovAgent blocked {action} for {trigger}")
            return None

        if tier_config.get("requires_human", False):
            esc_id = self.escalation.escalate(trigger, action, context, risk_tier, 30)
            self.pending_escalations[esc_id] = {"trigger": trigger, "action": action}
            return None

        try:
            result = self.executor.execute(action, context)
            self.audit.log_action(trigger, action, risk_tier, context, result, "agentic")
            logging.info(f"Executed {action} autonomously")
            return result
        except Exception as e:
            logging.error(f"Action failed: {e}")
            self.audit.log_error(trigger, action, str(e))
            return None

    def revoke(self):
        self.active = False
        self.audit.log_event("revocation", {})
        self.escalation.broadcast_revocation()

    def vet(self, tool_name: str):
        """Sovereign veto – kill any tool execution"""
        return self.govagent.veto(tool_name)
