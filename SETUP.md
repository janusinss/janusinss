# Deploying Your Enhanced GitHub Profile README

## 1. Copy files into `janusinss/janusinss`
Unzip `janusinss-readme-kit.zip` and copy all files (`README.md`, `config.json`, `assets/`, `scripts/`, and `.github/`) into the root of your `janusinss/janusinss` repository, then push to `main`.

## 2. Enable Live Contribution & Commit Sync
1. Open your `janusinss/janusinss` repo on GitHub.
2. Go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**.
3. Go to **Actions → Update Profile README → Run workflow**.

Once the workflow completes, your dithered hero waveform, contribution total, per-repo commit-per-day curves, star counts, and `pushed` dates will automatically update from your live GitHub activity every day at 08:00 PHT (00:00 UTC).

## 3. Customize Repos & Links
Edit `config.json` to match your exact repository slugs (e.g., `skill-v2`, `FreshCart`, `reo-portal`) or add extra links—pushing a change to `config.json` automatically regenerates all SVGs.

*Tip: If you want private repository activity included in the contribution waveform, create a Personal Access Token with `read:user` and `repo` scopes and save it as a repository secret named `PROFILE_TOKEN`.*
