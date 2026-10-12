# THE EUREKA MOMENT — FROM INSIGHT TO IMPACT
## Phase 1: 25-second proof of concept (`EUREKA_ARCHIMEDES_POC.mp4`)

Separate project. PASS THE LIGHT and THE POWER OF TEN are not touched.
The Archimedes scene is presented as an artistic interpretation of the legend, not documentary fact.

### Tool review (Oct 12, 2026)

| Tool | 16:9 photoreal video? | Status here |
|---|---|---|
| Promoat (key present, 749 credits) | No. Output is always vertical 9:16 with one AI presenter. | Excluded, per the brief. |
| Local renderer (`render.py`, `stage.py`, ffmpeg, `music.py`) | No photoreal people. | Free. Used for the ripple-to-blueprint graphics, the authentic Eureka logo, titles, music, grading and the edit. |
| Google Veo 3.1 (Gemini API) | Yes. Native 16:9 at 1080p, 4/6/8 s clips, 24 fps, speech and sound generated with the video, image-to-video for a consistent character. | **Recommended. Not available yet:** this environment has no Gemini key. |
| Runway Gen-4 / Kling / Luma | Yes (16:9). | Not available here. Runway and Kling would also need a separate voice tool for "Eureka!". |
| gcloud | — | Its token is not a working Google Cloud credential. |
| AWS keys (present) | Possibly Bedrock video models. | Not checked: the safety check blocked inspecting them. Use them only if you confirm they are yours for Bedrock. |

### Shot plan (25 s)

| Time | Shot | Source |
|---|---|---|
| 0–5 | Ancient Syracuse at golden hour. A slow dolly into a stone bath chamber. An older Greek scholar, an artistic interpretation of Archimedes, studies a golden crown beside a full water basin. | Veo, 8 s clip, trimmed |
| 5–10 | Close-up. He lowers the crown into the water and it overflows. Realisation crosses his face and he quietly says "Eureka!" | Veo, 8 s clip with native speech |
| 10–18 | The camera dives into the ripples, filmed as a macro shot. Gold geometric lines grow out of the rings, then architectural blueprints, then a healthcare system network (quality, accreditation, strategy, operations, people, training, growth). | Veo macro ripple clip (8 s) + local animated graphics |
| 18–25 | A contemporary hospital at dusk, with the camera rising. It is a generic building with no invented signage or logos. Then the authentic Eureka logo and "FROM INSIGHT TO IMPACT." | Veo, 8 s clip + local logo and title |

- The subtle Eureka corner logo is on screen throughout.
- Original orchestral music is generated locally for free. Veo's own audio is used only for the line and the water.

### Cost (Veo 3.1, 1080p, prices include audio)

- 4 clips × 8 s = 32 s of generation.
- **Fast tier** ($0.12/s): about $1 per clip, **about $4** for one set of clips.
- **Standard tier** ($0.40/s): about $3.20 per clip, **about $13** for one set of clips.
- **Recommended path:** first try the shots on Fast (about $4). Then render the final shots on Standard (about $13), with one retake each where needed.
- **Hard cap requested: $30.**
- These are published third-party rates. I'll check the live price before the first call and stop if it is higher.

### Minimum approval needed

1. Add a Gemini API key with billing enabled to this cloud environment's settings (environment menu → Edit → Network secrets, or as an environment variable) under the name `GEMINI_API_KEY`. Never paste it into chat. A new session picks it up.
2. Approve a spend cap. I propose up to **$30**.
