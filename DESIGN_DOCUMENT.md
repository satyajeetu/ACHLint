# ACHLint Design Document

## Purpose

This document describes the current technical design of ACHLint as implemented in the repository. It reflects the MVP architecture today, not an aspirational future-state platform.

## System Summary

ACHLint is a single-process Streamlit application with a small domain package, `achlint`, that handles parsing, validation, ACH file construction, formatting helpers, and reporting. The app has two main user-facing workflows:

- generate an ACH file from a strict CSV plus originator settings
- validate an existing ACH file

There is no database, background job system, or external API integration in the current design. All processing happens in-memory during a user session.

## Architecture

### Presentation Layer

File: [app.py](/Users/satyajeetu/Desktop/ACHLint/app.py)

Responsibilities:

- renders the landing, generate, validate, results, and help pages
- stores workflow state in Streamlit session state
- manages the step-based generation wizard
- invokes parsing, build, validation, and reporting functions
- presents grouped issues and downloadable artifacts

Important UI patterns:

- single-page app behavior via `st.session_state["page"]`
- multi-step generate wizard via `st.session_state["generate_step"]`
- latest run persisted in `st.session_state["latest_result"]`
- originator settings persisted only for the current session

### Domain Layer

Files:

- [achlint/models.py](/Users/satyajeetu/Desktop/ACHLint/achlint/models.py)
- [achlint/csv_parser.py](/Users/satyajeetu/Desktop/ACHLint/achlint/csv_parser.py)
- [achlint/nacha_builder.py](/Users/satyajeetu/Desktop/ACHLint/achlint/nacha_builder.py)
- [achlint/nacha_validator.py](/Users/satyajeetu/Desktop/ACHLint/achlint/nacha_validator.py)
- [achlint/report_builder.py](/Users/satyajeetu/Desktop/ACHLint/achlint/report_builder.py)
- [achlint/routing.py](/Users/satyajeetu/Desktop/ACHLint/achlint/routing.py)
- [achlint/formatter.py](/Users/satyajeetu/Desktop/ACHLint/achlint/formatter.py)
- [achlint/holidays.py](/Users/satyajeetu/Desktop/ACHLint/achlint/holidays.py)
- [achlint/csv_template.py](/Users/satyajeetu/Desktop/ACHLint/achlint/csv_template.py)
- [achlint/copy.py](/Users/satyajeetu/Desktop/ACHLint/achlint/copy.py)

The package is organized around pure or mostly pure functions, with dataclasses used for structured inputs, summaries, and outputs.

## Data Model

### `ValidationIssue`

Represents a single validation or advisory finding. It is used consistently across CSV parsing, ACH generation checks, and ACH validation. This unified issue model enables the UI, CSV export, and PDF report to share the same issue data structure.

Key fields:

- `code`
- `message`
- `severity`
- `field`
- `row_number`
- `line_number`
- `original_value`
- `suggested_fix`

### `PaymentRowInput`

Represents one parsed CSV payment row after normalization and basic type conversion.

### `OriginatorConfig`

Represents the ACH originator and header configuration required to construct the file and batch headers.

### `BuildSummary`, `BuildResult`, `ValidationResult`

These objects carry summary metrics, issues, statuses, and generated artifacts back to the UI.

## Generate Workflow Design

### Step 1: Parse CSV

File: [achlint/csv_parser.py](/Users/satyajeetu/Desktop/ACHLint/achlint/csv_parser.py)

`parse_payment_csv()`:

- decodes uploaded bytes as UTF-8 with BOM support
- enforces a strict header contract
- rejects unknown columns in strict mode
- validates each row for required values and supported account types
- validates routing numbers with ABA check-digit logic
- parses amount values into decimals
- parses optional per-row effective dates
- detects duplicate rows using a row signature

Design note:

The parser returns both `rows` and `issues`, which allows partial row parsing while still surfacing problems. Invalid amount rows are excluded from the final parsed row list.

### Step 2: Validate Originator Configuration

File: [achlint/nacha_builder.py](/Users/satyajeetu/Desktop/ACHLint/achlint/nacha_builder.py)

`validate_originator_config()` checks:

- required configuration fields
- business-day validity for the effective entry date
- validity of immediate destination and origin routing numbers
- length and numeric constraints for originating DFI identification
- file ID modifier format

### Step 3: Validate Row-Level Build Constraints

`validate_rows()` adds ACH-generation-specific checks and warnings, including:

- recipient name normalization warnings
- post-normalization recipient name length constraints
- warnings when row-level effective dates are present but ignored

### Step 4: Construct NACHA Records

`build_file()` builds the ACH text in this order:

