# GitHub Pages — DK MART

The repository root contains `index.html`, which is a static showcase page for DK MART.

## Enable GitHub Pages

1. Open the repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Select branch **main** and folder **/(root)**.
5. Click **Save**.
6. Open the Pages URL shown by GitHub.

## Important

GitHub Pages hosts the static showcase only. It does **not** execute the Flask application in `app.py`.

Deploy the Flask backend separately on a Python-capable host and then replace the `Live demo URL not configured yet` section in `index.html` with the real application URL.
