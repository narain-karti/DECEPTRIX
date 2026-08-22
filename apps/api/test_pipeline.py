import uuid
from core.database import SessionLocal, Base, engine
from models.orm import Job
from services.text_worker import process_text_audit, extract_claims, classify_source_tier

def test_text_pipeline_india_aadhaar():
    """Test India-specific Aadhaar mandate rumour."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='text', text_content='Aadhaar card will be mandatory for all bank transactions starting January 2027. RBI has issued circular. All accounts without Aadhaar will be frozen.', status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running India text audit on job {job_id}...")
    process_text_audit(job_id)

    db.refresh(job)
    print("Test 1 - India Aadhaar claim completed!")
    print(f"Status: {job.status}")
    print(f"Verdict: {job.verdict}")
    claims = job.report_data.get('extracted_claims') if job.report_data else None
    print(f"Extracted Claims: {claims}")
    db.close()
    return job

def test_text_pipeline_india_pib_fake():
    """Test India-specific PIB fake circular rumour."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='text', text_content='PIB India has issued a fake circular claiming that all VPN services must be registered with the Ministry of Electronics by next month. Action will be taken against unregistered users. Forward this to all your contacts.', status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running India text audit on job {job_id}...")
    process_text_audit(job_id)

    db.refresh(job)
    print("Test 2 - India PIB fake claim completed!")
    print(f"Status: {job.status}")
    print(f"Verdict: {job.verdict}")
    claims = job.report_data.get('extracted_claims') if job.report_data else None
    print(f"Extracted Claims: {claims}")
    db.close()
    return job

def test_text_pipeline_india_digital_rupee():
    """Test India-specific Digital Rupee rumour."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='text', text_content='RBI has cancelled all paper currency notes starting next month. Digital Rupee (e-Rupee) will be the only legal tender in India. Old notes can be exchanged at banks until December 2024.', status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running India text audit on job {job_id}...")
    process_text_audit(job_id)

    db.refresh(job)
    print("Test 3 - India Digital Rupee claim completed!")
    print(f"Status: {job.status}")
    print(f"Verdict: {job.verdict}")
    claims = job.report_data.get('extracted_claims') if job.report_data else None
    print(f"Extracted Claims: {claims}")
    db.close()
    return job

def test_text_pipeline_claim_extraction():
    """Test enhanced claim extraction with Indian language patterns."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Test English claim extraction
    claims = extract_claims("The earth is flat. New RBI rules mandate digital rupee. This is a test short.")
    print(f"Claim extraction test: {len(claims)} claims found: {claims}")

    # Test tier classification
    tier1 = classify_source_tier("https://pib.gov.in")
    tier2 = classify_source_tier("https://altnews.in")
    tier3 = classify_source_tier("https://randomblog.com")
    print(f"Tier classification - PIB: {tier1}, AltNews: {tier2}, Blog: {tier3}")

    db.close()

def test_text_pipeline_india_election():
    """Test India-specific election rumour."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='text', text_content='New EC directive: All opinion polls are banned until after the Lok Sabha results are declared. Any pollster publishing data before that will face criminal charges.', status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running India text audit on job {job_id}...")
    process_text_audit(job_id)

    db.refresh(job)
    print("Test 4 - India Election claim completed!")
    print(f"Status: {job.status}")
    print(f"Verdict: {job.verdict}")
    claims = job.report_data.get('extracted_claims') if job.report_data else None
    print(f"Extracted Claims: {claims}")
    db.close()
    return job

if __name__ == "__main__":
    print("=" * 60)
    print("DECEPTRIX India-Enhanced Text Audit Pipeline Tests")
    print("=" * 60)
    
    print("\n1. Testing claim extraction...")
    test_text_pipeline_claim_extraction()
    
    print("\n2. Testing India Aadhaar rumour...")
    test_text_pipeline_india_aadhaar()
    
    print("\n3. Testing India PIB fake circular...")
    test_text_pipeline_india_pib_fake()
    
    print("\n4. Testing India Digital Rupee rumour...")
    test_text_pipeline_india_digital_rupee()
    
    print("\n5. Testing India election rumour...")
    test_text_pipeline_india_election()
    
    print("\n" + "=" * 60)
    print("All India-enhanced pipeline tests completed!")
    print("=" * 60)
