# -*- coding: utf-8 -*-
"""薄弱指数回归测试。

完全使用临时数据库和自建测试数据，不读取也不修改真实 data.db。
运行：python tools/test_weak.py
"""
import os
import sys
import shutil
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

TMP = tempfile.mkdtemp()
db.DB_PATH = os.path.join(TMP, 'weak.db')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
db.engine = create_engine('sqlite:///' + db.DB_PATH)
db.SessionLocal = sessionmaker(bind=db.engine)
db.Base.metadata.create_all(db.engine)

PASS, FAIL = [], []


def chk(name, cond, detail=''):
    (PASS if cond else FAIL).append(
        name + ((' :: ' + str(detail)) if detail != '' and not cond else '')
    )


def sat(value, ref):
    return value / (value + ref) if (value + ref) > 0 else 0.0


def index_of(rows, name):
    for row in rows:
        if row['name'] == name:
            return row
    return None


user = db.create_user('weak_tester', 'hash')
db.set_current_user(user['id'])
subject = db.add_subject('数学')
kp_a = db.add_kp(subject['id'], '函数')
kp_b = db.add_kp(subject['id'], '数列')

for i in range(3):
    db.add_question({
        'subject_id': subject['id'],
        'title_text': '函数题 %d' % i,
        'knowledge_points': [{'id': kp_a['id']}],
    })
q_b = db.add_question({
    'subject_id': subject['id'],
    'title_text': '数列题',
    'knowledge_points': [{'id': kp_b['id']}],
})

rows = db.weak_analysis(top_n=50)
chk('两个知识点都参与分析', len(rows) == 2, len(rows))
chk('错题数统计正确', index_of(rows, '函数')['question_count'] == 3,
    index_of(rows, '函数')['question_count'])
chk('未复习错题按一次错误事件计', index_of(rows, '数列')['error_count'] == 1,
    index_of(rows, '数列')['error_count'])
chk('薄弱指数落在 0..10', all(0 <= r['weak_index'] <= 10 for r in rows),
    [r['weak_index'] for r in rows])

formula_ok = True
for r in rows:
    expected = round((
        sat(r['question_count'], db.WEAK_Q_REF) * 0.4 +
        sat(r['error_count'], db.WEAK_E_REF) * 0.3 +
        sat(r['decay_score'], db.WEAK_D_REF) * 0.2 +
        sat(r['recent_errors'], db.WEAK_R_REF) * 0.1
    ) * 10, 2)
    if abs(expected - r['weak_index']) > 0.001:
        formula_ok = False
chk('薄弱指数符合固定参考规模公式', formula_ok, rows)

# 复习答对后，该知识点不应再累计错误事件
db.add_review(q_b['id'], 1, '已订正')
rows = db.weak_analysis(top_n=50)
chk('复习答对后错误事件归零', index_of(rows, '数列')['error_count'] == 0,
    index_of(rows, '数列')['error_count'])

# 复习仍错，重新计为一次错误事件且进入近 7 天统计
db.add_review(q_b['id'], 0, '仍然做错')
rows = db.weak_analysis(top_n=50)
b_after_review = index_of(rows, '数列')
chk('复习仍错重新计一次错误事件', b_after_review['error_count'] == 1,
    b_after_review['error_count'])
chk('复习仍错计入近 7 天错误', b_after_review['recent_errors'] == 1,
    b_after_review['recent_errors'])

# 稳定性：往“函数”新增一道题，只允许“函数”的指数变化
before = {r['name']: r['weak_index'] for r in rows}
db.add_question({
    'subject_id': subject['id'],
    'title_text': '函数新增题',
    'knowledge_points': [{'id': kp_a['id']}],
})
after_rows = db.weak_analysis(top_n=50)
after = {r['name']: r['weak_index'] for r in after_rows}
moved = [name for name in before if abs(after.get(name, -1) - before[name]) > 0.001]
chk('新增错题不改变其他知识点指数', moved == ['函数'], moved)
chk('目标知识点指数上升', after['函数'] > before['函数'],
    (before['函数'], after['函数']))
chk('函数仍排在数列之前',
    [r['name'] for r in after_rows][0] == '函数',
    [r['name'] for r in after_rows])

print('=== PASS (%d) ===' % len(PASS))
for name in PASS:
    print('  ok  ' + name)
if FAIL:
    print('=== FAIL (%d) ===' % len(FAIL))
    for name in FAIL:
        print('  XX  ' + name)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