1. file header
2. batch header
3. entry detail records
4. batch control
5. file control
6. all-9 padding records

Each record builder asserts:

- exact 94-character length
- ASCII-only output

Current design assumptions:

- one batch only
- service class `220`
- SEC code `PPD`
- debit totals fixed to zero
- transaction codes limited to `22` and `32` for checking/savings credits

### Step 5: Self-Validation of Generated Output

File: [app.py](/Users/satyajeetu/Desktop/ACHLint/app.py)

`handle_generate()` re-validates the generated ACH text with `validate_ach()` before exposing the file to the user. If validation introduces errors, the generated ACH text is cleared and the run is marked failed.

This is an important design choice: generation is not considered complete until the output also passes the validator.

### Step 6: Artifact Generation

File: [achlint/report_builder.py](/Users/satyajeetu/Desktop/ACHLint/achlint/report_builder.py)

The app generates:

- exceptions CSV from all issues
- PDF summary report using ReportLab

These artifacts are built for both generation and validation flows.

## Validate Workflow Design

### ACH Structural Validation

File: [achlint/nacha_validator.py](/Users/satyajeetu/Desktop/ACHLint/achlint/nacha_validator.py)

`validate_ach()` performs structural checks over the uploaded ACH content, including:

- empty file detection
- per-line 94-character enforcement
- ASCII-only enforcement
- required file header, batch header, batch control, and file control presence
- record order validation
- service class validation
- SEC code validation
- supported transaction code validation
- entry count reconciliation
- entry hash reconciliation
- debit and credit total reconciliation
- block count validation
- multiple-of-10 padding validation
- all-9 padding placement validation
- ascending trace number validation

Status mapping:

- `fail` if any error-severity issues exist
- `pass_with_warnings` if only warnings exist
- `pass` if no issues exist

In the current implementation, most validator issues are error-severity by default.

## Reporting and User Communication

### UI Copy

File: [achlint/copy.py](/Users/satyajeetu/Desktop/ACHLint/achlint/copy.py)

The copy layer centralizes tone and issue presentation. This helps the product stay consistent in how it frames blocking issues, warnings, and next steps.

### Issue Rendering

File: [app.py](/Users/satyajeetu/Desktop/ACHLint/app.py)

Issues are grouped by severity and rendered into operator-friendly tables. The same issue model also powers downloadable CSV and PDF outputs, reducing translation logic between backend and UI layers.

## Key Design Decisions

### 1. Intentionally Narrow Product Scope

The code and UI explicitly position the app as:

- PPD only
- credits only
- one batch per file

This keeps the builder and validator simpler and helps the product make a narrower but more reliable promise.

### 2. Functional Core with Thin UI Orchestration

Most domain logic lives in standalone functions and dataclasses. This makes the backend easier to test and reason about than if the logic were embedded directly in Streamlit callbacks.

### 3. Shared Issue Contract Across Flows

Using `ValidationIssue` everywhere is one of the cleaner design choices in the codebase. It standardizes how problems are captured, displayed, exported, and reported.

### 4. Validation Before ACH Download

The generate flow validates both inputs and generated output before treating the run as successful. This creates a safer workflow for users and aligns with the product promise.

## Constraints and Known Boundaries

Current implementation boundaries include:

- no persistence beyond Streamlit session state
- no user accounts or role-based access
- no direct bank integrations
- no support for multi-batch files
- no support for debit entries
- no support for SEC classes beyond PPD
- no external NACHA rule engine or bank-specific profiles
- no asynchronous processing for large files

## Testing

File: [tests/test_achlint.py](/Users/satyajeetu/Desktop/ACHLint/tests/test_achlint.py)

The test suite currently covers:

- ABA routing validation
- formatting helpers
- holiday logic
- CSV-to-ACH happy path
- record-length checks
- entry hash calculation
- invalid CSV header handling
- invalid ACH line length handling

The tests provide a solid MVP smoke net, though broader edge-case coverage would likely be needed before expanding supported ACH functionality.

## Risks and Future Design Pressure

If the product expands, the current design will feel pressure in these areas:

- single-batch assumptions embedded in builder and validator logic
- default error severity behavior that may limit nuanced warning states
- Streamlit session-state coupling for more advanced workflows
- report generation and validation performance for larger files
- support for bank-specific requirements beyond the current generic checks

## Recommended Next Technical Evolutions

If ACHLint grows beyond the MVP, the cleanest next steps would likely be:

1. separate ACH rule profiles from the hardcoded MVP assumptions
2. add richer severity typing and issue categories
3. expand tests around control totals, record-order edge cases, and malformed files
4. isolate application services from Streamlit-specific state handling
5. introduce persistence for reusable originator profiles and audit history
