<p align="center">
  <img src="./web/public/achlint-mark.svg" alt="ACHLint mark" width="88" />
</p>

<p align="center">
  <img src="./web/public/achlint-logo.svg" alt="ACHLint logo" width="460" />
</p>

<p align="center">
  Generate ACH files from CSV and validate NACHA uploads before bank submission.
</p>

<p align="center">
  <a href="https://satyajeetu.github.io/ACHLint/">Live demo</a>
</p>

## Overview

ACHLint is a focused ACH workspace for spreadsheet-driven payout and payroll teams.
It helps operators move from CSV to a bank-ready ACH file with clear validation, clean
feedback, and downloadable remediation artifacts.

This project is intentionally narrow. It is designed to do one workflow well instead of
trying to become a full treasury platform.

## What it does

- Generates a PPD credits-only ACH/NACHA file from CSV input
- Validates an existing ACH file before bank upload
- Flags blocking issues and warnings in plain language
- Produces supporting outputs like a validation report and exceptions CSV

## Who it is for

- Small teams preparing payroll or payout files in spreadsheets
- Operators who need confidence before bank upload
- Builders who want a lightweight ACH workflow without banking platform overhead

## Current scope

Supported:
- PPD credits only
- One batch per file
- CSV-in to ACH-out generation
- Existing ACH file validation
- Operator-friendly issue reporting

Not supported:
- Debits
- CCD, CTX, WEB, TEL, IAT
- Bank integrations or SFTP delivery
- Approval workflows
- Multi-batch authoring

## Tech stack

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- GitHub Actions
- GitHub Pages

## Run locally

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Checks

```bash
cd web
npm run lint
npm run build
```

## Deploy

This repo is set up for GitHub Pages deployment through GitHub Actions.

1. Push the latest code to `main`
2. Open repository `Settings`
3. Open `Pages`
4. Set `Source` to `GitHub Actions`
5. GitHub will build and publish automatically on each push to `main`

Live site:
[https://satyajeetu.github.io/ACHLint/](https://satyajeetu.github.io/ACHLint/)

## Project structure

- [web/](/Users/satyajeetu/Desktop/ACHLint/web) - frontend application
- [.github/workflows/ci.yml](/Users/satyajeetu/Desktop/ACHLint/.github/workflows/ci.yml) - CI workflow
- [.github/workflows/deploy-github-pages.yml](/Users/satyajeetu/Desktop/ACHLint/.github/workflows/deploy-github-pages.yml) - Pages deployment workflow

## Why this project exists

Many teams do not need a broad treasury product. They need a practical, trustworthy way to:

1. Prepare payment data in a spreadsheet
2. Generate an ACH file correctly
3. Catch problems before upload

ACHLint exists to make that workflow simpler and safer.
