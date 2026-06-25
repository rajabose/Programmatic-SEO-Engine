#!/usr/bin/env python3
"""
quality_gate.py — Orchestrate all 6 content quality gates and route each page.

Routing:
  approved     — 0 gates failed
  review_queue — exactly 1 gate failed AND it is recoverable
  blocked      — 2+ gates failed OR any non-recoverable gate failed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from services import (
    eeat_enforcer,
    keyword_density,
    link_checker,
    rich_results_validator,
    seo_scorer,
    uniqueness_checker,
    word_count_check,
)


@dataclass
class GateCheck:
    name:        str
    passed:      bool
    message:     str
    recoverable: bool = True   # False = one failure alone triggers blocked


@dataclass
class GateResult:
    routing:          Literal['approved', 'review_queue', 'blocked']
    checks:           list[GateCheck] = field(default_factory=list)
    seo_score:        int   = 0
    uniqueness_score: float = 0.0
    word_count:       int   = 0

    def to_dict(self) -> dict:
        return {
            'routing':          self.routing,
            'seo_score':        self.seo_score,
            'uniqueness_score': round(self.uniqueness_score, 3),
            'word_count':       self.word_count,
            'checks': [
                {
                    'name':        c.name,
                    'passed':      c.passed,
                    'message':     c.message,
                    'recoverable': c.recoverable,
                }
                for c in self.checks
            ],
        }

    @property
    def failures(self) -> list[GateCheck]:
        return [c for c in self.checks if not c.passed]


class QualityGate:
    @staticmethod
    def run_all(
        html:         str,
        keyword:      str,
        product:      dict,
        docs_dir:     Path = Path('docs'),
        db_path:      Path = Path('db/seo_engine.db'),
        current_slug: str  = '',
    ) -> GateResult:
        checks: list[GateCheck] = []

        # ── 1. SEO Score ─────────────────────────────────────────────────────
        seo, _ = seo_scorer.score(html, keyword)
        checks.append(GateCheck(
            name='seo_score',
            passed=seo >= seo_scorer.THRESHOLD,
            message=f'SEO score {seo}/100 (need ≥{seo_scorer.THRESHOLD})',
            recoverable=True,
        ))

        # ── 2. Content Uniqueness ─────────────────────────────────────────────
        sim, similar_slug = uniqueness_checker.check(html, docs_dir, current_slug)
        sim_pct = round(sim * 100, 1)
        max_pct = int(uniqueness_checker.MAX_OVERLAP * 100)
        checks.append(GateCheck(
            name='uniqueness',
            passed=sim <= uniqueness_checker.MAX_OVERLAP,
            message=(
                f'{sim_pct}% overlap with "{similar_slug}" (max {max_pct}%)'
                if similar_slug else f'{sim_pct}% overlap (max {max_pct}%)'
            ),
            recoverable=True,
        ))

        # ── 3. Keyword Density ────────────────────────────────────────────────
        density, wc_raw = keyword_density.check(html, keyword)
        density_pct = round(density * 100, 1)
        max_pct_kd  = int(keyword_density.MAX_DENSITY * 100)
        checks.append(GateCheck(
            name='keyword_density',
            passed=density < keyword_density.MAX_DENSITY,
            message=f'Keyword density {density_pct}% (max {max_pct_kd}%)',
            recoverable=True,
        ))

        # ── 4. Word Count ─────────────────────────────────────────────────────
        wc, page_type, wc_passed = word_count_check.check(html)
        min_words = (word_count_check.TRANSACTIONAL_MIN
                     if page_type == 'transactional'
                     else word_count_check.INFORMATIONAL_MIN)
        checks.append(GateCheck(
            name='word_count',
            passed=wc_passed,
            message=f'{wc} words ({page_type}, need ≥{min_words})',
            recoverable=True,
        ))

        # ── 5. E-E-A-T Signals ────────────────────────────────────────────────
        eeat_ok, eeat_missing = eeat_enforcer.check(html)
        checks.append(GateCheck(
            name='eeat',
            passed=eeat_ok,
            message='E-E-A-T signals present' if eeat_ok else f'Missing: {"; ".join(eeat_missing)}',
            recoverable=True,
        ))

        # ── 6. Platform Link Liveness ─────────────────────────────────────────
        link_results, any_live = link_checker.check(html, db_path)
        has_urls = bool(link_results)
        live_count = sum(1 for r in link_results.values() if r['live'])
        checks.append(GateCheck(
            name='platform_links',
            passed=any_live or not has_urls,
            message=(
                'No platform URLs in page'          if not has_urls
                else f'{live_count}/{len(link_results)} platform links live'
            ),
            # Blocking only when URLs exist but none respond — page has nowhere to send traffic
            recoverable=not (has_urls and not any_live),
        ))

        # ── 7. Rich Results / JSON-LD Validation ──────────────────────────────
        rr_passed, rr_message = rich_results_validator.gate_check(html, current_slug)
        checks.append(GateCheck(
            name='rich_results',
            passed=rr_passed,
            message=rr_message,
            recoverable=True,  # Non-blocking by default; set STRICT_RICH_RESULTS=1 in CI for blocking
        ))

        # ── Routing ───────────────────────────────────────────────────────────
        failures = [c for c in checks if not c.passed]
        blocking  = [c for c in failures if not c.recoverable]

        if not failures:
            routing: Literal['approved', 'review_queue', 'blocked'] = 'approved'
        elif blocking or len(failures) > 1:
            routing = 'blocked'
        else:
            routing = 'review_queue'

        return GateResult(
            routing=routing,
            checks=checks,
            seo_score=seo,
            uniqueness_score=sim,
            word_count=wc,
        )
