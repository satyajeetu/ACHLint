from __future__ import annotations

from achlint.models import ValidationIssue


# ACHLint product voice:
# calm, competent, direct, slightly warm.
# Never hype-driven, never playful in failure states, and always action-oriented.


UI_COPY = {
    "landing_eyebrow": "ACH file generation without the guesswork",
    "landing_problem": (
        "When a bank rejects your ACH file, payroll and payout operations stall. "
        "The pressure is high, the rules are rigid, and most teams are still working from spreadsheets."
    ),
    "landing_title": "Turn your payment spreadsheet into a bank-accepted ACH file in minutes.",
    "landing_body": (
        "ACHLint gives operators a focused path from CSV to validated ACH output. "
        "Upload your payment file, review blocking issues before upload, and leave with an ACH file, "
        "a validation report, and an exceptions CSV."
    ),
    "landing_proof": "Built for spreadsheet-driven payroll and payouts. Focused scope. Validation before ACH download.",
    "landing_note": (
        "Start with guided setup if you are creating a new file. "
        "If you already have an ACH file, use Validate to understand what needs attention."
    ),
    "cta_primary": "Start guided setup",
    "cta_template": "Download CSV template",
    "cta_validate": "Validate an existing ACH",
    "tour_title": "First time using ACHLint?",
    "tour_body": (
        "You do not need to learn NACHA record structure to get started. "
        "Follow the guided path and ACHLint will show you what to review before you generate anything."
    ),
    "tour_start": "Start guided flow",
    "tour_hide": "Hide tutorial",
    "settings_saved": "Settings saved for this session. You can continue with the current values.",
    "validate_loading": "Reviewing your ACH file and checking for structural issues...",
    "generate_loading": "Generating your ACH file and preparing validation artifacts...",
    "results_pass_title": "Your file passed validation.",
    "results_pass_body": "Your artifacts are ready. You can move into your bank upload workflow with much more confidence.",
    "results_warning_title": "Your file passed core validation, with warnings to review.",
    "results_warning_body": "The file is structurally valid, but you should review the advisory notes before upload.",
    "results_fail_title": "This run has blocking issues.",
    "results_fail_body": (
        "Review the grouped issues below, fix the source data or file structure, "
        "and run validation again before uploading anything."
    ),
    "results_ready": "Ready for bank upload",
    "results_not_ready": "Not ready for bank upload",
    "results_no_issues": "No blocking issues were found in this run.",
}


ISSUE_TITLE_MAP = {
    "error": "Blocking issues",
    "warning": "Warnings to review",
    "info": "Helpful notes",
}


def issue_summary_copy(severity: str, count: int) -> str:
    if severity == "error":
        noun = "blocking issue" if count == 1 else "blocking issues"
        return f"We found {count} {noun}. Review them before this run can pass."
    if severity == "warning":
        noun = "warning" if count == 1 else "warnings"
        return f"We found {count} {noun}. The file may still be usable, but these items should be reviewed."
    noun = "note" if count == 1 else "notes"
    return f"We found {count} informational {noun}. These are provided for context."


def issue_impact_copy(issue: ValidationIssue) -> str:
    if issue.severity == "error":
        return "This blocks generation or validation pass status."
    if issue.severity == "warning":
        return "This does not block the run, but it should be reviewed before upload."
    return "This is informational and does not block the run."


def issue_next_step_copy(issue: ValidationIssue) -> str:
    if issue.suggested_fix:
        return issue.suggested_fix
    if issue.field:
        return f"Review the `{issue.field}` value and update the source data before running again."
    return "Review the source data or file structure, then run ACHLint again."


def issue_display_message(issue: ValidationIssue) -> str:
    return f"{issue.message} {issue_impact_copy(issue)}"
