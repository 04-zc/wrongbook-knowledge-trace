
# -*- coding: utf-8 -*-
import io, json, os, sys, tempfile, shutil, sqlite3
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['FLASK_ENV'] = 'testing'

import db
# use a throwaway DB so the real data.db is untouched
TMP = tempfile.mkdtemp()
db.DB_PATH = os.path.join(TMP, 'test.db')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
db.engine = create_engine('sqlite:///' + db.DB_PATH)
db.SessionLocal = sessionmaker(bind=db.engine)
db.Base.metadata.create_all(db.engine)
for st in ['CREATE INDEX IF NOT EXISTS idx_questions_user_deleted ON questions(user_id, deleted_at)']:
    with db.engine.begin() as c:
        from sqlalchemy import text; c.execute(text(st))

import app as webapp
webapp.app.config['TESTING'] = True
webapp.app.config['CSRF_ENABLED'] = False
client = webapp.app.test_client()

PASS, FAIL = [], []
def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name + ((' :: ' + str(detail)) if detail and not cond else ''))

def body(r):
    try: return json.loads(r.data.decode('utf-8'))
    except Exception: return {}

# ---- setup two accounts ----
r = client.post('/api/auth/register', json={'username':'alice','password':'aaa111'})
check('register alice', r.status_code == 200, r.data[:200])
client.post('/api/auth/logout')
r = client.post('/api/auth/register', json={'username':'bob','password':'bbb222'})
check('register bob', r.status_code == 200, r.data[:200])
client.post('/api/auth/logout')

# ---- FIX 1: reset_password must require old password ----
r = client.post('/api/auth/reset_password', json={'username':'alice','new_password':'hacked1'})
check('reset_password WITHOUT old password is rejected', r.status_code == 400, r.status_code)
r = client.post('/api/auth/login', json={'username':'alice','password':'aaa111'})
check('alice original password still works after failed reset', r.status_code == 200, body(r))
client.post('/api/auth/logout')
r = client.post('/api/auth/reset_password', json={'username':'alice','old_password':'aaa111','new_password':'newpw1'})
check('reset_password WITH correct old password succeeds', r.status_code == 200, body(r))
r = client.post('/api/auth/login', json={'username':'alice','password':'newpw1'})
check('login with new password works', r.status_code == 200, body(r))

# ---- FIX 2: session invalidated after change_password ----
r = client.post('/api/auth/change_password', json={'old_password':'newpw1','new_password':'final11'})
check('change_password ok', r.status_code == 200, body(r))
r = client.get('/api/auth/me')
check('session cleared after change_password', r.status_code == 401, r.status_code)
r = client.post('/api/auth/login', json={'username':'alice','password':'final11'})
check('relogin with changed password', r.status_code == 200, body(r))

# ---- data isolation setup: alice gets a subject + question ----
r = client.post('/api/subjects', json={'name':'Math'})
subj = body(r); check('alice creates subject', 'id' in subj, subj)
r = client.post('/api/knowledge_points', json={'subject_id':subj['id'],'name':'Algebra'})
kp = body(r); check('alice creates kp', 'id' in kp, kp)
r = client.post('/api/questions', json={'subject_id':subj['id'],'title_text':'x+1=2','knowledge_points':[{'id':kp['id']}]})
q = body(r); check('alice creates question', 'id' in q, q)
ALICE_Q, ALICE_KP, ALICE_SUBJ = q['id'], kp['id'], subj['id']
client.post('/api/auth/logout')

# ---- login as bob ----
r = client.post('/api/auth/login', json={'username':'bob','password':'bbb222'})
check('bob login', r.status_code == 200, body(r))
bob_subj = body(client.post('/api/subjects', json={'name':'Physics'}))['id']

# ---- FIX 6a: cannot attach question to another user's subject ----
r = client.post('/api/questions', json={'subject_id':ALICE_SUBJ,'title_text':'steal'})
check('bob cannot create question under alice subject', r.status_code >= 400, r.status_code)

# ---- FIX 6b: cannot bind to another user's knowledge point ----
r = client.post('/api/questions', json={'subject_id':bob_subj,'title_text':'own','knowledge_points':[{'id':ALICE_KP}]})
qq = body(r)
if r.status_code == 200:
    r2 = client.get('/api/questions/%d' % qq['id'])
    kps = body(r2).get('knowledge_points', [])
    check('bob cannot bind alice kp', len(kps) == 0, kps)
else:
    check('bob cannot bind alice kp (rejected outright)', True)

