#!/usr/bin/env python3
import subprocess
import logging

class ActionExecutor:
    def execute(self, action_name: str, context: dict):
        method = getattr(self, action_name, None)
        if not method:
            raise ValueError(f"Unknown action: {action_name}")
        logging.info(f"Executing: {action_name}")
        return method(context)

    def generate_daily_summary_markdown(self, context):
        result = subprocess.run(
            ["python3", "daily_sweep.py"],
            capture_output=True,
            text=True,
            cwd=".."
        )
        return {"success": result.returncode == 0}

    def flag_duplicate_report(self, context):
        logging.info(f"Flagging duplicate report: {context.get('report_id')}")
        return {"flagged": True}
class ActionRouter:
    '''Separation of Concerns: Routes instructions instead of monolithic tool calling.'''
    def route(self, intent: str):
        pass
