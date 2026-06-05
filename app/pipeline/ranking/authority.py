"""Curated domain-authority map and PR-outlet allowlist.

Pragmatic stand-in for a live SEO/domain-authority API: hand-tiered scores in
the 0..1 range. ``is_pr_outlet`` marks dedicated PR/communications trade press,
which earns a small ranking bonus. Unknown domains get ``DEFAULT_AUTHORITY``.
"""

from __future__ import annotations

DEFAULT_AUTHORITY = 0.3

# domain -> (authority_score, is_pr_outlet)
DOMAIN_AUTHORITY: dict[str, tuple[float, bool]] = {
    # Tier 1 — wire services & dedicated PR trade press
    "prnewswire.com": (0.95, True),
    "businesswire.com": (0.95, True),
    "globenewswire.com": (0.90, True),
    "prweek.com": (0.92, True),
    "prdaily.com": (0.85, True),
    "bulldogreporter.com": (0.80, True),
    "provokemedia.com": (0.85, True),
    "holmesreport.com": (0.85, True),
    "ragan.com": (0.80, True),
    "cision.com": (0.82, True),
    "muckrack.com": (0.78, True),
    "odwyerpr.com": (0.78, True),
    "agilitypr.com": (0.72, True),
    # Tier 2 — major business / marketing press
    "forbes.com": (0.80, False),
    "adweek.com": (0.78, False),
    "marketingweek.com": (0.75, False),
    "adage.com": (0.78, False),
    "fastcompany.com": (0.76, False),
    "hbr.org": (0.82, False),
    "techcrunch.com": (0.80, False),
    "reuters.com": (0.88, False),
    "bloomberg.com": (0.88, False),
    "wsj.com": (0.90, False),
    "nytimes.com": (0.90, False),
    "theguardian.com": (0.85, False),
    "marketingdive.com": (0.72, False),
    "thedrum.com": (0.74, False),
}


def lookup(domain: str) -> tuple[float, bool]:
    """Return ``(authority_score, is_pr_outlet)`` for a domain."""
    domain = domain.lower()
    if domain in DOMAIN_AUTHORITY:
        return DOMAIN_AUTHORITY[domain]
    # Allow subdomains to inherit from their parent (e.g. blog.cision.com).
    for known, value in DOMAIN_AUTHORITY.items():
        if domain.endswith("." + known):
            return value
    return (DEFAULT_AUTHORITY, False)
