<p align="center">
  <img src="./web/public/achlint-mark.svg" alt="ACHLint mark" width="84" />
</p>

<p align="center">
  <img src="./web/public/achlint-logo.svg" alt="ACHLint logo" width="460" />
</p>

<h1 align="center">ACHLint</h1>

<p align="center">
  Generate ACH files from CSV and validate NACHA uploads before bank submission.
</p>

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
- [.github/workflows/ci.yml](/Users/satyajeetu/Desktop/ACHLint/.github/workflows/ci.yml): CI checks
- [.github/workflows/deploy-github-pages.yml](/Users/satyajeetu/Desktop/ACHLint/.github/workflows/deploy-github-pages.yml): GitHub Pages deployment

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

## CI/CD

This project includes:
- GitHub Actions CI on push and pull request
- GitHub Pages deployment workflow

The Next.js app in [web/](/Users/satyajeetu/Desktop/ACHLint/web) is the full product surface and the only supported hosting path in this repository.
