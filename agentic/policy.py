#!/usr/bin/env python3
import json
import logging

class Policy:
    def __init__(self, policy_path: str):
        self.policy_path = policy_path
        self.data = self._load()
        logging.info(f"Policy loaded from {policy_path}")

    def _load(self):
        with open(self.policy_path, 'r') as f:
            return json.load(f)

    def get_tier_config(self, tier: str):
        for t in self.data["risk_tiers"]:
            if t["tier"] == tier:
                return t
        raise ValueError(f"Unknown tier: {tier}")

    def get_mapping(self, trigger: str):
        for m in self.data["trigger_mapping"]:
            if m["trigger"] == trigger:
                return m
        return None
