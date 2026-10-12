"""Generate ONE approved Promoat clip: quote -> refuse if over budget -> queue -> poll -> download.

  python3 generate.py C2_lets_make_it_happen 95      # clip key from clips.json, approved credit cap
"""
import json
import os
import sys
import time
import urllib.request

import promoat as P

HERE = os.path.dirname(os.path.abspath(__file__))


def main(key, cap, resolution='1080P'):
    body = {**json.load(open(os.path.join(HERE, 'clips.json')))[key], 'resolution': resolution}
    q = P.call('POST', '/videos/estimate', body)
    need, bal = q.get('credits_required'), q.get('credits_balance')
    print(f'{key}: quote {need} credits, balance {bal}, approved cap {cap}')
    if need is None or need > cap:
        sys.exit(f'STOP: quote {need} is missing or above the approved {cap} credits — nothing spent.')
    if not q.get('sufficient_credits'):
        sys.exit('STOP: insufficient credits — nothing spent.')
    jobs_file = os.path.join(HERE, 'jobs.json')
    jobs = json.load(open(jobs_file)) if os.path.exists(jobs_file) else {}
    idem = jobs.get(key, {}).get('idempotency_key') or f'ptl-{key}-{int(time.time())}'
    r = P.call('POST', '/videos', {**body, 'expected_credits': need}, idem=idem)
    print({k: r.get(k) for k in ('workflow_id', 'status', 'credits_reserved', 'error_code', 'http_error', 'warnings')})
    if not r.get('workflow_id'):
        sys.exit('STOP: queue failed (any reservation is refunded automatically).')
    jobs[key] = {'workflow_id': r['workflow_id'], 'idempotency_key': idem, 'quoted': need}
    json.dump(jobs, open(jobs_file, 'w'), indent=1)
    while True:  # talking/voiced scenes take ~10-25 min
        st = P.call('GET', f"/jobs/{r['workflow_id']}/status")
        print(time.strftime('%H:%M:%S'), st.get('status'), st.get('phase'), st.get('progress'), flush=True)
        if st.get('status') in ('completed', 'failed'):
            break
        time.sleep(30)
    jobs[key].update({'status': st.get('status'), 'credits_consumed': st.get('credits_consumed'),
                      'video_url': st.get('video_url'), 'error_code': st.get('error_code')})
    json.dump(jobs, open(jobs_file, 'w'), indent=1)
    if st.get('status') != 'completed':
        sys.exit(f"FAILED: {st.get('error_code')} {st.get('error_message')} (refunded automatically)")
    os.makedirs(os.path.join(HERE, 'clips'), exist_ok=True)
    out = os.path.join(HERE, 'clips', f'{key}.mp4')
    urllib.request.urlretrieve(st['video_url'], out)
    print('downloaded', out, '| credits consumed', st.get('credits_consumed'))


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]))