# ---- cross-user access ----
r = client.get('/api/questions/%d' % ALICE_Q)
check('bob cannot read alice question', r.status_code == 404 or body(r) is None, r.status_code)

# ---- FIX 3: sqlite backup export/import must not leak other users ----
r = client.get('/api/backup/export/sqlite')
check('sqlite export ok', r.status_code == 200, r.status_code)
tmpdb = os.path.join(TMP, 'leak.db')
open(tmpdb,'wb').write(r.data)
data = db.read_sqlite_export(tmpdb, user_id=999999)   # nonexistent user
check('scoped read returns no foreign questions', len(data.get('questions',[])) == 0, len(data.get('questions',[])))
# read alice's own backup as alice -> should have her question, no api key
conn = sqlite3.connect(tmpdb); conn.row_factory = sqlite3.Row
users = [dict(x) for x in conn.execute('SELECT * FROM users')]
conn.close()
check('exported sqlite contains only current user', len(users) == 1, users)

# settings never leak llm_api_key on scoped read
db.set_current_user(1)
db.set_setting('llm_api_key', 'sk-secret-value')
data2 = db.read_sqlite_export(tmpdb, user_id=1)
check('scoped read strips llm_api_key',
      all(s.get('key') != 'llm_api_key' for s in data2.get('settings', [])),
      [s.get('key') for s in data2.get('settings', [])])

# ---- FIX 5: subject delete cascades ----
client.post('/api/auth/logout')
client.post('/api/auth/login', json={'username':'alice','password':'final11'})
before = len(body(client.get('/api/questions')))
r = client.delete('/api/subjects/%d' % ALICE_SUBJ)
check('subject delete ok', r.status_code == 200, body(r))
kps_after = body(client.get('/api/knowledge_points'))
check('knowledge points cascaded', all(k['id'] != ALICE_KP for k in kps_after), kps_after)
qs_after = body(client.get('/api/questions'))
check('questions cascaded', all(x['id'] != ALICE_Q for x in qs_after), qs_after)
conn = sqlite3.connect(db.DB_PATH)
orphan_q = conn.execute('SELECT COUNT(*) FROM questions WHERE subject_id=?', (ALICE_SUBJ,)).fetchone()[0]
orphan_k = conn.execute('SELECT COUNT(*) FROM knowledge_points WHERE subject_id=?', (ALICE_SUBJ,)).fetchone()[0]
conn.close()
check('no orphan questions left', orphan_q == 0, orphan_q)
check('no orphan kps left', orphan_k == 0, orphan_k)

# ---- FIX 4: upload whitelist ----
from werkzeug.datastructures import FileStorage
r = client.post('/api/upload_attachment', data={'file': (io.BytesIO(b'<script>alert(1)</script>'), 'evil.html')},
                content_type='multipart/form-data')
check('html attachment rejected', r.status_code == 400, r.status_code)
r = client.post('/api/upload_attachment', data={'file': (io.BytesIO(b'%PDF-1.4'), 'good.pdf')},
                content_type='multipart/form-data')
check('pdf attachment accepted', r.status_code == 200, body(r))
r = client.post('/api/upload_image', data={'file': (io.BytesIO(b'<svg onload=alert(1)>'), 'x.svg')},
                content_type='multipart/form-data')
check('svg image rejected', r.status_code == 400, r.status_code)

# ---- FIX 4b: magic bytes + uploads auth + request size cap ----
r = client.post('/api/upload_image', data={'file': (io.BytesIO(b'<script>alert(1)</script>'), 'fake.png')},
                content_type='multipart/form-data')
check('html renamed as png rejected', r.status_code == 400, r.status_code)
r = client.post('/api/upload_image', data={'file': (io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 16), 'real.png')},
                content_type='multipart/form-data')
check('png magic accepted', r.status_code == 200, r.data[:120])
alice = db.get_user_by_username('alice')
other = webapp.app.test_client()
other.post('/api/auth/login', json={'username': 'bob', 'password': 'bbb222'})
r = other.get('/uploads/u%d/secret.png' % alice['id'])
check('cross-user upload dir denied', r.status_code == 403, r.status_code)
anon_files = webapp.app.test_client()
r = anon_files.get('/uploads/u%d/secret.png' % alice['id'])
check('anonymous upload access denied', r.status_code == 401, r.status_code)
check('request size cap configured',
      webapp.app.config.get('MAX_CONTENT_LENGTH') == webapp.MAX_UPLOAD_BYTES)

