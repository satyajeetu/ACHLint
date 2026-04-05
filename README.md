# ACHLint

ACHLint is a lightweight ACH file generator and validator for spreadsheet-driven payroll and payout teams.

It helps operators:
- convert a strict CSV into a PPD credits-only ACH/NACHA file
- validate an existing ACH file before bank upload
- catch blocking issues earlier with plain-language feedback
- download remediation artifacts such as an exceptions CSV and validation report

## Why this project exists

Most small teams do not need a full treasury platform. They need a reliable way to:

1. prepare payout data in a spreadsheet
2. turn it into a bank-ready ACH file
3. validate the result before upload

ACHLint is intentionally narrow so the workflow stays understandable and trustworthy.

## Product scope

Supported today:
- PPD credits only
- one batch per file
- CSV-in to ACH-out generation
- existing ACH file validation
- operator-friendly issue reporting

Not supported today:
- debits
- CCD, CTX, WEB, TEL, IAT
- bank integrations or SFTP push
- approval workflows
- multi-batch authoring

## Repository structure

- [web/](/Users/satyajeetu/Desktop/ACHLint/web): primary frontend, built with Next.js, TypeScript, and Tailwind CSS
- [achlint/](/Users/satyajeetu/Desktop/ACHLint/achlint): legacy Python ACH logic and reference implementation
- [app.py](/Users/satyajeetu/Desktop/ACHLint/app.py): legacy Streamlit app
- [.github/workflows/ci.yml](/Users/satyajeetu/Desktop/ACHLint/.github/workflows/ci.yml): CI checks
- [.github/workflows/deploy-github-pages.yml](/Users/satyajeetu/Desktop/ACHLint/.github/workflows/deploy-github-pages.yml): GitHub Pages deployment
- [netlify.toml](/Users/satyajeetu/Desktop/ACHLint/netlify.toml): Netlify deployment config

## Run locally

Frontend:

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

Frontend checks:

```bash
cd web
npm run lint
npm run build
```

Legacy Streamlit app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Legacy Python tests:

```bash
source .venv/bin/activate
pytest
```

## Deployment options

### GitHub Pages

This repo is already configured for GitHub Pages at:

- [https://satyajeetu.github.io/ACHLint/](https://satyajeetu.github.io/ACHLint/)

Setup:

1. Push the latest code to `main`
2. Open repository `Settings`
3. Go to `Pages`
4. Set `Source` to `GitHub Actions`
5. GitHub will run the Pages workflow automatically on each push to `main`

Notes:
- static export is configured in [web/next.config.ts](/Users/satyajeetu/Desktop/ACHLint/web/next.config.ts)
- the GitHub Pages base path is set to `/ACHLint/`
- if the repo name changes, update `repoName` in [web/next.config.ts](/Users/satyajeetu/Desktop/ACHLint/web/next.config.ts)

### Netlify

Setup:

1. Push this repository to GitHub
2. Import the repo into Netlify
3. Netlify will read [netlify.toml](/Users/satyajeetu/Desktop/ACHLint/netlify.toml) and use:
   - base directory: `web`
   - build command: `npm run build`

Recommended Netlify settings:
- production branch: `main`
- Node version: `22`

## CI/CD

This project includes:
- GitHub Actions CI on push and pull request
- GitHub Pages deployment workflow
- Netlify-compatible build configuration

## Current implementation note

The Next.js app in [web/](/Users/satyajeetu/Desktop/ACHLint/web) is the primary product surface now.

The old Streamlit/Python implementation remains in the repo as a reference and fallback implementation, but it is no longer the recommended hosting path.
