# ACHLint Product Summary

## Overview

ACHLint is a focused Streamlit application that helps operations teams turn a strict payments CSV into a NACHA/ACH file and validate ACH files before bank upload. The product is intentionally narrow: it supports PPD credit entries only, generates a single batch per file, and emphasizes pre-upload issue detection over broad ACH feature coverage.

## Problem

Many payroll and payout teams still manage payment instructions in spreadsheets. When an ACH file is rejected by a bank, the team often has little visibility into what went wrong, and resolving the issue can delay payroll or vendor payouts. ACHLint addresses that pain by providing a guided workflow, structural validation, and plain-language issue reporting.

## Target User

ACHLint is designed for spreadsheet-driven operators such as:

- payroll administrators at small and midsize companies
- finance or operations teams running recurring payouts
- internal teams that need basic ACH confidence checks without adopting a full treasury platform

These users typically care about speed, clarity, and bank acceptance more than advanced ACH customization.

## Core Value Proposition

ACHLint gives users a simple path from payment spreadsheet to ACH output while reducing the risk of preventable formatting or structural errors. It aims to make ACH generation feel operationally safe by:

- validating CSV inputs before generation
- validating generated ACH output before download
- explaining issues in operator-friendly language
- producing follow-up artifacts for remediation and auditability

## Primary User Flows

### 1. Generate Flow

Users upload a payment CSV, review parsed rows and issues, confirm originator settings, and generate ACH artifacts only after validation checks pass.

Key steps:

1. Upload payment CSV
2. Review CSV preview, row counts, totals, and issues
3. Confirm company and bank configuration
4. Generate ACH artifacts
5. Review final results and download outputs

### 2. Validate Flow

Users upload an existing ACH file to inspect whether the file structure matches ACHLint’s supported MVP constraints.

Key checks include:

- 94-character record lengths
- record ordering
- entry counts and totals
- entry hash
- block padding
- support for PPD credits-only files

## Inputs

### Payment CSV

Required columns:

- `name`
- `routing_number`
- `account_number`
- `account_type`
- `amount`

Optional columns:

- `id_number`
- `discretionary_data`
- `effective_date`

### Originator Settings

The generate flow also collects ACH header and batch configuration such as company name, company identification, routing numbers, effective entry date, file ID modifier, and originating DFI identification.

## Outputs

When generation succeeds, ACHLint can produce:

- ACH/NACHA file text
- validation report PDF
- exceptions CSV

When validation is run on an existing ACH file, ACHLint produces:

- validation result summary
- validation report PDF
- exceptions CSV

## Current MVP Scope

ACHLint currently supports:

- PPD SEC code
- credit transactions only
- checking and savings destination accounts
- one batch per file
- strict CSV schema enforcement
- single-session configuration in the Streamlit app

ACHLint does not currently position itself as a full ACH platform. It is best understood as a guided ACH generation and linting workspace for a narrow, high-confidence use case.

## Product Principles Reflected in the App

- Focused scope over broad feature claims
- Validation before download
- Plain-language issue communication
- Spreadsheet-first workflow
- Fast operator feedback with downloadable remediation artifacts

## Success Criteria

The product is successful when a user can:

1. upload payment data without needing NACHA expertise
2. identify blocking issues before bank submission
3. generate a structurally valid ACH file within the supported scope
4. leave with enough supporting artifacts to fix or explain exceptions quickly
