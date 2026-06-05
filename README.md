# PR Social Publisher

A web app that, every morning, **discovers** interesting public-relations topics from
the web, **ranks** them by the prominence/authority of the source, drafts an
**AI-written caption + a matching stock photo**, and presents them in an in-app
**review queue**. Once you approve (and optionally edit) a post, it **publishes** to a
Facebook Page and Instagram.

## How it works

```
 ┌──────────┐   ┌───────────┐   ┌──────────────┐   ┌──────────┐   ┌───────────┐
 │ Ingest   │ → │ Rank by   │ → │ AI caption + │ → │ Review   │ → │ Publish   │
 │ (web/RSS)│   │ prominence│   │ stock image  │   │ queue UI │   │ (FB + IG) │
 └──────────┘   └───────────┘   └──────────────┘   └──────────┘   └───────────┘
```

Every external dependency sits behind a small interface with a **mock** implementation,
so the whole app runs end-to-end with **zero API keys**. Switch to real providers by
changing environment variables — no code changes for callers.

| Stage    | Default (keyless) | Real options (set env) |
|----------|-------------------|------------------------|
| Search   | `rss` (PR/news feeds) | `firecrawl`, `exa` |
| Caption  | `mock`            | `claude` (Anthropic) |
| Images   | `mock` (picsum)   | `unsplash`, `pexels` |
| Publish  | `mock`            | `meta` (Facebook Page + Instagram) |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # all-mock defaults; no keys needed
python scripts/seed.py        # optional: sample posts for an instant UI
uvicorn app.main:app --reload
```

Then:

- Open <http://localhost:8000/> — the **review queue**.
- `curl -X POST http://localhost:8000/jobs/run-daily` — manually run the daily pipeline
  (ingest → rank → caption → image). Returns counts; refresh the queue to see results.
- In the UI: edit a caption, swap the image, **Approve**, then **Publish**. The
  `MockPublisher` marks it `PUBLISHED` with a fake post id (see *Publish history* on the
  detail page).
- `GET /health` — health check.
- `pytest` — runs ranking, pipeline, and publish-transition tests.

## Going live

1. **AI captions:** set `CAPTION_PROVIDER=claude` and `ANTHROPIC_API_KEY`
   (model via `CLAUDE_MODEL`, default `claude-sonnet-4-5`).
2. **Stock images:** set `IMAGE_PROVIDER=unsplash` + `UNSPLASH_ACCESS_KEY`
   (or `pexels` + `PEXELS_API_KEY`). Photographer attribution is stored per their TOS.
3. **Publishing to Facebook + Instagram:** set `PUBLISHER=meta` and the `META_*` vars.
   This requires:
   - A Facebook **Page** and a long-lived **Page access token**.
   - An **Instagram Business/Creator account** linked to that Page.
   - A Meta App approved (App Review) for `pages_manage_posts`,
     `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`.
   - Instagram fetches the image server-side, so the selected image URL must be public.

   The Meta flow is implemented in `app/pipeline/publish/meta.py` (Facebook photo post,
   Instagram two-step container/publish) and is wired through the same `Publisher`
   interface as the mock.

## Scheduling

A background scheduler (APScheduler) runs the pipeline daily at `DAILY_RUN_HOUR`
(`TIMEZONE`). The populated queue **is** your morning digest; an email/Slack digest is a
straightforward later add-on.

## Project layout

```
app/
  main.py            FastAPI app + lifespan (DB init + scheduler)
  config.py          settings / provider selection / ranking weights
  db.py, models.py   SQLAlchemy engine + ORM (Source, Article, Suggestion, …)
  pipeline/          ingestion, ranking, caption, images, publish, orchestrator
  services/          suggestions (approve/edit/publish), scheduler
  web/               dashboard + ops routes, Jinja2 templates, static assets
scripts/seed.py      sample data
tests/               ranking, pipeline, publish tests
```

## Configuration reference

See `.env.example` for every supported variable, including ranking weights
(`RANK_W_*`), `MAX_DAILY_SUGGESTIONS`, and `MAX_ARTICLE_AGE_HOURS`.

## Notes

- The frontend loads **htmx** from a pinned CDN (see `app/templates/base.html`). To run
  fully offline, drop `htmx.min.js` into `app/static/` and point the `<script>` at it.
- Tests, lint (`ruff`), and the full discover → review → edit → approve → publish flow
  pass against the mock providers with no network or keys.
