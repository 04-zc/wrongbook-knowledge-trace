# -*- coding: utf-8 -*-
"""AI 与 OCR 调用链集成测试。

默认使用 mock，不访问网络、不要求安装 PaddleOCR。设置以下环境变量后
可追加真实调用测试：

    WRONGBOOK_REAL_LLM=1
    WRONGBOOK_LLM_KEY=你的Key

运行：python tools/test_integration.py
"""
import io
import json
import os
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

TMP = tempfile.mkdtemp()
db.DB_PATH = os.path.join(TMP, 'integration.db')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
db.engine = create_engine('sqlite:///' + db.DB_PATH)
db.SessionLocal = sessionmaker(bind=db.engine)
db.Base.metadata.create_all(db.engine)

import app as webapp

webapp.app.config['TESTING'] = True
webapp.app.config['CSRF_ENABLED'] = False
client = webapp.app.test_client()
# 备份原始实现，供可选真实调用使用；mock 只覆盖本次进程内的测试路径
real_call_llm = webapp.call_llm
real_ocr_image = webapp.ocr_image
real_get_ocr = webapp.get_ocr
real_paddle_available = webapp.PADDLE_AVAILABLE

PASS, FAIL, SKIP = [], [], []


def chk(name, cond, detail=''):
    (PASS if cond else FAIL).append(
        name + ((' :: ' + str(detail)) if detail != '' and not cond else '')
    )


def body(response):
    try:
        return json.loads(response.data.decode('utf-8'))
    except Exception:
        return {}


client.post('/api/auth/register', json={'username': 'ituser', 'password': 'pass11'})
subject = body(client.post('/api/subjects', json={'name': '数学'}))
kp = body(client.post('/api/knowledge_points', json={'subject_id': subject['id'], 'name': '导数'}))
question = body(client.post('/api/questions', json={
    'subject_id': subject['id'],
    'title_text': '求导数',
    'knowledge_points': [{'id': kp['id']}],
}))
db.set_current_user(1)
db.set_setting('llm_api_key', 'test-key')
db.set_setting('llm_model', 'deepseek-chat')
db.set_setting('ocr_enabled', 'true')

# --- 模型返回 JSON 时，典型例题应被解析成结构化列表 ---
def fake_llm(prompt, json_mode=False):
    if '典型例题' in prompt:
        return json.dumps({'questions': [
            {'question': '例题一', 'answer': '答案一', 'analysis': '解析一'}
        ]}, ensure_ascii=False)
    if '变式练习题' in prompt:
        return json.dumps({'questions': [
            {'question': '变式一', 'answer': '答案一', 'analysis': '解析一'}
        ]}, ensure_ascii=False)
    if '学习资源' in prompt:
        return json.dumps({'resources': [
            {'type': 'note', 'title': '复习笔记', 'content': '内容'}
        ]}, ensure_ascii=False)
    return '这是模型返回的纯文本内容。'


webapp.call_llm = fake_llm
r = client.post('/api/ai/generate', json={'kp_id': kp['id'], 'mode': 'typical'})
data = body(r)
chk('typical 调用链返回结构化例题',
    r.status_code == 200 and data.get('questions', [{}])[0].get('question') == '例题一',
    data)
r = client.post('/api/ai/generate', json={'kp_id': kp['id'], 'mode': 'concept'})
chk('concept 调用链返回纯文本', r.status_code == 200 and 'content' in body(r), body(r))
r = client.post('/api/ai/generate', json={'kp_id': kp['id'], 'mode': 'resources'})
chk('resources 调用链返回结构化资源',
    r.status_code == 200 and body(r).get('resources')[0].get('title') == '复习笔记',
    body(r))

# --- 流式接口应逐段返回 delta 并以 DONE 结束 ---
def fake_stream(prompt):
    yield '第一段'
    yield '第二段'


webapp.call_llm_stream = fake_stream
r = client.post('/api/ai/stream', json={'kp_id': kp['id'], 'mode': 'concept'})
stream_text = r.data.decode('utf-8')
chk('流式接口返回 SSE 数据', r.status_code == 200 and 'text/event-stream' in r.headers.get('Content-Type', ''),
    r.headers.get('Content-Type'))
