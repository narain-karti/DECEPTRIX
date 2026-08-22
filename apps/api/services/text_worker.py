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

def extract_claims(text: str):
    # Simple sentence splitting rule-based approach
    text = text.replace('\n', ' ')
    sentences = re.split(r'(?<=[.!?]) +', text)
    claims = [s.strip() for s in sentences if len(s.strip().split()) > 4]
    return claims

def classify_source_tier(url: str) -> int:
    """Classify source tier by domain suffix instead of naive substring."""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 3
    if domain.endswith(('.gov', '.gov.in', '.nic.in', '.edu', '.ac.in', '.mil')):
        return 1  # Primary authority
    if 'factcheck' in domain or 'pib.gov' in domain or 'snopes' in domain:
        return 2  # Official fact-check
    return 3  # Discovery

@celery_app.task(name="services.text_worker.process_text_audit")
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
        text_content = job.text_content if hasattr(job, 'text_content') and job.text_content else "No text provided."
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

        # Aggregate verdicts
        outcomes = [c["outcome"] for c in processed_claims]
        if "Contradicted" in outcomes:
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
            model_or_connector="DuckDuckGo + BART-Large-MNLI",
            version="1.0",
            limitations="Search coverage is bounded by DuckDuckGo results at audit time. NLI model has 1024-token context limit.",
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
