from sqlalchemy.orm import Session
from urllib.parse import urlparse
import uuid
import datetime
import re
from duckduckgo_search import DDGS
from transformers import pipeline
from core.celery_app import celery_app
from core.database import SessionLocal

from models.orm import Job
from schemas.common import EvidenceEvent
from schemas.text import ClaimItem

_nli_model = None
def get_nli_model():
    global _nli_model
    if _nli_model is None:
        print("Loading BART MNLI model...")
        _nli_model = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return _nli_model

# India-specific domain extensions and fact-check entities
_INDIA_T1_DOMAINS = ('.gov.in', '.nic.in', '.ac.in', '.mil.in', '.gov')
_INDIA_T2_DOMAINS = ('factcheck', 'pib', 'factcheck.gov', 'altnews', 'boomlive', 'indiafactcheck', 'daksh')
_INDIA_REGIONAL_KEYWORDS = ('aadhaar', 'pan card', 'rbi', 'digital rupee', 'upei', 'upi', 'modi', 'pm', 'cabinet', 'lok sabha', 'rajya sabha')

def extract_claims(text: str):
    # Improved sentence splitting handling Devanagari and English
    text = text.replace('\n', ' ')

    # Split on sentence boundaries: . ! ? followed by space or end-of-string
    sentences = re.split(r'(?<=[.!?])[\s]+', text)

    # Further filter: keep sentences with >4 words (English) or >2 words (indicative Indian)
    claims = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # English word count
        en_words = len(s.split())
        # Hindi/Devanagari approximate count (split on spaces + common delimiters)
        hi_transliterated_words = len(re.findall(r'[a-zA-Z]+', s))
        if en_words > 4 or hi_transliterated_words > 2:
            claims.append(s)

    return claims


def classify_source_tier(url: str) -> int:
    """Classify source tier with India-specific domain awareness."""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 3

    # Strip www. prefix for consistent matching
    if domain.startswith('www.'):
        domain = domain[4:]

    # T1: Primary Indian authorities and official .gov.in domains
    for t1 in _INDIA_T1_DOMAINS:
        if domain.endswith(t1):
            return 1

    # T1: Specific Indian government eng domains
    if domain.endswith('.gov'):
        return 1

    # T2: India-specific fact-checkers and verified platforms
    for t2 in _INDIA_T2_DOMAINS:
        if t2 in domain:
            return 2

    # T3: General discovery / other
    return 3


def _is_india_related(text: str) -> bool:
    """Heuristic: check if text references India-specific persons, entities, or schemes."""
    lower = text.lower()
    for kw in _INDIA_REGIONAL_KEYWORDS:
        if kw in lower:
            return True
    return False


