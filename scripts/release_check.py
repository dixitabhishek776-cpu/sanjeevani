from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
errors=[]
for p in root.rglob('*'):
    if not p.is_file() or any(part in {'.git','.pytest_cache','__pycache__','node_modules','.next'} for part in p.parts): continue
    try: text=p.read_text(errors='ignore')
    except Exception: continue
    if re.search(r'sk-ant-[A-Za-z0-9_-]{20,}', text) or re.search(r'AKIA[0-9A-Z]{16}', text): errors.append(f'possible credential in {p.relative_to(root)}')
    if 'local-development-only-change-me' in text and p.name not in {'auth.py','release_check.py'}: errors.append(f'unsafe JWT default leaked into {p.relative_to(root)}')
if errors:
    raise SystemExit('\n'.join(errors))
print('release_check: PASS')
