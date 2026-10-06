
import os, sys, json, tempfile, shutil
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db
TMP = tempfile.mkdtemp()
db.DB_PATH = os.path.join(TMP,'e2e.db')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
db.engine = create_engine('sqlite:///'+db.DB_PATH)
db.SessionLocal = sessionmaker(bind=db.engine)
db.Base.metadata.create_all(db.engine)
import app as webapp
webapp.app.config['TESTING']=True
c = webapp.app.test_client()
ok=[]
def chk(n,cond,d=''): ok.append((n,bool(cond),d))

chk('register', c.post('/api/auth/register', json={'username':'user1','password':'pass11'}).status_code==200)
chk('me', c.get('/api/auth/me').status_code==200)
sid = json.loads(c.post('/api/subjects', json={'name':'S'}).data)['id']
kid = json.loads(c.post('/api/knowledge_points', json={'subject_id':sid,'name':'K'}).data)['id']
qid = json.loads(c.post('/api/questions', json={'subject_id':sid,'title_text':'t','knowledge_points':[{'id':kid}]}).data)['id']
chk('kp bound', len(json.loads(c.get('/api/questions/%d'%qid).data)['knowledge_points'])==1)
chk('weak_points', c.get('/api/weak_points').status_code==200)
chk('kp_tree', c.get('/api/kp_tree?subject_id=%d'%sid).status_code==200)
chk('review add', c.post('/api/questions/%d/review'%qid, json={'result':1,'note':'n'}).status_code==200)
chk('review today', c.get('/api/review/today').status_code==200)
chk('trash empty', json.loads(c.get('/api/questions/trash').data)==[])
chk('soft delete', c.delete('/api/questions/%d'%qid).status_code==200)
chk('in trash', len(json.loads(c.get('/api/questions/trash').data))==1)
chk('restore', c.post('/api/questions/%d/restore'%qid).status_code==200)
chk('back in library', any(q['id']==qid for q in json.loads(c.get('/api/questions').data)))
r = c.get('/api/backup/export')
pkg = os.path.join(TMP,'pkg.zip'); open(pkg,'wb').write(r.data)
chk('zip export', r.status_code==200 and os.path.getsize(pkg)>0)
c.post('/api/auth/logout')
chk('register u2', c.post('/api/auth/register', json={'username':'user2','password':'pass22'}).status_code==200)
chk('u2 empty', json.loads(c.get('/api/questions').data)==[])
r = c.post('/api/backup/import', data={'file':(open(pkg,'rb'),'pkg.zip')}, content_type='multipart/form-data')
chk('import', r.status_code==200, r.data[:150])
chk('u2 imported questions', len(json.loads(c.get('/api/questions').data))>0)
chk('u2 own subject', len(json.loads(c.get('/api/subjects').data))>0)
chk('report summary', c.get('/api/reports/summary').status_code==200)
chk('word export', c.get('/api/reports/export/word').status_code==200)
bad=[x for x in ok if not x[1]]
for n,p,d in ok: print(('  ok  ' if p else '  XX  ')+n+((' :: '+str(d)) if not p else ''))
print('\n%d passed, %d failed' % (len(ok)-len(bad), len(bad)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if bad else 0)