def process_text_audit(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        job.progress = 10
        job.current_step = "Extracting atomic claims from text..."
        db.commit()

        # 1. Claim Extraction
        text_content = job.text_content if job.text_content else "No text provided."
        claims = extract_claims(text_content)

        if not claims:
            if len(text_content.split()) > 2:
                claims = [text_content]
            else:
                job.progress = 100
                job.status = "completed"
                job.verdict = "Unsupported"
                job.current_step = "Audit complete."
                job.completed_at = datetime.datetime.utcnow()
                db.commit()
                return

        job.progress = 25
        job.current_step = "Searching evidence sources (DuckDuckGo)..."
        db.commit()

        # 2 & 3. Evidence Retrieval and Entailment
        nli_model = get_nli_model()

        processed_claims = []

        with DDGS() as ddgs:
            for idx, claim in enumerate(claims):
                job.current_step = f"Researching claim {idx + 1} of {len(claims)}..."
                job.progress = 25 + int((idx / max(len(claims), 1)) * 50)
                db.commit()

                results = []
                try:
                    import itertools
                    for r in itertools.islice(ddgs.text(claim), 3):
                        results.append(r)
                except Exception as e:
                    print(f"DDGS error: {e}")

                if not results:
                    processed_claims.append({
                        "id": str(uuid.uuid4()),
                        "text": claim,
                        "outcome": "Unsupported",
                        "citations": []
                    })
                    continue

                # Combine snippets to check entailment
                context = " ".join([r.get("body", "") for r in results])
                # Truncate context to avoid exceeding BART's 1024 token limit
                context = context[:2000]

                job.current_step = f"Analyzing entailment for claim {idx + 1}..."
                db.commit()

                labels = ["supports", "contradicts", "neutral"]
                res = nli_model(context + " This text ", candidate_labels=[l + f" that {claim}" for l in labels])

                top_label_full = res['labels'][0]

                outcome = "Unsupported"
                if "supports" in top_label_full:
                    outcome = "Supported"
                elif "contradicts" in top_label_full:
                    outcome = "Contradicted"

                citations = []
                for r in results:
                    url = r.get("href", "")
                    citations.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "tier": classify_source_tier(url)
                    })

                processed_claims.append({
                    "id": str(uuid.uuid4()),
                    "text": claim,
                    "outcome": outcome,
                    "citations": citations
                })

        job.progress = 80
        job.current_step = "Composing audit verdict..."
        db.commit()

        # Aggregate verdicts with India-specific weighting
        outcomes = [c["outcome"] for c in processed_claims]
        citation_counts = {}
        for c in processed_claims:
            for cit in c.get("citations", []):
                tier = cit["tier"]
                citation_counts[tier] = citation_counts.get(tier, 0) + 1

        # Weighted verdict: T1 evidence strongly contradicts/supports; T3 is exploratory
        has_contradicted_t1 = any(
            c["outcome"] == "Contradicted" and any(cit["tier"] == 1 for cit in c.get("citations", []))
            for c in processed_claims
        )
        has_supported_t1 = any(
            c["outcome"] == "Supported" and any(cit["tier"] == 1 for cit in c.get("citations", []))
            for c in processed_claims
        )
        t3_only = all(
            all(cit["tier"] == 3 for cit in c.get("citations", []))
            for c in processed_claims
        )

        if has_contradicted_t1:
            verdict = "Contradicted"
            explanation = "Found evidence from authoritative Indian sources that directly contradicts one or more claims."
            severity = "high"
        elif has_supported_t1:
            verdict = "Supported"
            explanation = "Found evidence from authoritative Indian sources supporting the claims."
            severity = "low"
        elif t3_only:
            verdict = "Unsupported"
            explanation = "Only Tier 3 (discovery) sources found; insufficient authoritative Indian evidence to confirm or refute."
            severity = "medium"
        elif "Contradicted" in outcomes:
            verdict = "Contradicted"
            explanation = "Found evidence that directly contradicts one or more claims."
            severity = "high"
        elif "Supported" in outcomes:
            verdict = "Supported"
            explanation = "Found evidence supporting the claims."
            severity = "low"
        else:
            verdict = "Unsupported"
            explanation = "Could not find sufficient evidence to support or contradict the claims."
            severity = "medium"

        # Enhanced evidence event with India-specific metadata
        evidence = EvidenceEvent(
            event_id=str(uuid.uuid4()),
            case_id=job_id,
            modality="text",
            type="source_retrieval",
            status="completed",
            score_or_null=1.0 if verdict == "Contradicted" else 0.5 if verdict == "Unsupported" else 0.0,
            severity=severity,
            confidence_quality="medium",
            explanation=explanation,
            model_or_connector="DuckDuckGo + BART-Large-MNLI (India-enhanced)",
            version="2.0-india",
            limitations="Search coverage bounded by DuckDuckGo results at audit time. NLI model has 1024-token context limit. India-specific domain tiers applied.",
            created_at=datetime.datetime.utcnow()
        )

        job.progress = 100
        job.status = "completed"
        job.current_step = "Audit complete."
        job.verdict = verdict
        job.evidence = [evidence.model_dump(mode='json')]

        claim_items = [ClaimItem(claim_id=c["id"], text=c["text"], outcome=c["outcome"], citations=c["citations"]).model_dump(mode='json') for c in processed_claims]
        job.report_data = {"extracted_claims": claim_items}

        job.completed_at = datetime.datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"Text worker error: {e}")
        import traceback
        traceback.print_exc()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.current_step = f"Error: {str(e)[:200]}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


