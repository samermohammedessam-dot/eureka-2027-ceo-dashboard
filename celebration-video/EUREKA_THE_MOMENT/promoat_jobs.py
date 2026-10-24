"""THE MOMENT — Promoat job helper (key from $PROMOAT_KEY via pass_the_light/promoat.py; never printed).

  python3 promoat_jobs.py queue <shot> [--frame <ids key>]   estimate -> queue with expected_credits (budget-checked)
  python3 promoat_jobs.py wait <shot> [<shot> ...]            poll and download to build/moment/<shot>.mp4
A local ledger (ledger.json, gitignored) tracks credits spent against the approved budget.
"""
import json
import os
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'pass_the_light'))
import promoat as P  # noqa: E402

BUDGET, START_BALANCE = 400, 736       # approved: up to 400 credits from the 736 balance
FLOOR = START_BALANCE - BUDGET
OUT = os.path.join(HERE, '..', 'build', 'moment')
IDS = os.path.join(HERE, 'ids.json')


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def body_for(shot, frame_key=None):
    J = json.load(open(os.path.join(HERE, 'clips.json')))
    s = J['shots'][shot]
    b = {k: v for k, v in s.items() if not k.startswith('_')}
    b['character_id'] = J['characters'][s['_actor']]
    if frame_key:
        b['first_frame_asset_id'] = load(IDS, {})[frame_key]['frame_id']
    return b


def queue(shot, frame_key=None):
    b = body_for(shot, frame_key)
    q = P.call('POST', '/videos/estimate', b)
    need, bal = q.get('credits_required'), q.get('credits_balance')
    print(f'{shot}: quote {need}, balance {bal}', q.get('warnings') or '')
    if need is None or bal - need < FLOOR:
        sys.exit(f'STOP: {shot} would go below the approved budget floor ({FLOOR}); nothing spent.')
    ids = load(IDS, {})
    key = str(uuid.uuid4())
    r = P.call('POST', '/videos', {**b, 'expected_credits': need}, idem=key)
    print({k: r.get(k) for k in ('workflow_id', 'status', 'credits_reserved', 'warnings', 'error_code', 'message')})
    ids[shot] = {'workflow_id': r.get('workflow_id'), 'idem': key, 'quoted': need}
    json.dump(ids, open(IDS, 'w'), indent=1)


def wait(shots):
    ids = load(IDS, {})
    pending = {s: ids[s]['workflow_id'] for s in shots}
    while pending:
        for s, wf in list(pending.items()):
            st = P.call('GET', f'/jobs/{wf}/status')
            if st.get('status') in ('completed', 'failed'):
                del pending[s]
                ids = load(IDS, {})          # reload: other tools may have written meanwhile
                ids[s].update({'status': st.get('status'), 'credits_consumed': st.get('credits_consumed'),
                               'error_code': st.get('error_code')})
                url = st.get('video_url') or (st.get('result') or {}).get('video_url')
                if url:
                    dst = os.path.join(OUT, f'{s}.mp4')
                    subprocess.run(['curl', '-sS', '-o', dst, url], check=True)
                    wh = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries',
                                         'stream=width,height', '-of', 'csv=p=0', dst], capture_output=True, text=True).stdout.strip()
                    ids[s]['size'] = wh
                print(s, ids[s])
                json.dump(ids, open(IDS, 'w'), indent=1)
        if pending:
            time.sleep(10)
    print('balance', P.call('GET', '/usage/summary').get('credits_balance'))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == 'queue':
        fk = sys.argv[sys.argv.index('--frame') + 1] if '--frame' in sys.argv else None
        queue(sys.argv[2], fk)
    elif sys.argv[1] == 'wait':
        wait(sys.argv[2:])
