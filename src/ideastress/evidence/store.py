"""Evidence & Claim Store with deterministic Evidence Audit rules.

Enforces IdeaStress core rule:
  - Evidence and Claim are strictly separated entities.
  - No claim can remain VERIFIED without valid primary/secondary external evidence.
  - Contradicting evidence automatically flags CONTRADICTED.
  - User input alone can never masquerade as externally VERIFIED fact.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List
from urllib.parse import urlparse

from ideastress.domain.models import (
    AuditReport,
    Claim,
    ClaimStatus,
    Evidence,
    SourceReliability,
)


def compute_snippet_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def is_valid_http_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class EvidenceStore:
    """In-memory structured repository for evidences and linked claims."""

    def __init__(self) -> None:
        self._evidences: Dict[str, Evidence] = {}
        self._claims: Dict[str, Claim] = {}

    def add_evidence(self, evidence: Evidence) -> Evidence:
        if not evidence.content_hash:
            evidence.content_hash = compute_snippet_hash(evidence.snippet)
        self._evidences[evidence.evidence_id] = evidence
        return evidence

    def add_claim(self, claim: Claim) -> Claim:
        self._claims[claim.claim_id] = claim
        return claim

    def get_evidence(self, evidence_id: str) -> Evidence | None:
        return self._evidences.get(evidence_id)

    def all_evidences(self) -> List[Evidence]:
        return list(self._evidences.values())

    def all_claims(self) -> List[Claim]:
        return list(self._claims.values())

    def link_supporting(self, claim_id: str, evidence_id: str) -> None:
        claim = self._claims[claim_id]
        if evidence_id not in claim.supporting_evidence_ids:
            claim.supporting_evidence_ids.append(evidence_id)

    def link_contradicting(self, claim_id: str, evidence_id: str) -> None:
        claim = self._claims[claim_id]
        if evidence_id not in claim.contradicting_evidence_ids:
            claim.contradicting_evidence_ids.append(evidence_id)

    def audit_claims(self) -> AuditReport:
        """Deterministically audit all claims and downgrade unbacked VERIFIED claims."""
        downgraded = 0
        contradictions = 0
        verified_count = 0
        issues: List[str] = []

        for claim in self._claims.values():
            sup_evs = [
                self._evidences[eid]
                for eid in claim.supporting_evidence_ids
                if eid in self._evidences
            ]
            con_evs = [
                self._evidences[eid]
                for eid in claim.contradicting_evidence_ids
                if eid in self._evidences
            ]

            # Rule 1: Any contradicting evidence forces CONTRADICTED status
            if con_evs:
                contradictions += 1
                if claim.status != ClaimStatus.CONTRADICTED:
                    claim.status = ClaimStatus.CONTRADICTED
                    claim.confidence_label = "low"
                    claim.audit_notes.append(
                        f"Marked CONTRADICTED because {len(con_evs)} contradicting evidence item(s) exist."
                    )
                    downgraded += 1
                issues.append(f"Claim '{claim.claim_id}' has contradicting evidence.")
                continue

            # Rule 2: VERIFIED requires >=1 PRIMARY or SECONDARY external evidence with a valid URL
            if claim.status == ClaimStatus.VERIFIED:
                strong_external = [
                    e
                    for e in sup_evs
                    if e.source_reliability
                    in (SourceReliability.PRIMARY, SourceReliability.SECONDARY)
                    and is_valid_http_url(e.url)
                    and e.access_status == "success"
                ]
                if not strong_external:
                    if any(e.source_reliability == SourceReliability.USER_INPUT for e in sup_evs):
                        claim.status = ClaimStatus.ASSUMPTION
                        note = "Downgraded VERIFIED -> ASSUMPTION: user input cannot be labeled externally verified."
                    elif sup_evs:
                        claim.status = ClaimStatus.SUPPORTED
                        note = "Downgraded VERIFIED -> SUPPORTED: lacks primary/secondary source with verified URL."
                    else:
                        claim.status = ClaimStatus.UNKNOWN
                        note = "Downgraded VERIFIED -> UNKNOWN: no linked evidence found."
                    claim.confidence_label = "low"
                    claim.audit_notes.append(note)
                    issues.append(f"Claim '{claim.claim_id}': {note}")
                    downgraded += 1
                else:
                    verified_count += 1

            # Rule 3: SUPPORTED with zero evidence downgrades to ASSUMPTION
            elif claim.status == ClaimStatus.SUPPORTED and not sup_evs:
                claim.status = ClaimStatus.ASSUMPTION
                claim.confidence_label = "low"
                note = "Downgraded SUPPORTED -> ASSUMPTION: no linked evidence."
                claim.audit_notes.append(note)
                issues.append(f"Claim '{claim.claim_id}': {note}")
                downgraded += 1

        return AuditReport(
            passed=(downgraded == 0),
            total_claims=len(self._claims),
            verified_claims=verified_count,
            downgraded_claims=downgraded,
            contradictions_found=contradictions,
            issues=issues,
        )
