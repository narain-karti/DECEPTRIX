import asyncio
from sqlalchemy.orm import Session
import uuid
import datetime
import re
from duckduckgo_search import DDGS
from transformers import pipeline

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

async def process_text_audit(job_id: str, db: Session):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
    
    job.progress = 10
    db.commit()
    
    # 1. Claim Extraction
    text_content = job.text_content if hasattr(job, 'text_content') and job.text_content else "No text provided."
    claims = extract_claims(text_content)
    
    if not claims:
        # If no claims, maybe the text itself is one claim
        if len(text_content.split()) > 2:
            claims = [text_content]
        else:
            # Nothing to analyze
            job.progress = 100
            job.status = "completed"
            job.verdict = "Unsupported"
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
            return
            
    job.progress = 25
    db.commit()
    
    # 2 & 3. Evidence Retrieval and Entailment
    nli_model = get_nli_model()
    
    processed_claims = []
    
    def process_claims():
        with DDGS() as ddgs:
            for claim in claims:
                # Search DuckDuckGo
                results = []
                try:
                    for r in ddgs.text(claim, max_results=3):
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
                    citations.append({
                        "url": r.get("href", ""),
                        "tier": 1 if "gov" in r.get("href", "") or "edu" in r.get("href", "") or "news" in r.get("href", "") else 2
                    })
                    
                processed_claims.append({
                    "id": str(uuid.uuid4()),
                    "text": claim,
                    "outcome": outcome,
                    "citations": citations
                })

    await asyncio.to_thread(process_claims)
    
    job.progress = 80
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
        created_at=datetime.datetime.utcnow()
    )
    
    job.progress = 100
    job.status = "completed"
    job.verdict = verdict
    job.evidence = [evidence.model_dump()]
    
    # Store extracted claims in report_data
    claim_items = [ClaimItem(claim_id=c["id"], text=c["text"], outcome=c["outcome"], citations=c["citations"]).model_dump() for c in processed_claims]
    job.report_data = {"extracted_claims": claim_items}
    
    job.completed_at = datetime.datetime.utcnow()
    db.commit()
