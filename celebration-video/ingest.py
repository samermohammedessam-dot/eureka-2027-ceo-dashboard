"""Build assets/manifest.json from one downloaded folder of photos and logos.

Expected (flexible) layout of the shared folder:
  <root>/
    Eureka .../          -> Eureka logo (file with 'logo' in its name) + team/event photos
    <Institution A>/     -> its logo (file with 'logo' in its name) + its photos
    <Institution B>/ ...
Nested sub-folders are searched too. Folders are shown in alphabetical order unless
assets/order.txt lists the institution folder names one per line.

  python3 ingest.py <downloaded_root>
"""
import json
import os
import re
import sys

IMG = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.jfif', '.bmp', '.tif', '.tiff')
HERE = os.path.dirname(os.path.abspath(__file__))


def images(folder):
    out = []
    for dp, _, fs in os.walk(folder):
        out += [os.path.join(dp, f) for f in sorted(fs) if f.lower().endswith(IMG)]
    return out


def is_logo(path):
    return bool(re.search(r'logo|لوجو|شعار', path, re.I))


def pretty(name):
    name = re.sub(r'[_\-]+', ' ', name)
    name = re.sub(r'\b(gahar|accreditation|final|photos?|pictures?|pics?|20\d\d)\b', '', name, flags=re.I)
    return re.sub(r'\s+', ' ', name).strip().title()


def main(root):
    root = os.path.abspath(root)
    subs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    man = {'eureka_logo': None, 'team_photos': [], 'institutions': []}
    rel = lambda p: os.path.relpath(p, root)
    order_file = os.path.join(root, 'order.txt')
    if os.path.exists(order_file):
        wanted = [l.strip() for l in open(order_file, encoding='utf-8') if l.strip()]
        subs = [d for d in wanted if d in subs] + [d for d in subs if d not in wanted]
    for d in subs:
        files = images(os.path.join(root, d))
        logos = [f for f in files if is_logo(f)]
        photos = [f for f in files if f not in logos]
        if re.search(r'eureka|يوريكا|team', d, re.I):
            if logos and not man['eureka_logo']:
                man['eureka_logo'] = rel(logos[0])
            man['team_photos'] += [rel(p) for p in photos]
            continue
        if not logos:
            print(f'!! no logo found in "{d}" – skipped (name a file *logo*)')
            continue
        man['institutions'].append({'name': pretty(d), 'folder': d, 'logo': rel(logos[0]),
                                    'photos': [rel(p) for p in photos[:4]]})
    loose = [f for f in os.listdir(root) if f.lower().endswith(IMG)]
    for f in loose:
        if is_logo(f) and not man['eureka_logo']:
            man['eureka_logo'] = f
        elif not is_logo(f):
            man['team_photos'].append(f)
    json.dump(man, open(os.path.join(root, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"Eureka logo: {man['eureka_logo']}\nteam photos: {len(man['team_photos'])}")
    for i, inst in enumerate(man['institutions'], 1):
        print(f"{i:2d}. {inst['name']:<45} logo={os.path.basename(inst['logo'])}  photos={len(inst['photos'])}")
    n = len(man['institutions'])
    if n != 10:
        print(f'!! expected 10 institutions, found {n}')


if __name__ == '__main__':
    main(sys.argv[1])
