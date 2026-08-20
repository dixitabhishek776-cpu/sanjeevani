from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
patterns=[re.compile(r'AKIA[0-9A-Z]{16}'),re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(r'''(?i)(?:password|secret|api[_-]?key)\s*[=:]\s*["'][^"']{16,}["']''')]
skip={'.git','node_modules','.next','__pycache__','.pytest_cache'}
errors=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or any(part in skip for part in p.parts): continue
    try: text=p.read_text(errors='ignore')
    except Exception: continue
    if any(x.search(text) for x in patterns): errors.append(str(p))
if errors:
    print('Potential secrets found:\n'+'\n'.join(sorted(set(errors))))
    sys.exit(1)
print('Secret scan passed')
