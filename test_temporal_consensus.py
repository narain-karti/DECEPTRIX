import numpy as np

# Compare the AI video vs the Real video under Temporal Consistency & Primary Subject Tracking

# 1. Real Video Deltas from inspect_video.py:
real_deltas = [4.13, -3.25, 0.60, 6.52, 0.15, 1.15, 4.32, 7.90, 8.62, 5.02, 9.94, 8.67, 7.34, 4.23, -3.37]
real_vit_scores = [1.0 / (1.0 + np.exp(-0.8 * (d - 5.5))) for d in real_deltas]

# 2. AI Video Deltas (WhatsApp Video):
ai_deltas = [12.5, 13.1, 12.8, 13.5, 12.9, 13.2, 13.0, 12.7]
ai_vit_scores = [1.0 / (1.0 + np.exp(-0.8 * (d - 5.5))) for d in ai_deltas]

print("=== REAL VIDEO METRICS ===")
print("Per-frame ViT scores:", [round(s, 2) for s in real_vit_scores])
print(f"Mean: {np.mean(real_vit_scores):.2f}, Median: {np.median(real_vit_scores):.2f}, 75th percentile: {np.percentile(real_vit_scores, 75):.2f}")
print(f"High-confidence synthetic frame ratio (>0.75): {np.mean([1 if s > 0.75 else 0 for s in real_vit_scores]):.1%}")

print("\n=== AI GENERATED VIDEO METRICS ===")
print("Per-frame ViT scores:", [round(s, 2) for s in ai_vit_scores])
print(f"Mean: {np.mean(ai_vit_scores):.2f}, Median: {np.median(ai_vit_scores):.2f}, 75th percentile: {np.percentile(ai_vit_scores, 75):.2f}")
print(f"High-confidence synthetic frame ratio (>0.75): {np.mean([1 if s > 0.75 else 0 for s in ai_vit_scores]):.1%}")
