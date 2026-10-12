"""Minimal Promoat Partner API helper (key from $PROMOAT_KEY; never printed)."""
import json, os, sys, urllib.request, uuid

BASE = 'https://platform.promoat.ai/api/partner/v1'


def call(method, path, body=None, idem=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=None if body is None else json.dumps(body).encode())
    req.add_header('Authorization', 'Bearer ' + os.environ['PROMOAT_KEY'])
    req.add_header('Content-Type', 'application/json')
    if idem:
        req.add_header('Idempotency-Key', idem)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as e:
            return {'http_error': e.code, **json.loads(e.read() or b'{}')}
        except urllib.error.URLError:
            if attempt == 3:
                raise
            import time
            time.sleep(2 ** (attempt + 1))


if __name__ == '__main__':
    m, p = sys.argv[1], sys.argv[2]
    body = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    print(json.dumps(call(m, p, body), indent=1))
