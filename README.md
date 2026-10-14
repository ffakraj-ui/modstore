MODSTORE – auto APK site (GitHub Pages)
=======================================
Files
  appteka_fetch.py   Appteka se data laata hai (token wale asli download links as-is)
  build.py           data -> HTML pages (layout fixed, sirf data print hota hai)
  assets/            style.css, site.js
  data/ids.json      saare app ids (yahi "database" hai, repo me commit hota hai)
  .github/workflows/update.yml    har 5 din auto: fetch -> build -> deploy
  .github/workflows/add-apps.yml  manual: naye apps add (Actions tab > Run workflow)

Setup
  1. Repo banao, ye sab push karo (.github folder bhi).
  2. Settings > Pages > Source = GitHub Actions.
  3. Settings > Secrets and variables > Actions > Variables: SITE_URL = https://tumhara-domain.com
     (bina custom domain ke khali chhod sakte ho).
  4. Actions > "Update site" > Run workflow (pehli baar).

Naye apps: Actions > "Add new apps" > Run workflow > index=apps, count=200.
Local test:
  python3 appteka_fetch.py --refresh && python3 build.py --domain https://x.com
  cd site && python3 -m http.server 8000
  
