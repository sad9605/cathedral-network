#!/usr/bin/env python3
import logging
import threading
import time
import signal
import sys
from datetime import datetime, timezone, timedelta

from .policy import Policy
from .actions import ActionExecutor
from .escalation import EscalationHandler
from .audit import AuditLogger
from .state import StateTracker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AgenticWarden:
    def __init__(self, policy_path="config/agentic_policy.json", state_path="logs/warden_state.json"):
        self.policy = Policy(policy_path)
        self.executor = ActionExecutor()
        self.escalation = EscalationHandler()
        self.audit = AuditLogger()
        self.state = StateTracker(state_path)
        self.active = True
        self.pending_escalations = {}
        logging.info("Agentic Warden initialized with state tracking")

    def act_on_trigger(self, trigger: str, context: dict, cooldown_hours: int = 24):
        if not self.active:
            logging.warning("Warden inactive")
            return None

        # Check if already acted on this trigger within cooldown
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

        # Mark as acted BEFORE execution to prevent duplicate escalations
        self.state.mark_acted(trigger, context)

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
class ActionRouter:
    '''Separation of Concerns: Routes instructions instead of monolithic tool calling.'''
    def route(self, intent: str):
        pass
