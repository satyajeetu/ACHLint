# ACHLint

ACHLint is a consumer-ready ACH utility for generating a strict PPD credits-only ACH/NACHA file from CSV input and validating uploaded ACH files.

## CI/CD and hosting

This project is set up for:

- CI with GitHub Actions on every push to `main`/`master` and every pull request
- CD through Netlify using the Next.js frontend in `web/`

The repository now has two app layers:

- `web/`: the Netlify-ready frontend built with Next.js, TypeScript, Tailwind CSS, and client-side ACH logic
- `app.py` + `achlint/`: the legacy Streamlit/Python implementation retained as a reference while the new frontend becomes the primary deployment target

Once this folder is pushed to GitHub, Netlify can auto-deploy new commits from your selected branch after the CI checks pass.

## Run the Netlify frontend locally

```bash
cd web
npm install
npm run dev
```

## Run frontend checks

```bash
cd web
npm run lint
npm run build
```

## Run the legacy Python app locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Run legacy Python tests

```bash
source .venv/bin/activate
pytest
```

## Deploy to Netlify

1. Push this repository to GitHub.
2. In Netlify, choose `Add new project` and import the GitHub repo.
3. Netlify will read `netlify.toml` and use:
   - Base directory: `web`
   - Build command: `npm run build`
4. Deploy the site.

### Recommended Netlify settings

- Production branch: `main`
- Node version: `22` (already pinned in `netlify.toml`)
- Build status checks: leave GitHub Actions enabled so Netlify deploys after frontend lint/build passes

### Notes

- The Netlify deployment target is the Next.js app in `web/`.
- ACH generation and validation now run client-side in the frontend, which makes the product deployable on Netlify without a separate backend.
- The old Streamlit app is still in the repo, but it is no longer the recommended hosting path.
