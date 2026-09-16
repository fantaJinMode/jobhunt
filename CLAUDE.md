# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

```bash
# Quick start (no API key required)
python -m jobhunt run --mock --scorer keyword

# Build profile from resume
python -m jobhunt profile --resume resume.pdf

# Run the full pipeline
python -m jobhunt run                    # build digest only
python -m jobhunt run --send             # build and email
python -m jobhunt run --limit 10         # cost guard while tuning
python -m jobhunt run --no-draft         # screen only, skip drafting

# Track applications
python -m jobhunt applied "greenhouse:stripe:5501001"
python -m jobhunt stats

# Tests (no network, no API key, no cost)
python -m pytest tests -q
python -m pytest tests/test_parsers.py -v         # just the parser suite
python -m pytest tests/test_llm.py::test_screen_splits_into_batches_of_the_configured_size -v
```

## Architecture

**Pipeline:** fetch → prefilter → screen → draft → digest → mail

The prefilter is **deterministic, free, and what keeps the LLM bill small**. Roughly 2000 raw postings → 40 candidates before a single token is spent. Everything runs in `cli.py:cmd_run()`.

### Two-stage LLM design

Cost lives in `llm.py`, deliberately lopsided:

- **screen**: batch ~8 jobs per call, JD truncated to ~1400 chars, cheapest model (e.g., Haiku, Groq)
- **draft**: one call per job, ~6000 chars of JD, best model (e.g., Sonnet), only for top ~5

Each stage can point at a different provider via `SCREEN_PROVIDER` / `DRAFT_PROVIDER`.

### Provider interface

`providers.py` defines one tiny interface, five backends:

```python
complete(model, system, user, max_tokens, json_mode) -> str
complete_document(model, prompt, pdf, max_tokens) -> str  # Anthropic + Gemini only
```

Adding a provider = one class with `complete()` + entry in `PROVIDERS` dict. Everything except Anthropic uses plain `requests`.

### ATS parsers

`fetch.py` keeps HTTP **out** of the parsers. Each `parse_*(slug, company, body)` takes already-decoded JSON and returns `list[Job]`. This is what makes `--mock` exercise the real code path instead of a parallel implementation.

**Quirks handled:**
- **Greenhouse**: `content` is HTML-entity-escaped HTML. Unescape before stripping tags and again after, or you ship `&amp;` into the prompt.
- **Lever**: `createdAt` is epoch **milliseconds**. Full JD split across `descriptionPlain` + `lists[].text` + `lists[].content` + `additionalPlain` — concatenate all four or you lose requirements section.
- **Ashby**: skip `isListed: false` (unpublished drafts).

### Dedupe and tracking

`seen.json` is both the dedupe index and the application tracker. A job shown once is never shown again. **Gitignored** — shipping one would break the first run for anyone who cloned the repo.

Job IDs: `{ats}:{slug}:{id}` — globally unique, so the same role posted on two boards is two rows.

### LLM JSON parsing

`llm.parse_json()` is deliberately forgiving. Models wrap JSON in fences, open with "Here is the JSON:", or return an object where you asked for an array. The parser strips fences, tries straight parse, then falls back to outermost bracketed span. See `tests/test_llm.py::test_parse_json_survives_real_model_habits` for the cases it handles.

## Configuration

**Tune `config.yaml:filters` first.** It is deterministic, free, and it is what keeps the LLM bill small.

Common gotcha: `"sde"` as a bare regex does **NOT** match "Software Development Engineer" — different words entirely. Use `\bsde\b` for the acronym **and** list the spelled-out variants separately. There's a test pinning this (`test_parsers.py`).

Provider precedence: stage-specific env var → global env var → built-in default.
```bash
LLM_PROVIDER=anthropic          # sets both stages
SCREEN_PROVIDER=groq            # override per stage
DRAFT_PROVIDER=anthropic
SCREEN_MODEL=claude-haiku-4-5-20251001
DRAFT_MODEL=claude-sonnet-5
```

## Test Coverage

No network, no API key, no cost. 77 tests covering:

- Each parser against fixtures in its **native** ATS shape
- The two expensive bugs: Lever's epoch-ms timestamps (fixtures dates are generated relative to *now*, never hardcoded, so they can't silently age past the freshness gate) and the `\bsde\b` regex
- Prefilter rejects planted junk: wrong seniority, wrong city, wrong function, stale posting, unlisted Ashby draft
- LLM layer with provider stubbed: batching splits at configured size, JD truncation applied before send, fenced/preamble/object-or-array JSON all parse, scores land on right job when returned out of order, failed batch warns and run continues, draft kit always has every key the digest renders

## GitHub Actions CI

`.github/workflows/daily.yml` runs at 06:00 IST weekdays. `seen.json` carried between runs with `actions/cache`, **not committed** — a `seen.json` in the repo would mark every job as already-seen for anyone who cloned it.

Secrets to set: `PROFILE_JSON`, `ANTHROPIC_API_KEY` (or `GEMINI_API_KEY`/`GROQ_API_KEY`), `SMTP_USER`/`SMTP_PASS`, `MAIL_TO`.

Trigger manually: Actions → *daily job digest* → *Run workflow*, with `dry_run` ticked to build digest artifact without emailing.

## Gotchas

1. **Never commit personal data**: `profile.json`, `seen.json`, `.env` all gitignored. CI gets `profile.json` from a secret.
2. **Gmail needs App Password**: Your normal password stops working once 2FA is on. Create one at https://myaccount.google.com/apppasswords.
3. **Freshness is a soft signal**: Boards often re-stamp `updated_at`, so `max_age_days` is a heuristic, not a promise.
4. **Use `--limit` while tuning**: A bad regex can run up a bill before you notice.
5. **Keyword scorer is dev-only**: It cannot tell a Staff role from a new-grad one and has no idea what words mean. Exists to prove the plumbing, never to build a digest you'd act on.
