# Perceptual Candidate Groups Review Package

## Overview
This directory contains visual review contact sheets and a structured register for **37 candidate groups** comprising **117 images** flagged as `perceptual_candidate` during the TR-02A dataset audit.

These groups were linked through perceptual hash similarity (Hamming distance $\le 4$) without explicit filename roots.

---

## Critical Distinction: Similarity vs. Patient Identity

> [!WARNING]
> **Visual similarity does NOT prove shared patient identity.**
> Common skin conditions (e.g. urticaria plaques, acne pustules) frequently present with identical color profiles, textures, and framing even when photographed from completely different individuals across the world.

Reviewers must strictly distinguish:
1. **Identical Source Derivative**: Crops, re-encodings, watermarked variants, or slight rotations of the **exact same original photograph**.
2. **Sequential Photographic Burst**: Multiple photos taken of the same lesion under identical background, skin markings, and lighting.
3. **Visually Similar Distinct Patients**: Different patients who simply have similar dermatological lesions.

---

## Permitted Reviewer Decisions

Reviewers must record one of the following exact decisions in `review_register.csv`:

| Decision Value | Criteria | Future Split Impact |
|---|---|---|
| `confirmed_same_source` | Visually confirmed as crops/edits of the exact same photograph. | Group kept intact; assigned to a single partition. |
| `confirmed_duplicate` | Exact duplicate or re-encoded copy of the same image. | Group kept intact or duplicate marked for exclusion. |
| `unrelated_images` | Different patients/lesions exhibiting coincidental visual similarity. | Group dissolved; images treated as independent singletons. |
| `uncertain` | Ambiguous framing; insufficient context to determine identity. | Conservative hold: keep grouped to avoid potential leakage. |
| `pending_review` | **Default unreviewed state.** | Requires review before activating physical split. |

---

## Review Files
- **Review Register**: [`review_register.csv`](review_register.csv) (117 rows)
- **Contact Sheets**: Stored under [`contact_sheets/`](contact_sheets/) (37 PNG files)
