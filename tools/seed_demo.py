#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成错题本演示数据。

运行：python tools/seed_demo.py
演示账号：demo / demo123
"""
import os
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
import db

DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'demo123'


def reset_demo_user():
    existing = db.get_user_by_username(DEMO_USERNAME)
    if existing:
        db.delete_user_account(existing['id'])


def main():
    db.init_db()
    reset_demo_user()
    user = db.create_user(DEMO_USERNAME, generate_password_hash(DEMO_PASSWORD))
    uid = user['id']
    db.set_current_user(uid)

    # 学科
    math = db.add_subject('数学')
    physics = db.add_subject('物理')
    english = db.add_subject('英语')

    # 数学知识树
    function = db.add_kp(math['id'], '函数')
    derivative = db.add_kp(math['id'], '导数', parent_id=function['id'], level=1)
    monotonic = db.add_kp(math['id'], '单调性', parent_id=function['id'], level=1)
    trig = db.add_kp(math['id'], '三角函数')
    induction = db.add_kp(math['id'], '诱导公式', parent_id=trig['id'], level=1)
    trig_image = db.add_kp(math['id'], '三角函数图像', parent_id=trig['id'], level=1)
    sequence = db.add_kp(math['id'], '数列')
    arithmetic = db.add_kp(math['id'], '等差数列', parent_id=sequence['id'], level=1)
    geometric = db.add_kp(math['id'], '等比数列', parent_id=sequence['id'], level=1)

    # 物理知识树
    mechanics = db.add_kp(physics['id'], '力学')
    newton = db.add_kp(physics['id'], '牛顿运动定律', parent_id=mechanics['id'], level=1)
    momentum = db.add_kp(physics['id'], '动量守恒', parent_id=mechanics['id'], level=1)
    electromagnetism = db.add_kp(physics['id'], '电磁学')
    electric_field = db.add_kp(physics['id'], '电场', parent_id=electromagnetism['id'], level=1)
    circuit = db.add_kp(physics['id'], '电路分析', parent_id=electromagnetism['id'], level=1)

    # 英语知识树
    grammar = db.add_kp(english['id'], '语法')
    tense = db.add_kp(english['id'], '时态', parent_id=grammar['id'], level=1)
    clause = db.add_kp(english['id'], '从句', parent_id=grammar['id'], level=1)

    def kp_link(kp):
        return {'id': kp['id'], 'name': kp['name'], 'confidence': 1, 'is_auto': 0}

    questions = [
        {
            'subject_id': math['id'], 'title_text': '求函数 f(x)=x³-3x 的单调区间。',
            'correct_answer': '在 (-∞,-1) 和 (1,+∞) 上单调递增，在 (-1,1) 上单调递减。',
            'user_answer': '只求出 x=±1，没有判断区间。',
            'analysis': 'f′(x)=3x²-3=3(x-1)(x+1)，根据导数符号判断单调性。',
            'mistake_reason': '忽略导数符号表', 'status': 0,
            'knowledge_points': [kp_link(derivative), kp_link(monotonic)]
        },
        {
            'subject_id': math['id'], 'title_text': '已知 sin(π+α)=1/3，求 cos(π-α) 的值。',
            'correct_answer': '1/3', 'user_answer': '-1/3',
            'analysis': 'sin(π+α)=-sinα，cos(π-α)=-cosα，再利用同角关系求解。',
            'mistake_reason': '诱导公式符号记错', 'status': 0,
            'knowledge_points': [kp_link(induction)]
        },
        {
            'subject_id': math['id'], 'title_text': '求 y=2sin(2x+π/3) 的最小正周期和最大值。',
            'correct_answer': '周期为 π，最大值为 2。', 'user_answer': '周期写成 2π。',
            'analysis': '周期 T=2π/|ω|=π，振幅为 2，所以最大值是 2。',
            'mistake_reason': '周期公式记混', 'status': 1,
            'knowledge_points': [kp_link(trig_image)]
        },
        {
            'subject_id': math['id'], 'title_text': '等差数列 {aₙ} 中 a₁=2，d=3，求 a₁₀。',
            'correct_answer': '29', 'user_answer': '30',
            'analysis': 'aₙ=a₁+(n-1)d，所以 a₁₀=2+9×3=29。',
            'mistake_reason': '项数计算错误', 'status': 0,
            'knowledge_points': [kp_link(arithmetic)]
        },
        {
            'subject_id': math['id'], 'title_text': '等比数列首项为 3，公比为 2，求前 5 项和。',
            'correct_answer': '93', 'user_answer': '96',
            'analysis': 'Sₙ=a₁(1-qⁿ)/(1-q)=3×(1-32)/(1-2)=93。',
            'mistake_reason': '等比求和公式忘记减 1', 'status': 2,
            'knowledge_points': [kp_link(geometric)]
        },
        {
            'subject_id': math['id'], 'title_text': '已知函数 f(x)=ln x - x，求其最大值。',
            'correct_answer': '当 x=1 时取得最大值 -1。',
            'user_answer': '只求导没有判断极大值。',
            'analysis': 'f′(x)=1/x-1，令 f′(x)=0 得 x=1，再判断单调性。',
            'mistake_reason': '不会利用导数求最值', 'status': 0,
            'knowledge_points': [kp_link(derivative)]
        },
        {
            'subject_id': physics['id'], 'title_text': '质量为 2kg 的物体受到 6N 合力，求加速度。',
            'correct_answer': '3 m/s²', 'user_answer': '12 m/s²',
            'analysis': '根据牛顿第二定律 F=ma，a=F/m=6÷2=3 m/s²。',
            'mistake_reason': '公式变形错误', 'status': 0,
            'knowledge_points': [kp_link(newton)]
        },
        {
            'subject_id': physics['id'], 'title_text': '两物体碰撞前后动量如何变化？',
            'correct_answer': '系统总动量守恒。', 'user_answer': '认为碰撞后动量一定减小。',
            'analysis': '无外力或合外力为零时，系统总动量保持不变。',
            'mistake_reason': '混淆动量与动能', 'status': 0,
            'knowledge_points': [kp_link(momentum)]
        },
        {
            'subject_id': physics['id'], 'title_text': '点电荷电场强度与距离有什么关系？',
            'correct_answer': '与距离的平方成反比。', 'user_answer': '与距离成反比。',
            'analysis': 'E=kQ/r²，电场强度与距离平方成反比。',
            'mistake_reason': '平方反比关系记错', 'status': 1,
            'knowledge_points': [kp_link(electric_field)]
        },
        {
            'subject_id': physics['id'], 'title_text': '串联电路中电流和电压有什么特点？',
            'correct_answer': '电流处处相等，总电压等于各分电压之和。',
            'user_answer': '认为电压处处相等。',
            'analysis': '串联电路电流相同，电压按电阻分配。',
            'mistake_reason': '串并联规律混淆', 'status': 0,
            'knowledge_points': [kp_link(circuit)]
        },
        {
            'subject_id': english['id'], 'title_text': 'He ___ in Beijing for five years.',
            'correct_answer': 'has lived', 'user_answer': 'lived',
            'analysis': 'for five years 表示持续到现在，用现在完成时。',
            'mistake_reason': '时态判断错误', 'status': 0,
            'knowledge_points': [kp_link(tense)]
        },
        {
            'subject_id': english['id'], 'title_text': 'The book ___ I bought yesterday is very useful.',
            'correct_answer': 'which/that', 'user_answer': 'what',
            'analysis': '先行词是物，定语从句用 which 或 that。',
            'mistake_reason': '关系代词选择错误', 'status': 0,
            'knowledge_points': [kp_link(clause)]
        }
    ]

    created_questions = []
    for item in questions:
        created_questions.append(db.add_question(item))

    # 复习记录：分布到最近 30 天，形成趋势
    session = db.get_session()
    now = datetime.utcnow()
    for idx, q in enumerate(created_questions):
        for offset, result in [(29 - (idx % 25), 0), (12 - (idx % 8), 0), (3 - (idx % 3), 1)]:
            if offset < 0:
                continue
            session.add(db.ReviewLog(
                question_id=q['id'],
                review_date=now - timedelta(days=offset),
                result=result,
                note='演示复习记录'
            ))
    session.commit()
    session.close()

    today = datetime.utcnow().date()
    db.add_review_plan(created_questions[0]['id'], today.isoformat(), '订正单调区间')
    db.add_review_plan(created_questions[1]['id'], today.isoformat(), '复习诱导公式')
    db.add_review_plan(created_questions[6]['id'], (today - timedelta(days=1)).isoformat(), '补做牛顿第二定律')
    db.add_review_plan(created_questions[10]['id'], (today + timedelta(days=2)).isoformat(), '巩固现在完成时')

    db.add_ai_material(derivative['id'], 'summary',
                       '核心概念\n导数是函数在某一点的瞬时变化率。\n\n必背公式\n(xⁿ)′ = n·xⁿ⁻¹\n\n解题方法\n1. 求导；2. 令导数为 0；3. 判断符号；4. 写单调区间。\n\n易错点\n忽略定义域，忘记判断导数符号。')
    db.add_ai_material(induction['id'], 'concept',
                       '诱导公式口诀：奇变偶不变，符号看象限。\n\nsin(π+α)=-sinα\ncos(π-α)=-cosα')
    db.add_ai_material(induction['id'], 'variant',
                       '变式练习\n1. 已知 cos(π+α)=1/4，求 sin(π/2+α)。\n答案：-1/4。')
    db.add_learning_resource(derivative['id'], {
        'type': 'textbook', 'title': '高等数学上册', 'page': '96',
        'content': '导数与单调性一节'
    })
    db.add_learning_resource(induction['id'], {
        'type': 'course', 'title': 'B站三角函数基础课',
        'url': 'https://search.bilibili.com/all?keyword=诱导公式',
        'content': '重点看诱导公式推导和符号判断'
    })
    db.add_learning_resource(newton['id'], {
        'type': 'note', 'title': '牛顿第二定律笔记', 'content': 'F=ma，注意单位统一。'
    })

    db.save_mind_map(created_questions[1]['id'], json.dumps({
        'question_id': created_questions[1]['id'],
        'question_text': created_questions[1]['title_text'],
        'nodes': [
            {'id': 'question', 'type': 'question', 'label': '这道错题', 'detail': created_questions[1]['title_text']},
            {'id': 'symptom', 'type': 'symptom', 'label': '错误表象', 'detail': '符号判断错误'},
            {'id': 'point-0', 'type': 'direct', 'label': '诱导公式', 'detail': '奇变偶不变，符号看象限'},
            {'id': 'root-cause', 'type': 'root', 'label': '根本原因', 'detail': '象限符号掌握不牢'}
        ],
        'edges': [
            {'from': 'question', 'to': 'symptom'},
            {'from': 'symptom', 'to': 'point-0'},
            {'from': 'point-0', 'to': 'root-cause'}
        ]
    }, ensure_ascii=False))
    db.add_trace(created_questions[1]['id'], json.dumps({
        'symptom': '诱导公式符号错误',
        'direct_points': [{'name': '诱导公式', 'confidence': 0.92, 'reason': '题目直接考查诱导公式'}],
        'prerequisite_points': [{'name': '单位圆', 'confidence': 0.7, 'reason': '理解象限符号需要单位圆'}],
        'root_cause': '象限符号规律没有真正理解',
        'path': ['错误表象', '诱导公式', '单位圆', '根因']
    }, ensure_ascii=False))
    db.add_kp_feedback(created_questions[1]['id'], induction['id'], 'confirm')

    print('演示数据生成完成')
    print(f'账号：{DEMO_USERNAME}')
    print(f'密码：{DEMO_PASSWORD}')
    print(f'学科：3，知识点：17，错题：{len(created_questions)}')


if __name__ == '__main__':
    main()
