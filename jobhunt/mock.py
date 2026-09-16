"""Mock ATS payloads in each provider's exact native JSON shape.

These exercise the real parsers, so `--mock` tests everything except the
HTTP hop. Includes deliberate junk (wrong function, US-only remote, an
on-site city, a remote-sounding title in an on-site office, a stale posting,
an unlisted Ashby draft) so the filters have something to actually reject.

Dates are computed relative to *now*, never hardcoded. A fixture with a
hardcoded date silently ages past `max_age_days` and one day your demo
returns zero jobs for no visible reason. `_STALE` is the only old one, and
it is old on purpose.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .fetch import parse_greenhouse, parse_lever, parse_ashby, Job


def _ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _gh(days: int) -> str:
    """Greenhouse: ISO 8601 with an offset."""
    return _ago(days).strftime("%Y-%m-%dT%H:%M:%S-04:00")


def _lever(days: int) -> int:
    """Lever: epoch MILLISECONDS. Seconds here silently dates every posting
    to 1970 and the freshness filter eats the entire board."""
    return int(_ago(days).timestamp() * 1000)


def _ashby(days: int) -> str:
    return _ago(days).strftime("%Y-%m-%dT%H:%M:%S.000Z")


STALE_DAYS = 280   # comfortably past any sane max_age_days

_BACKEND_JD = """<p>We are building the control plane for our edge platform.</p>
<p><strong>What you'll do</strong></p><ul>
<li>Design and operate low-latency distributed services handling millions of RPS</li>
<li>Work in Go and Java across caching, routing and traffic-steering systems</li>
<li>Own reliability: on-call, incident response, capacity planning</li></ul>
<p><strong>What we look for</strong></p><ul>
<li>3+ years building backend systems at scale</li>
<li>Strong fundamentals in data structures, algorithms and networking (TCP/IP, HTTP, DNS)</li>
<li>Experience with Kubernetes and observability tooling</li></ul>"""

_FULLSTACK_JD = """<p>Own features end to end across our React/TypeScript web app and
Node services on AWS.</p><ul><li>5+ years shipping production web apps</li>
<li>React, TypeScript, Node, PostgreSQL</li><li>Stripe or similar billing integration a plus</li>
<li>Fully remote team across four continents</li></ul>"""

_FRONTEND_JD = """<p>Build delightful UI in React and TypeScript. Own our design
system, animations and accessibility work.</p>"""

GREENHOUSE = {
    "acme-edge": {"jobs": [
        # keeper: right level, remote, fresh
        {"id": 5501001, "title": "Senior Full Stack Engineer",
         "absolute_url": "https://boards.greenhouse.io/acme-edge/jobs/5501001",
         "location": {"name": "Remote"},
         "updated_at": _gh(2), "content": _FULLSTACK_JD},
        # junk: on-site office; "Distributed" in the title must not read as remote
        {"id": 5501002, "title": "Software Engineer II, Distributed Systems",
         "absolute_url": "https://boards.greenhouse.io/acme-edge/jobs/5501002",
         "location": {"name": "San Francisco, CA"},
         "updated_at": _gh(3), "content": _BACKEND_JD},
        # junk: wrong function
        {"id": 5501003, "title": "Enterprise Account Executive",
         "absolute_url": "https://boards.greenhouse.io/acme-edge/jobs/5501003",
         "location": {"name": "Remote"},
         "updated_at": _gh(4),
         "content": "<p>Own a $3M quota selling to CIOs.</p>"},
        # junk: remote, but only inside one country
        {"id": 5501004, "title": "Backend Engineer, Payments",
         "absolute_url": "https://boards.greenhouse.io/acme-edge/jobs/5501004",
         "location": {"name": "Remote - United States"},
         "updated_at": _gh(1), "content": _BACKEND_JD},
        # junk: would pass every other gate, but it is ancient
        {"id": 5501005, "title": "Senior Software Engineer, Platform",
         "absolute_url": "https://boards.greenhouse.io/acme-edge/jobs/5501005",
         "location": {"name": "Remote"},
         "updated_at": _gh(STALE_DAYS), "content": _BACKEND_JD},
    ]},
    "novapay": {"jobs": [
        # keeper: "SDE" spelled out — the bare regex "sde" would miss this
        {"id": 7702001, "title": "Software Development Engineer, Core Infra",
         "absolute_url": "https://boards.greenhouse.io/novapay/jobs/7702001",
         "location": {"name": "Remote - Worldwide"},
         "updated_at": _gh(1),
         "content": _BACKEND_JD + "<p>TypeScript, Kafka, Postgres. Async-first team.</p>"},
        # junk: right discipline now, wrong region
        {"id": 7702002, "title": "Frontend Engineer, Design Systems",
         "absolute_url": "https://boards.greenhouse.io/novapay/jobs/7702002",
         "location": {"name": "Remote (EMEA only)"},
         "updated_at": _gh(2), "content": _FRONTEND_JD},
    ]},
}

LEVER = {
    "quantstack": [
        # junk: on-site city, no workplaceType
        {"id": "a1b2c3d4-1111-4aaa-9999-000000000001",
         "text": "Backend Engineer (Go)",
         "hostedUrl": "https://jobs.lever.co/quantstack/a1b2c3d4-1111-4aaa-9999-000000000001",
         "applyUrl": "https://jobs.lever.co/quantstack/a1b2c3d4-1111-4aaa-9999-000000000001/apply",
         "categories": {"location": "Bangalore", "team": "Infrastructure",
                        "commitment": "Full-time"},
         "createdAt": _lever(2),
         "descriptionPlain": "We run a real-time market data pipeline in Go. "
                             "You will own ingestion, fan-out and the storage layer.",
         "lists": [{"text": "Requirements",
                    "content": "<li>2-5 years backend experience</li>"
                               "<li>Go or Java, strong CS fundamentals</li>"
                               "<li>Comfort with Kubernetes, gRPC, Kafka</li>"}],
         "additionalPlain": "We interview with one system design round and one "
                            "pair-programming round. No take-home."},
        # junk: management track
        {"id": "a1b2c3d4-1111-4aaa-9999-000000000002",
         "text": "Engineering Manager, Platform",
         "hostedUrl": "https://jobs.lever.co/quantstack/a1b2c3d4-1111-4aaa-9999-000000000002",
         "categories": {"location": "Remote", "team": "Platform",
                        "commitment": "Full-time"},
         "workplaceType": "remote",
         "createdAt": _lever(3),
         "descriptionPlain": "Lead a team of 8 engineers. 5+ years of people management required.",
         "lists": []},
        # keeper: blank location, but the workplaceType flag says remote
        {"id": "a1b2c3d4-1111-4aaa-9999-000000000003",
         "text": "Senior React Native Engineer",
         "hostedUrl": "https://jobs.lever.co/quantstack/a1b2c3d4-1111-4aaa-9999-000000000003",
         "categories": {"location": "", "team": "Mobile",
                        "commitment": "Full-time"},
         "workplaceType": "remote",
         "createdAt": _lever(1),
         "descriptionPlain": "Own our iOS and Android apps end to end: React Native, "
                             "TypeScript, RevenueCat subscriptions, app store releases.",
         "lists": [{"text": "Nice to have",
                    "content": "<li>Deep linking or mobile attribution background</li>"}]},
    ],
}

ASHBY = {
    "helioscale": {"jobs": [
        # keeper: remote anywhere, AI product work
        {"id": "9f8e7d6c-2222-4bbb-8888-000000000001",
         "title": "AI Engineer, Agents",
         "location": "Remote - Anywhere", "isRemote": True, "isListed": True,
         "jobUrl": "https://jobs.ashbyhq.com/helioscale/9f8e7d6c-2222-4bbb-8888-000000000001",
         "publishedAt": _ashby(1),
         "compensation": {"compensationTierSummary": "₹32L – ₹48L"},
         "descriptionPlain": "Build LLM-powered agents and the tool layer they call "
                             "(MCP servers, RAG over customer data, evals). "
                             "TypeScript or Python. 5+ years experience."},
        # junk: unlisted draft
        {"id": "9f8e7d6c-2222-4bbb-8888-000000000002",
         "title": "AI Engineer, Agents",
         "location": "Remote - Anywhere", "isRemote": True, "isListed": False,
         "jobUrl": "https://jobs.ashbyhq.com/helioscale/unlisted",
         "publishedAt": _ashby(1),
         "descriptionPlain": "Draft posting that should never surface."},
        # junk: wrong discipline
        {"id": "9f8e7d6c-2222-4bbb-8888-000000000003",
         "title": "Data Scientist, Growth",
         "location": "Remote", "isRemote": True, "isListed": True,
         "jobUrl": "https://jobs.ashbyhq.com/helioscale/9f8e7d6c-2222-4bbb-8888-000000000003",
         "publishedAt": _ashby(2),
         "descriptionHtml": "<p>Causal inference, experimentation, SQL &amp; Python.</p>"},
        # junk: location text says Remote, the board's flag says it is not
        {"id": "9f8e7d6c-2222-4bbb-8888-000000000004",
         "title": "Software Engineer, Product",
         "location": "Remote", "isRemote": False, "isListed": True,
         "jobUrl": "https://jobs.ashbyhq.com/helioscale/9f8e7d6c-2222-4bbb-8888-000000000004",
         "publishedAt": _ashby(2),
         "descriptionPlain": "Hybrid: three days a week in our Bengaluru office."},
    ]},
}


def fetch_all_mock(companies=None) -> list[Job]:
    jobs: list[Job] = []
    for slug, body in GREENHOUSE.items():
        jobs += parse_greenhouse(slug, slug.replace("-", " ").title(), body)
    for slug, body in LEVER.items():
        jobs += parse_lever(slug, slug.title(), body)
    for slug, body in ASHBY.items():
        jobs += parse_ashby(slug, slug.title(), body)
    print(f"  [mock] {len(jobs)} postings from {len(GREENHOUSE) + len(LEVER) + len(ASHBY)} boards")
    return jobs
