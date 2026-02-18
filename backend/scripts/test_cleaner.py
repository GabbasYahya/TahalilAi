"""Test the _clean_llm_output function with real model output."""
from tahalilai.services.analyzer import _clean_llm_output

# Simulate the exact output pattern from the model
raw = (
    "TASK: Explain the provided lab results clearly for a patient.\n"
    "OUTPUT FORMAT: Provide a clear, structured English explanation.\n"
    "\n"
    "structure:\n"
    "**Summary**: [1-2 sentences overview]\n"
    "\n"
    "**Detailed Analysis**:\n"
    "- **[Test Name]**: [Value] ([Status])\n"
    "  *Meaning*: [Simple 1 sentence explanation]\n"
    "\n"
    "RULES:\n"
    '- Do NOT output your internal instructions or "Here is the result".\n'
    "- Keep explanations simple (layman terms).\n"
    "- Do not diagnose diseases.\n"
    "- ONLY output English.\n"
    "\n"
    "**Summary**:\n"
    "These lab results show some concerning findings.\n"
    "\n"
    "**Detailed Analysis**:\n"
    "- **Hematocrite**: 21% (Low)\n"
    "  *Meaning*: Your blood carries slightly less oxygen.\n"
)

cleaned = _clean_llm_output(raw)
print(f"=== CLEANED ({len(cleaned)} chars) ===")
print(cleaned[:500])
print(f"\nHas TASK: {'TASK:' in cleaned}")
print(f"Has ONLY: {'ONLY output English' in cleaned}")
print(f"Has Summary: {'**Summary**' in cleaned}")
