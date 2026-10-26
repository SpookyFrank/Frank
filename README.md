# Science Shorts Bot — zero-extra-cost starter

A working starter that makes a 720×1280 narrated fact-card MP4 from a curated science fact, uploads privately to YouTube, and optionally schedules public release two days later. **No ChatGPT Pro subscription required.** All footage is generated locally (original text cards), so no stock footage API or image generation credits are required.

## What it does / does not do

- Daily GitHub Actions schedule (08:00 Taiwan = 00:00 UTC; scheduling is best-effort).
- Deterministic daily topic from `data/facts.json`; six starter topics rotate, so **add original researched facts regularly** before monetization. No unsupported AI facts are automatically published.
- edge-tts English voice, with offline espeak-ng fallback; FFmpeg + Pillow make vertical video.
- Includes title/description/source citation on YouTube and date/fact marker for deduplication.
- Default is **render-only** if no YouTube token; **private upload** if token exists. To schedule public, manually set repository variable `PUBLISH_ENABLED=1`.
- Resumable upload, retry for transient errors, and search of latest 200 uploads to avoid most duplicate runs. This is not transactional exactly-once delivery; if API response is lost, check channel before manually rerunning.
- Does **not** provide full-motion AI generated video, word-synchronized captions, trending search, or guaranteed unattended publication. It produces readable on-screen fact text and voice.

## Prerequisites

Python 3.11, FFmpeg, FFprobe, and `espeak-ng` for offline voice fallback. On Ubuntu: `sudo apt install ffmpeg espeak-ng fonts-dejavu-core`.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m unittest discover -s tests
python main.py --day 2026-10-25
```

Open `output/2026-10-25/final.mp4`. If edge-tts cannot connect, espeak-ng must be installed. Voice service usage and rights should be checked before monetization.

## YouTube OAuth (manual first time)

1. Create a Google Cloud project; enable **YouTube Data API v3**.
2. Configure OAuth consent screen, choose appropriate audience, add your Google account as a test user if required.
3. Create an **OAuth client ID: Desktop app**. Download its JSON and rename it `client_secret.json` in project root. Never commit it.
4. Run `python auth_local.py` on **your own computer**; sign in to the Google account that manages the intended YouTube channel, verify the permissions, and approve. It creates `token.json` locally.
5. Add the **entire content** of `token.json` as repository Actions secret `YOUTUBE_TOKEN_JSON` under Settings → Secrets and variables → Actions. The secret contains a refresh token; treat it like a password.
6. Test locally: `python main.py --upload --day 2026-10-25` (uses local token.json). Check the YouTube Studio video is **private**.
7. Once your API project is authorized to publish and your output has been reviewed, create Actions repository **variable** `PUBLISH_ENABLED` with value `1`. Scheduled runs will then set `publishAt` two days in the future. Keep it unset to upload privately.

**Important:** An OAuth app in Testing mode may issue refresh tokens that expire after 7 days; for ongoing automation, configure an appropriate production consent status and comply with Google's verification requirements. YouTube may restrict videos uploaded by unverified API projects to private until the project passes an audit. The API cannot bypass that requirement. The channel owner must be eligible to create and operate the account.

## GitHub Actions

Create a **private** GitHub repository, upload these files, enable Actions, and run the workflow once using **Actions → Daily Science Shorts → Run workflow**. Scheduled workflow runs from the default branch. GitHub can delay or drop scheduled runs; monitor the workflow history. The script determines the day in Taiwan time.

Secrets (optional): `GEMINI_API_KEY` — optional AI rewrite request, but the reviewed narration remains unchanged unless `ALLOW_AI_REWRITE=1` is explicitly set; do not enable unreviewed AI rewriting for auto-publication. `YOUTUBE_TOKEN_JSON` — enables upload. Variable `PUBLISH_ENABLED=1` — enables future public scheduling.

**Note:** YouTube uploads consume significant API quota (`videos.insert`), and daily free quotas and rate limits can change. Verify your current quota in Google Cloud. If a quota is exceeded, the run fails rather than silently posting.

## Quality / safety checks before unattended publishing

- Review the initial private uploads, source URLs, pronunciation, font layout, and whether the voice/music usage complies with current terms.
- Curated facts are short, with source URLs for manual verification. Check them before publishing; URLs and facts can change. For science accuracy, a source link is not a substitute for fact checking.
- No copyrighted music or third-party footage is included. Add stock video only if its license allows your intended use and you retain attribution/rights evidence.
- YouTube policies on repetitious/inauthentic content and synthetic content disclosure apply. Repeated identical template videos may not qualify for monetization.
- Avoid enabling public scheduling until API audit status and account permissions are confirmed.
- If you lose or revoke the OAuth refresh token, re-run `auth_local.py` and replace the GitHub secret.
- For genuine exactly-once behavior across parallel workflows and crashes, use a durable transactional store; this sample has only recent-upload deduplication and a workflow concurrency lock.

## Free asset fallback

The built-in generated text card is the guaranteed no-stock-media fallback. To add visuals later, you may integrate Pexels or Pixabay with API keys and enforce per-asset license checks. This project intentionally does not depend on external media providers.

## Optional changes

- Add fresh verified facts to `data/facts.json` (unique `id`, `title`, `fact`, `source`, `keywords`).
- Edit the visual design in `bot/video.py`.
- To test private upload: `python main.py --upload`.
- To schedule: `PUBLISH_ENABLED=1 python main.py --upload --schedule` after confirming permission and review.
