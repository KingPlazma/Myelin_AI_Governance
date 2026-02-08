"""
MYELIN – Fairness Auditing Entry Point
This script runs a population-level fairness audit.
"""

from ensemble import FairnessEnsemble


def run_fairness_audit():

    # Ground truth labels
    y_true = [
        1, 1, 1, 1, 1, 1, 1, 1,
        0, 0, 0, 0, 0, 0, 0, 0
    ]

    # Model predictions (mixed outcomes for BOTH groups)
    y_pred = [
        # Group 0
        1, 1, 0, 1, 0, 1, 0, 1,

        # Group 1
        1, 0, 1, 0, 1, 0, 0, 0
    ]

    # Sensitive attribute (0 = privileged, 1 = unprivileged)
    sensitive = [
        0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 1, 1, 1, 1
    ]

    auditor = FairnessEnsemble("rules")

    report = auditor.run(
        y_true=y_true,
        y_pred=y_pred,
        sensitive=sensitive
    )

    return report


if __name__ == "__main__":
    print("\n=== MYELIN FAIRNESS AUDIT REPORT ===")
    print(run_fairness_audit())
