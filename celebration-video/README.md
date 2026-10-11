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

## Second film: "Lighting the City of Excellence" (`EUREKA_10_GAHAR_CELEBRATION.mp4`)

A procedural night city with ten landmark towers. A torch-like flame flies from tower to tower, each
tower lights up, and the institution's real logo appears followed by photos from its own folder only.
At the end the ten lights converge into a giant gold "10".

| File | Purpose |
|---|---|
| `city_timeline.py` | Scene timings (0.55 s beat: every torch arrival lands on the music) |
| `music_city.py` | Original score for this film (synthesised in code, royalty-free) |
| `city_film.py` | City, camera, torch, milestone reveal component, finale |

```bash
python3 city_film.py world                                  # build the city layers once
EUREKA_ASSETS=/path/to/assets python3 city_film.py stills 20 80
EUREKA_ASSETS=/path/to/assets python3 city_film.py video    # -> EUREKA_10_GAHAR_CELEBRATION.mp4
```

Quick edits: names, branch labels, order and photos live in the assets folder's `manifest.json`;
on-screen text is in `city_film.py` (search for the phrase), and timings are in `city_timeline.py`.