db.set_current_user(alice['id'])
db.set_setting('ocr_enabled', 'false')
r = client.post('/api/ocr', data={'file': (io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 16), 'scan.png')},
                content_type='multipart/form-data')
check('ocr disabled is enforced', r.status_code == 400, r.status_code)
db.set_setting('ocr_enabled', 'true')

# ---- FIX 7: unknown settings key ignored ----
r = client.post('/api/settings', json={'evil_key':'v', 'llm_model':'deepseek-chat'})
check('settings save ok', r.status_code == 200, body(r))
db.set_current_user(1)
check('unknown setting key ignored', db.get_setting('evil_key', '') == '', db.get_setting('evil_key',''))
check('known setting key saved', db.get_setting('llm_model','') == 'deepseek-chat')

# ---- FIX 10: /api/auth/* prefix no longer blanket-bypassed ----
r = client.post('/api/auth/logout')
r = client.get('/api/auth/anything_else')
anon = webapp.app.test_client().get('/api/auth/anything_else')
check('unknown /api/auth/* path is NOT anonymously reachable', anon.status_code == 401, anon.status_code)

# ---- FIX 11: CSRF token on state-changing requests ----
webapp.app.config['CSRF_ENABLED'] = True
csrf_client = webapp.app.test_client()
r = csrf_client.post('/api/auth/login', json={'username': 'alice', 'password': 'final11'})
csrf = body(r).get('csrf_token', '')
check('login returns csrf token', r.status_code == 200 and len(csrf) >= 32, body(r))
r = csrf_client.post('/api/subjects', json={'name': 'CSRF'})
check('POST without csrf token rejected', r.status_code == 403, r.status_code)
r = csrf_client.post('/api/subjects', json={'name': 'CSRF'}, headers={'X-CSRF-Token': csrf})
check('POST with csrf token accepted', r.status_code == 200, r.data[:120])
r = csrf_client.post('/api/subjects', json={'name': 'CSRF2'}, headers={'X-CSRF-Token': 'wrong-token'})
check('wrong csrf token rejected', r.status_code == 403, r.status_code)
webapp.app.config['CSRF_ENABLED'] = False

# ---- FIX 12: login failure rate limit ----
webapp.reset_login_attempts()
rl_client = webapp.app.test_client()
for _ in range(5):
    rl_client.post('/api/auth/login', json={'username': 'rateuser', 'password': 'wrong11'})
r = rl_client.post('/api/auth/login', json={'username': 'rateuser', 'password': 'wrong11'})
check('login locked after repeated failures', r.status_code == 429, r.status_code)
check('lock response has Retry-After header', bool(r.headers.get('Retry-After')),
      r.headers.get('Retry-After'))
webapp.reset_login_attempts()
r = rl_client.post('/api/auth/login', json={'username': 'alice', 'password': 'final11'})
check('login works after attempts reset', r.status_code == 200, r.status_code)
webapp.reset_login_attempts()

# ---- FIX 13: optimistic lock on concurrent edit ----
client.post('/api/auth/login', json={'username': 'alice', 'password': 'final11'})
lock_subj = body(client.post('/api/subjects', json={'name': 'Lock'}))['id']
lock_q = body(client.post('/api/questions', json={'subject_id': lock_subj, 'title_text': 'v1'}))
lock_qid = lock_q['id']
v1 = lock_q['updated_at']
r = client.put('/api/questions/%d' % lock_qid, json={'title_text': 'v2', 'expected_updated_at': v1})
check('edit with matching version ok', r.status_code == 200, r.status_code)
v2 = body(r).get('updated_at')
r = client.put('/api/questions/%d' % lock_qid, json={'title_text': 'v3', 'expected_updated_at': v1})
check('stale edit rejected with 409', r.status_code == 409, r.status_code)
check('conflict returns current question',
      body(r).get('current', {}).get('title_text') == 'v2', body(r).get('current'))
r = client.put('/api/questions/%d' % lock_qid, json={'title_text': 'v3', 'expected_updated_at': v2})
check('edit with refreshed version ok', r.status_code == 200, r.status_code)

# ---- FIX 8: migration backup helper exists and is safe on empty dir ----
check('migration backup helper callable', callable(db._backup_before_migration))

print('\n=== PASS (%d) ===' % len(PASS))
for p in PASS: print('  ok  ' + p)
if FAIL:
    print('\n=== FAIL (%d) ===' % len(FAIL))
    for x in FAIL: print('  XX  ' + x)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
