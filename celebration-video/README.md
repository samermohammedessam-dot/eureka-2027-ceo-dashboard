# Eureka × GAHAR — "10 Accreditation Achievements" celebration film

A 90-second, 1920×1080 awards-gala opening film. It is built procedurally: Python
(numpy + Pillow) renders every frame and FFmpeg encodes them. There are no AI-generated
visuals, and the real photos and logos are used as they are.

| File | Purpose |
|---|---|
| `timeline.py` | Scene timings shared by the picture and the music (120 BPM: cuts land on beats) |
| `music.py` | Original orchestral score, synthesised in code, so it is royalty-free |
| `render.py` | All visuals: light rays, spotlights, gold dust, confetti, fireworks, the institution template and the "10" reveal |
| `ingest.py` | Builds `manifest.json` from one folder of photos and logos |
| `make_placeholders.py` | Clearly marked placeholder assets for testing |

## Make the film

```bash
pip install numpy pillow scipy
python3 ingest.py /path/to/downloaded_folder          # writes manifest.json there, lists the 10
EUREKA_ASSETS=/path/to/downloaded_folder python3 render.py video --out build/Eureka_GAHAR_10.mp4
```

Folder layout: one sub-folder per institution, containing the logo (a file with `logo` in its
name) and photos. A folder whose name contains "Eureka" holds the Eureka logo and the team
photos. To fix the display names or the order, edit `manifest.json` (each `name` and the order
of the list).

Check frames quickly: `python3 render.py stills 5 30 80 88` writes PNGs to `build/stills/`.
