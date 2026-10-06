
# -*- coding: utf-8 -*-
import io, json, os, sys, tempfile, shutil, sqlite3
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db
TMP = tempfile.mkdtemp()
db.DB_PATH = os.path.join(TMP, 't.db')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
db.engine = create_engine('sqlite:///' + db.DB_PATH)
db.SessionLocal = sessionmaker(bind=db.engine)
db.Base.metadata.create_all(db.engine)
import app as webapp
webapp.app.config['TESTING'] = True
c = webapp.app.test_client()
PASS, FAIL = [], []
def chk(n, cond, d=''):
    (PASS if cond else FAIL).append(n + ((' :: ' + str(d)) if (d and not cond) else ''))
def body(r):
    try: return json.loads(r.data.decode('utf-8'))
    except Exception: return {}

c.post('/api/auth/register', json={'username':'alice','password':'pass11'})
sid = body(c.post('/api/subjects', json={'name':'S'}))['id']

# --- validation: empty question ---
r = c.post('/api/questions', json={'subject_id':sid,'title_text':'   ','title_image':''})
chk('empty question rejected (400)', r.status_code == 400, r.status_code)
r = c.post('/api/questions', json={'subject_id':sid,'title_image':'/uploads/x.png'})
chk('image-only question accepted', r.status_code == 200, body(r))
qid_img = body(r).get('id')

# --- validation: empty knowledge point name ---
r = c.post('/api/knowledge_points', json={'subject_id':sid,'name':'  '})
chk('empty kp name rejected (400)', r.status_code == 400, r.status_code)

# --- update_question cannot blank both fields ---
r = c.post('/api/questions', json={'subject_id':sid,'title_text':'orig'})
qid = body(r)['id']
r = c.put('/api/questions/%d' % qid, json={'title_text':'', 'title_image':''})
chk('update cannot blank question', r.status_code == 400, r.status_code)
r = c.put('/api/questions/%d' % qid, json={'title_text':'changed'})
chk('update with title ok', r.status_code == 200 and body(r).get('title_text') == 'changed', body(r))

# --- kp description can now be cleared ---
kid = body(c.post('/api/knowledge_points', json={'subject_id':sid,'name':'K'})).get('id')
c.post('/api/knowledge_points/%d/description' % kid, json={'description':'hello'})
db.set_current_user(1)
chk('description set', db.get_kp(kid)['description'] == 'hello', db.get_kp(kid)['description'])
c.post('/api/knowledge_points/%d/description' % kid, json={'description':''})
chk('description cleared', db.get_kp(kid)['description'] == '', db.get_kp(kid)['description'])

# --- case-insensitive username ---
c.post('/api/auth/logout')
r = c.post('/api/auth/register', json={'username':'BobX','password':'pass22'})
chk('register BobX ok', r.status_code == 200, body(r))
c.post('/api/auth/logout')
r = c.post('/api/auth/register', json={'username':'bobx','password':'pass33'})
chk('case-variant duplicate rejected', r.status_code == 400, (r.status_code, body(r)))
r = c.post('/api/auth/login', json={'username':'BOBX','password':'pass22'})
chk('login case-insensitive works', r.status_code == 200, body(r))

# --- weak index: fixed normalization, monotonic, bounded ---
db.set_current_user(1)
w = db.weak_analysis(top_n=50)
chk('weak index computed', len(w) >= 1, w)
chk('weak index within 0..10', all(0 <= x['weak_index'] <= 10 for x in w), [x['weak_index'] for x in w])
def sat(v, k): return (v/(v+k)) if (v+k)>0 else 0.0
ok_formula = True
for x in w:
    exp = round((sat(x['question_count'],db.WEAK_Q_REF)*0.4 + sat(x['error_count'],db.WEAK_E_REF)*0.3
                 + sat(x['decay_score'],db.WEAK_D_REF)*0.2 + sat(x['recent_errors'],db.WEAK_R_REF)*0.1)*10, 2)
    if abs(exp - x['weak_index']) > 0.001: ok_formula = False
chk('weak index matches documented formula', ok_formula, [(x['weak_index'],) for x in w[:3]])

# stability: add a question, unrelated indices must not move
before = {x['name']: x['weak_index'] for x in db.weak_analysis(top_n=99)}
newq = db.add_question({'subject_id':sid,'title_text':'稳定性','knowledge_points':[]})
after = {x['name']: x['weak_index'] for x in db.weak_analysis(top_n=99)}
moved = [n for n in before if abs(after.get(n, -1) - before[n]) > 0.001]
chk('unrelated weak indices stable on new question', len(moved) == 0, moved)

# --- kp_tree correct + no N+1 regression ---
t = db.kp_tree(sid)
chk('kp_tree returns nodes', len(t) >= 1, len(t))
chk('kp_tree nodes carry question_count', all('question_count' in n for n in t))

# --- cookie flags ---
appconf = webapp.app.config
chk('SESSION_COOKIE_SAMESITE is Lax', appconf.get('SESSION_COOKIE_SAMESITE') == 'Lax', appconf.get('SESSION_COOKIE_SAMESITE'))
chk('SESSION_COOKIE_HTTPONLY on', appconf.get('SESSION_COOKIE_HTTPONLY') is True)

# --- backup round trip still works with table whitelist ---
c.post('/api/auth/login', json={'username':'alice','password':'pass11'})
r = c.get('/api/backup/export')
pkg = os.path.join(TMP, 'p.zip'); open(pkg,'wb').write(r.data)
r = c.get('/api/backup/export/sqlite')
sdb = os.path.join(TMP, 'p.db'); open(sdb,'wb').write(r.data)
data = db.read_sqlite_export(sdb, 1)
chk('whitelisted backup read works', isinstance(data.get('questions'), list), type(data.get('questions')))
chk('llm key stripped', all(s.get('key') != 'llm_api_key' for s in data.get('settings', [])))

# crafted table name must be ignored
evil = os.path.join(TMP, 'evil.db')
conn = sqlite3.connect(evil)
conn.execute('CREATE TABLE "questions_x; DROP TABLE users; --" (id INTEGER)')
conn.commit(); conn.close()
data2 = db.read_sqlite_export(evil, 1)
chk('non-whitelisted table ignored', data2.get('questions') == [])

print('=== PASS (%d) ===' % len(PASS))
for p in PASS: print('  ok  ' + p)
if FAIL:
    print('=== FAIL (%d) ===' % len(FAIL))
    for x in FAIL: print('  XX  ' + x)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
