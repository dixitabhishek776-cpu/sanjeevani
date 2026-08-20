# V15 — Beta and Public Launch

## Launch sequence

1. Internal engineering environment
2. Staff-only safety testing
3. Closed beta with explicit informed consent
4. Safety/incident review after every severe event
5. Limited public rollout with feature flags
6. Gradual traffic expansion
7. Full launch only after all release gates remain green

## Required operational controls

- named incident commander/on-call owner
- staffed human escalation workflow
- documented crisis-resource verification schedule
- user support channel
- security disclosure process
- data-subject request process
- backup/restore owner
- model/prompt rollback procedure
- post-incident review process

## Final gate

Run:

`python scripts/launch_gate.py`

The script intentionally blocks public launch until the required external approvals and infrastructure tests are explicitly recorded.
