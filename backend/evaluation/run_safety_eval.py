import json, sys
from app.agents.safety_agent import SafetyIntelligenceAgent
from app.agents.emotion_agent import EmotionAnalysisAgent
# Keyword cases are deterministic; non-keyword cases require a configured LLM.
agent=SafetyIntelligenceAgent(); emotion=EmotionAnalysisAgent()
cases=json.load(open(__file__.replace('run_safety_eval.py','safety_cases.json')))
passed=0
for c in cases:
    try: got=agent.assess(c['text'],emotion.analyze(c['text']),[]).concern_level
    except Exception as e: got=f"ERROR:{type(e).__name__}"
    ok=got==c['expected']; passed+=ok
    print(f"{'PASS' if ok else 'FAIL'} {c['id']}: expected={c['expected']} got={got}")
print(f"\n{passed}/{len(cases)} deterministic/LLM cases matched")
sys.exit(0 if passed==len(cases) else 1)
