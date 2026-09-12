#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 test1 账号生成独立演示数据（不修改原学科）。"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db

USERNAME = 'test1'


def main():
    db.init_db()
    user = db.get_user_by_username(USERNAME)
    if not user:
        raise SystemExit('账号 test1 不存在')
    db.set_current_user(user['id'])

    for subject in db.list_subjects():
        if subject['name'].startswith('演示-'):
            db.delete_subject(subject['id'])

    math = db.add_subject('演示-数学')
    physics = db.add_subject('演示-物理')
    english = db.add_subject('演示-英语')

    function = db.add_kp(math['id'], '函数')
    derivative = db.add_kp(math['id'], '导数', parent_id=function['id'], level=1)
    trig = db.add_kp(math['id'], '三角函数')
    induction = db.add_kp(math['id'], '诱导公式', parent_id=trig['id'], level=1)
    sequence = db.add_kp(math['id'], '数列')
    arithmetic = db.add_kp(math['id'], '等差数列', parent_id=sequence['id'], level=1)

    mechanics = db.add_kp(physics['id'], '力学')
    newton = db.add_kp(physics['id'], '牛顿运动定律', parent_id=mechanics['id'], level=1)
    electric = db.add_kp(physics['id'], '电场', level=0)

    grammar = db.add_kp(english['id'], '语法')
    tense = db.add_kp(english['id'], '时态', parent_id=grammar['id'], level=1)

    def link(kp):
        return {'id': kp['id'], 'name': kp['name'], 'confidence': 1, 'is_auto': 0}

    questions_data = [
        {
            'subject_id': math['id'], 'title_text': '求函数 f(x)=x³-3x 的单调区间。',
            'correct_answer': '在 (-∞,-1) 和 (1,+∞) 上单调递增，在 (-1,1) 上单调递减。',
            'user_answer': '只求出驻点，没有判断单调区间。',
            'analysis': 'f′(x)=3x²-3=3(x-1)(x+1)，通过导数符号判断单调性。',
            'mistake_reason': '忽略导数符号表', 'status': 0,
            'knowledge_points': [link(derivative)]
        },
        {
            'subject_id': math['id'], 'title_text': '已知 sin(π+α)=1/3，求 cos(π-α)。',
            'correct_answer': '1/3', 'user_answer': '-1/3',
            'analysis': 'sin(π+α)=-sinα，cos(π-α)=-cosα。',
            'mistake_reason': '诱导公式符号错误', 'status': 0,
            'knowledge_points': [link(induction)]
        },
        {
            'subject_id': math['id'], 'title_text': '等差数列 a₁=2，d=3，求 a₁₀。',
            'correct_answer': '29', 'user_answer': '30',
            'analysis': 'aₙ=a₁+(n-1)d。',
            'mistake_reason': '项数计算错误', 'status': 1,
            'knowledge_points': [link(arithmetic)]
        },
        {
            'subject_id': physics['id'], 'title_text': '质量 2kg 的物体受 6N 合力，求加速度。',
            'correct_answer': '3 m/s²', 'user_answer': '12 m/s²',
            'analysis': 'F=ma，a=F÷m。',
            'mistake_reason': '公式变形错误', 'status': 0,
            'knowledge_points': [link(newton)]
        },
        {
            'subject_id': physics['id'], 'title_text': '点电荷电场强度与距离的关系是什么？',
            'correct_answer': '与距离平方成反比。', 'user_answer': '与距离成反比。',
            'analysis': 'E=kQ÷r²。',
            'mistake_reason': '平方反比关系记错', 'status': 0,
            'knowledge_points': [link(electric)]
        },
        {
            'subject_id': english['id'], 'title_text': 'He ___ in Beijing for five years.',
            'correct_answer': 'has lived', 'user_answer': 'lived',
            'analysis': 'for five years 表示持续到现在，用现在完成时。',
            'mistake_reason': '时态判断错误', 'status': 0,
            'knowledge_points': [link(tense)]
        }
    ]

    questions = [db.add_question(item) for item in questions_data]

    session = db.get_session()
    now = datetime.utcnow()
    for idx, q in enumerate(questions):
        for offset, result in [(25 - idx * 3, 0), (10 - idx, 0), (2, 1)]:
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
    db.add_review_plan(questions[0]['id'], today.isoformat(), '订正单调区间')
    db.add_review_plan(questions[1]['id'], today.isoformat(), '复习诱导公式')
    db.add_review_plan(questions[3]['id'], (today - timedelta(days=1)).isoformat(), '补做牛顿第二定律')
    db.add_review_plan(questions[5]['id'], (today + timedelta(days=2)).isoformat(), '巩固现在完成时')

    db.add_ai_material(derivative['id'], 'summary',
                       '核心概念\n导数是函数在某一点的瞬时变化率。\n\n必背公式\n(xⁿ)′ = n·xⁿ⁻¹\n\n方法\n1. 求导；2. 求驻点；3. 判断符号；4. 写单调区间。')
    db.add_ai_material(induction['id'], 'concept',
                       '诱导公式口诀：奇变偶不变，符号看象限。\n\nsin(π+α)=-sinα')
    db.add_learning_resource(derivative['id'], {
        'type': 'textbook', 'title': '高等数学上册', 'page': '96', 'content': '导数与单调性'
    })
    db.add_learning_resource(induction['id'], {
        'type': 'course', 'title': 'B站三角函数课程',
        'url': 'https://search.bilibili.com/all?keyword=诱导公式',
        'content': '重点看符号判断'
    })
    db.save_mind_map(questions[1]['id'], json.dumps({
        'question_id': questions[1]['id'],
        'question_text': questions[1]['title_text'],
        'nodes': [
            {'id': 'question', 'type': 'question', 'label': '这道错题', 'detail': questions[1]['title_text']},
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
    db.add_trace(questions[1]['id'], json.dumps({
        'symptom': '诱导公式符号错误',
        'direct_points': [{'name': '诱导公式', 'confidence': 0.92, 'reason': '直接考查诱导公式'}],
        'prerequisite_points': [{'name': '单位圆', 'confidence': 0.7, 'reason': '象限符号依赖单位圆'}],
        'root_cause': '象限符号规律没有真正理解',
        'path': ['错误表象', '诱导公式', '单位圆', '根因']
    }, ensure_ascii=False))
    db.add_kp_feedback(questions[1]['id'], induction['id'], 'confirm')

    print('test1 演示数据已生成')
    print('学科：演示-数学 / 演示-物理 / 演示-英语')
    print(f'错题：{len(questions)}')


if __name__ == '__main__':
    main()
