# EUREKA — THE MOMENT · FROM DISCOVERY TO IMPACT
135-second 16:9 cinematic brand film. This is a separate project: PASS THE LIGHT and THE POWER OF TEN are not touched.
Archimedes appears as a fictional artistic interpretation of the legend.

## Tools
- **Promoat Partner API** (skill v1.1.1, price table 2026-10-11, existing `PROMOAT_KEY`):
  - silent 9:16 *scenes* clips at 1080P, one presenter per clip;
  - opening stills (first frames) to approve each look before any video is generated;
  - text-to-speech for the voiceover and the "Eureka!" line.
- **Local pipeline (free):** water and light, blueprints, real Eureka photos, counters, logos, the corner brand, orchestral score, mix and edit. It reuses `render.py`, `music.py` and the POWER OF TEN stage and photo-journey code.
- **9:16 → 16:9 without stretching or blurred side panels:**
  - Archimedes shots are composed tall. The 16:9 frame then tilts and pushes inside the tall image (basin → face), giving a real camera move.
  - Modern scenes sit as a full-height cinematic panel next to typography and animated graphics.

## Promoat clips (live estimates, all silent, 1080P)

| # | Clip | Use | Video (with approved still) | Still |
|---|---|---|---|---|
| A1 | Archimedes studies the crown and lowers it; the water overflows (10 s) | Scene 1 | 9 | 4 |
| A2 | Realization; he exclaims (5 s) | Scene 1 | 6 | 4 |
| A3 | Golden light rises from the water (5 s) | Scene 1 → 2 | 6 | 4 |
| H1 | Dr. Karim, medical director, corridor with a tablet | Who we are | 6 | 4 |
| H2 | Amira, accreditation and quality walk-round | What we do | 6 | 4 |
| H3 | Dr. Karim, strategy roadmap on glass | What we do | 6 | 4 |
| H4 | Nour, nurse educator, simulation training | What we do | 6 | 4 |
| H5 | Amira, a completed new hospital wing | Turnkey projects | 6 | 4 |

- **Video and stills:** 51 + 32 = 83 credits.
- **TTS:** "Eureka!" 10, plus all four voiceover lines in one call (409 characters) 10 = 20 credits.
- **Total: 103 credits** of the 749 balance.
- **Requested cap: 150**, which leaves room for a few retakes.
- Prompts and request bodies are in `clips.json`.

## Story breakdown (135 s)

| Time | Scene | Build |
|---|---|---|
| 0–15 | The Discovery | A1 (tilt from basin to face) → A2 with "Eureka!" → A3 golden energy |
| 15–30 | Discovery to purpose | Dive into the ripples → gold geometry → blueprints → hospital architecture → **Eureka logo**. VO 1 |
| 30–50 | Who we are | H1 + real Eureka team photos with cinematic moves. VO 2 |
| 50–75 | What we do | 7 services, about 3.5 s each. H2 accreditation, H3 strategy, H4 training and H5 turnkey are Promoat clips; operations, organizational development / HR and business development use real photos and animated systems graphics |
| 75–105 | The impact | 8 animated counters over real healthcare imagery and light trails. The **10 GAHAR** counter shows the ten real partner logos. *All figures to be confirmed by Eureka before the final render* |
| 105–125 | People and partnerships | Photo journey of real teams, owners, training and accreditation moments. VO 3 |
| 125–135 | The future | Golden light travels through the institutions → Eureka logo, "Healthcare Development Experts", "FROM INSIGHT TO IMPACT." VO 4 |

- The Eureka corner logo is visible throughout.
- Original orchestral score, built locally to fit the edit.

## Approval steps
1. **Test:** the A1 opening still (4 credits). Approve the look.
2. Then the A1 video (9 credits). Approve its quality.
3. Then the remaining clips and TTS (90 credits).
