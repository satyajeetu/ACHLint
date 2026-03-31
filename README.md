# ACHLint

ACHLint is a Streamlit app that converts a strict payments CSV into a PPD credits-only ACH/NACHA file and validates uploaded ACH files.

## CI/CD and hosting

This project is set up for:

- CI with GitHub Actions on every push to `main`/`master` and every pull request
- CD through Streamlit Community Cloud by connecting the GitHub repository and deploying `app.py`

Once this folder is pushed to GitHub, Streamlit can auto-deploy new commits from your selected branch after the CI checks pass.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Run tests

```bash
source .venv/bin/activate
pytest
```

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository for this project and push the code.
2. In Streamlit Community Cloud, choose `New app`.
3. Select the GitHub repo, branch, and set the main file path to `app.py`.
4. Deploy the app.

### Notes

- Python is pinned in `runtime.txt` for consistent local/CI/hosting behavior.
- App theme and server settings live in `.streamlit/config.toml`.
- If you add secrets later, store them in Streamlit Cloud secrets and keep local values in `.streamlit/secrets.toml`, which is ignored by git.
