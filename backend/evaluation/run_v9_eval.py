import json
from pathlib import Path
from app.agents.safety_agent import SafetyIntelligenceAgent, CONCERN_LEVELS

rank={v:i for i,v in enumerate(CONCERN_LEVELS)}
cases=json.loads(Path(__file__).with_name('safety_cases_v9.json').read_text())
agent=SafetyIntelligenceAgent()
results=[]
for c in cases:
    a=agent.assess(c['text'], emotion=None, recent_concern_levels=[])
    passed=rank[a.concern_level] >= rank[c['expected_min']]
    results.append((c['id'], a.concern_level, c['expected_min'], passed))
print(json.dumps([{'id':i,'actual':a,'expected_min':e,'passed':p} for i,a,e,p in results], indent=2))
print(f"passed={sum(x[3] for x in results)}/{len(results)}")
if not all(x[3] for x in results): raise SystemExit(1)
