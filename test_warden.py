from agentic.warden import AgenticWarden

# Initialize warden with policy
warden = AgenticWarden("agentic/config/agentic_policy.json")

# Test a Green trigger (autonomous, no human needed)
result = warden.act_on_trigger("daily_sweep_complete", {"timestamp": "2026-06-15"})

print(f"Result: {result}")
print("✅ Test complete")
