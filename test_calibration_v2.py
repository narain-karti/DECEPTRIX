import numpy as np

# Test the three videos under calibrated sigmoid (center=3.8, slope=1.0)

def score_delta(delta):
    return 1.0 / (1.0 + np.exp(-1.0 * (delta - 3.8)))

# 1. Real Interview Video (with glasses/angles):
real_deltas = [3.85, -0.05, -1.38, -4.62, 5.59, 3.13, 4.18, 2.30, 4.48, 3.52, -0.84, 2.92, 5.79, 1.69, 6.12, -1.15, 4.57, -2.78, 2.30, -0.23, 1.14, 2.93, 3.09, 4.26, 3.29]
real_scores = [score_delta(d) for d in real_deltas]
real_primary = (np.median(real_scores) * 0.6) + (np.percentile(real_scores, 75) * 0.4)
real_lipsync = 0.15
real_dct = 0.10
real_jitter = 0.0

# 2. AI Video 1 (91728992):
ai1_deltas = [5.99, 6.63, -3.59, -2.54, 6.11, 7.17, 5.87, 5.88]
ai1_scores = [score_delta(d) for d in ai1_deltas]
ai1_primary = (np.median(ai1_scores) * 0.6) + (np.percentile(ai1_scores, 75) * 0.4)
ai1_lipsync = 0.56
ai1_dct = 0.32
ai1_jitter = 0.0

# 3. Pure AI Generated Video (WhatsApp / 05824924):
ai2_deltas = [10.27, 10.31, 10.56, 10.54, 10.84]
ai2_scores = [score_delta(d) for d in ai2_deltas]
ai2_primary = (np.median(ai2_scores) * 0.6) + (np.percentile(ai2_scores, 75) * 0.4)
ai2_lipsync = 0.70
ai2_dct = 0.25
ai2_jitter = 0.0

def evaluate_consensus(deepfake_primary, lip_sync_val, jitter_max, freq_max, meta_val=0.15):
    corroboration = (lip_sync_val * 0.35) + (jitter_max * 0.25) + (freq_max * 0.25) + (meta_val * 0.15)
    elevated_count = sum([
        1 if deepfake_primary > 0.60 else 0,
        1 if lip_sync_val > 0.45 else 0,
        1 if jitter_max > 0.45 else 0,
        1 if freq_max > 0.35 else 0,
    ])
    
    if deepfake_primary >= 0.75 and elevated_count >= 1:
        final_score = min(1.0, max(0.85, deepfake_primary))
        verdict = "Likely Manipulated"
    elif deepfake_primary >= 0.55 and elevated_count >= 2:
        final_score = min(0.90, max(0.70, (deepfake_primary * 0.6) + (corroboration * 0.4)))
        verdict = "Likely Manipulated"
    elif elevated_count >= 2:
        final_score = 0.68
        verdict = "Likely Manipulated"
    elif elevated_count >= 1 or deepfake_primary >= 0.45:
        final_score = max(0.35, min(0.55, deepfake_primary))
        verdict = "Suspicious"
    else:
        final_score = max(0.05, min(0.25, (deepfake_primary * 0.5) + (corroboration * 0.3)))
        verdict = "Likely Real"
        
    return verdict, round(final_score, 2), round(deepfake_primary, 2)

print("--- Real Interview Video ---")
v_real, s_real, d_real = evaluate_consensus(real_primary, real_lipsync, real_jitter, real_dct)
print(f"Verdict: {v_real} | Score: {s_real} | ViT: {d_real}")

print("\n--- AI Video (91728992) ---")
v_ai1, s_ai1, d_ai1 = evaluate_consensus(ai1_primary, ai1_lipsync, ai1_jitter, ai1_dct)
print(f"Verdict: {v_ai1} | Score: {s_ai1} | ViT: {d_ai1}")

print("\n--- AI Avatar Video (WhatsApp) ---")
v_ai2, s_ai2, d_ai2 = evaluate_consensus(ai2_primary, ai2_lipsync, ai2_jitter, ai2_dct)
print(f"Verdict: {v_ai2} | Score: {s_ai2} | ViT: {d_ai2}")