chk('流式接口包含两段内容和结束标记',
    '第一段' in stream_text and '第二段' in stream_text and '[DONE]' in stream_text,
    stream_text[:200])

# --- 知识点推荐应消费模型 JSON 并匹配已有知识点 ---
def fake_recommend(prompt, json_mode=False):
    return json.dumps({'knowledge_points': [
        {'path': '数学 > 导数', 'confidence': 0.95}
    ]}, ensure_ascii=False)


webapp.call_llm = fake_recommend
recommend = webapp.ai_recommend('求导数', subject['id'])
matched = [item for item in recommend if item.get('id') == kp['id']]
chk('AI 推荐匹配已有知识点', bool(matched), recommend)

# --- OCR 解析代码应过滤低置信度文本 ---
class FakeOcr:
    def predict(self, image_path):
        return [{'rec_texts': ['保留文本', '低分文本'], 'rec_scores': [0.9, 0.2]}]


db.set_setting('ocr_confidence_threshold', '0.6')
webapp.get_ocr = lambda: FakeOcr()
text = webapp.ocr_image('unused.png')
chk('OCR 解析过滤低置信度结果', text == '保留文本', text)

# --- /api/ocr 调用链：mock 引擎时返回文本并保存图片 ---
webapp.PADDLE_AVAILABLE = True
webapp.ocr_image = lambda image_path: '识别出的题干'
r = client.post('/api/ocr', data={
    'file': (io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 16), 'scan.png')
}, content_type='multipart/form-data')
ocr_data = body(r)
chk('OCR 接口返回识别文本', r.status_code == 200 and ocr_data.get('text') == '识别出的题干', ocr_data)
saved_url = ocr_data.get('url') or ''
if saved_url.startswith('/uploads/'):
    saved_path = os.path.join(webapp.UPLOAD_DIR, saved_url[len('/uploads/'):].replace('/', os.sep))
    try:
        os.remove(saved_path)
    except OSError:
        pass

# --- 可选真实调用 ---
if os.environ.get('WRONGBOOK_REAL_LLM') == '1':
    real_key = os.environ.get('WRONGBOOK_LLM_KEY') or db.get_setting('llm_api_key', '')
    if not real_key or real_key == 'test-key':
        SKIP.append('真实大模型调用（未提供 WRONGBOOK_LLM_KEY）')
    else:
        db.set_setting('llm_api_key', real_key)
        try:
            reply = real_call_llm('只回复两个字：正常')
            chk('真实大模型调用返回内容', bool((reply or '').strip()), reply)
        except Exception as exc:
            FAIL.append('真实大模型调用 :: ' + str(exc))
else:
    SKIP.append('真实大模型调用（默认关闭）')

if real_paddle_available and os.environ.get('WRONGBOOK_REAL_OCR') == '1':
    try:
        from PIL import Image, ImageDraw
        image_path = os.path.join(TMP, 'real_ocr.png')
        image = Image.new('RGB', (200, 60), 'white')
        ImageDraw.Draw(image).text((10, 20), 'ABC 123', fill='black')
        image.save(image_path)
        webapp.get_ocr = real_get_ocr
        webapp.ocr_image = real_ocr_image
        real_text = real_ocr_image(image_path)
        chk('真实 PaddleOCR 调用返回文本', bool((real_text or '').strip()), real_text)
    except Exception as exc:
        FAIL.append('真实 PaddleOCR 调用 :: ' + str(exc))
else:
    SKIP.append('真实 PaddleOCR 调用（默认关闭）')

print('=== PASS (%d) ===' % len(PASS))
for name in PASS:
    print('  ok  ' + name)
if FAIL:
    print('=== FAIL (%d) ===' % len(FAIL))
    for name in FAIL:
        print('  XX  ' + name)
if SKIP:
    print('=== SKIP (%d) ===' % len(SKIP))
    for name in SKIP:
        print('  --  ' + name)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAIL else 0)
