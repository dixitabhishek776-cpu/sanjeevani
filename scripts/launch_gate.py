#!/usr/bin/env python3
"""Final release gate. It intentionally blocks public launch until external approvals exist."""
import os, sys
required = {
    "CLINICAL_REVIEW_SIGNED": "independent clinical safety review",
    "SECURITY_REVIEW_SIGNED": "security/penetration review",
    "PRIVACY_LEGAL_REVIEW_SIGNED": "privacy/legal review",
    "HUMAN_ESCALATION_STAFFED": "staffed human escalation operation",
    "BACKUP_RESTORE_DRILL_PASSED": "successful restore drill",
    "STAGING_E2E_PASSED": "staging end-to-end suite",
    "SAFETY_BENCHMARK_PASSED": "safety benchmark",
}
failed = [f"{k}: {v}" for k,v in required.items() if os.getenv(k) != "1"]
if failed:
    print("PUBLIC_LAUNCH_BLOCKED")
    print("\n".join("- " + x for x in failed))
    sys.exit(2)
print("PUBLIC_LAUNCH_GATES_PASSED")
