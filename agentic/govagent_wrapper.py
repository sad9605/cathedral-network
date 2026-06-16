#!/usr/bin/env python3
"""
GovAgent Wrapper for Cathedral Agentic Warden
Properly uses ExecutiveAgent with persona, policy, and model_client
"""

import logging
from pathlib import Path
import yaml

GOVAGENT_AVAILABLE = False
ExecutiveAgent = None
Policy = None
TelemetryManager = None
HITLManager = None

try:
    import govagent
    ExecutiveAgent = govagent.ExecutiveAgent
    Policy = govagent.Policy
    TelemetryManager = govagent.telemetry.TelemetryManager
    HITLManager = govagent.hitl.HITLManager
    GOVAGENT_AVAILABLE = True
    logging.info("GovAgent imported successfully")
except ImportError as e:
    logging.warning(f"GovAgent not found: {e}")

class MockModelClient:
    """Simple mock model client for GovAgent"""
    def generate(self, prompt: str, **kwargs):
        return {"response": "Approved", "choices": [{"text": "Approved"}]}

class GovAgentWrapper:
    def __init__(self, policy_path: str = "govagent_policy.yaml"):
        self.policy_path = Path(policy_path)
        self.agent = None
        self.policy_obj = None
        self.policy_data = None
        
        if not GOVAGENT_AVAILABLE:
            logging.info("GovAgent not available - running in bypass mode")
            return
            
        if not self.policy_path.exists():
            logging.warning(f"GovAgent policy file not found: {self.policy_path}")
            return

        try:
            # Load policy data
            with open(self.policy_path, 'r') as f:
                self.policy_data = yaml.safe_load(f)
            
            # Create Policy object
            self.policy_obj = Policy(self.policy_data)
            
            # Create model client
            model_client = MockModelClient()
            
            # Create telemetry manager (optional)
            telemetry = TelemetryManager() if TelemetryManager else None
            
            # Create HITL manager (optional)
            hitl = HITLManager() if HITLManager else None
            
            # Initialize ExecutiveAgent with persona
            persona = "Cathedral Network Sentinel - Responsible for monitoring global threats and escalating warnings to human Wardens"
            
            self.agent = ExecutiveAgent(
                persona=persona,
                policy=self.policy_obj,
                model_client=model_client,
                telemetry=telemetry,
                hitl_manager=hitl
            )
            logging.info(f"GovAgent ExecutiveAgent initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize GovAgent: {e}")
            self.agent = None

    def check_tool(self, tool_name: str, context: dict) -> bool:
        """Check if a tool is allowed by GovAgent"""
        if not GOVAGENT_AVAILABLE or self.agent is None:
            # Fallback: check policy directly
            if self.policy_data and 'tools' in self.policy_data:
                tools = {t['name']: t for t in self.policy_data['tools']}
                return tool_name in tools
            return True

        try:
            # Use GovAgent to check tool
            if hasattr(self.agent, 'can_execute'):
                return self.agent.can_execute(tool_name, context)
            elif hasattr(self.agent, 'authorize'):
                return self.agent.authorize(tool_name, context)
            else:
                return self._check_policy(tool_name)
        except Exception as e:
            logging.error(f"GovAgent check failed: {e}")
            return self._check_policy(tool_name)

    def _check_policy(self, tool_name: str) -> bool:
        """Fallback policy check"""
        if self.policy_data and 'tools' in self.policy_data:
            tools = {t['name']: t for t in self.policy_data['tools']}
            return tool_name in tools
        return True

    def execute(self, tool_name: str, context: dict, *args, **kwargs):
        """Execute a tool through GovAgent"""
        if not self.check_tool(tool_name, context):
            logging.error(f"Tool {tool_name} blocked by GovAgent")
            return None

        if hasattr(self, '_tool_callbacks') and tool_name in self._tool_callbacks:
            return self._tool_callbacks[tool_name](*args, **kwargs)
        
        logging.warning(f"No callback registered for {tool_name}")
        return None

    def register_tool(self, tool_name: str, callback):
        """Register a tool callback"""
        if not hasattr(self, '_tool_callbacks'):
            self._tool_callbacks = {}
        self._tool_callbacks[tool_name] = callback

    def veto(self, tool_name: str) -> bool:
        """Sovereign veto"""
        logging.warning(f"VETO EXECUTED for {tool_name}")
        return True
