# Game stats site

A public page showing your Brawl Stars trophies, Clash trophies, and TETR.IO TR. A GitHub Action refreshes the numbers every 15 minutes and republishes the site. Your API keys live in GitHub Secrets and never appear in the code.

## Setup (about 20 minutes)

**1. Get your API keys (Brawl Stars and Clash)**
- Brawl Stars: sign in at developer.brawlstars.com, create a key, and in "Allowed IP addresses" enter `45.79.218.79`.
- Clash Royale: same thing at developer.clashroyale.com (use developer.clashofclans.com for Clash of Clans).
- That IP belongs to RoyaleAPI's free proxy, which is what lets GitHub reach the official APIs. TETR.IO needs no key.

**2. Create a public repo and upload files**
- On GitHub, click **New repository**, set it to **Public**, and upload `index.html`, `style.css`, `app.js`, `stats.json`, `fetch_stats.py`, `config.json`, and `README.md` (select the files, not the folder).

**3. Add the automation file**
- Click **Add file → Create new file**, type `.github/workflows/stats.yml` as the name, paste in the contents of `stats-workflow.yml`, and commit.

**4. Add your keys as secrets**
- Go to **Settings → Secrets and variables → Actions → New repository secret**. Add `BRAWLSTARS_TOKEN` and `CLASH_TOKEN` with your two keys.

**5. Edit `config.json`**
- Set `brawl_stars_tag`, `clash_tag` (with the #), and `tetrio_username`. Use `"clash_kind": "clans"` if your Clash game is Clash of Clans.
- Optional: set `site_url` to your finished site address so a failed refresh keeps showing the last known number.

**6. Turn on Pages**
- **Settings → Pages → Source: GitHub Actions**. Then open **Actions → Update stats and deploy → Run workflow**. In a minute or two your site is live at `https://yourusername.github.io/reponame/`.

## Good to know
- Numbers refresh about every 15 minutes, sometimes later, since GitHub delays scheduled runs. The page itself rechecks every minute.
- Never paste a key into any file. If one leaks, delete it on the developer site and create a new one.
- GitHub can pause scheduled runs on a repo with no activity for 60 days. If the numbers stop updating, open the Actions tab and re-enable the workflow.
- The TETR.IO rating shows as unranked until you've played 10 league games.
