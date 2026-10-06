#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import math
import sqlite3
import uuid
import contextvars
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    ForeignKey, Boolean, Float, select, func, case, delete,
    UniqueConstraint, inspect, text, event
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload

Base = declarative_base()
_current_user = contextvars.ContextVar('current_user_id', default=None)

def current_user_id():
    return _current_user.get()

def set_current_user(uid):
    _current_user.set(uid)


class ConflictError(Exception):
    """乐观锁冲突：记录已被其他窗口或标签页修改。"""

    def __init__(self, message, current=None):
        super().__init__(message)
        self.current = current


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Subject(Base):
    __tablename__ = 'subjects'
    __table_args__ = (UniqueConstraint('user_id', 'name', name='uq_subject_user_name'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(100), default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    questions = relationship('Question', back_populates='subject', cascade='all, delete-orphan')
    knowledge_points = relationship('KnowledgePoint', back_populates='subject', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class KnowledgePoint(Base):
    __tablename__ = 'knowledge_points'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=True)
    level = Column(Integer, default=0)
    description = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    subject = relationship('Subject', back_populates='knowledge_points')
    parent = relationship('KnowledgePoint', remote_side=[id], backref='children')
    question_links = relationship('QuestionKP', back_populates='knowledge_point', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'name': self.name,
            'parent_id': self.parent_id,
            'level': self.level,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=True)
    title_text = Column(Text, nullable=False)
    title_image = Column(String(255), default='')
    options = Column(Text, default='[]')
    user_answer = Column(Text, default='')
    correct_answer = Column(Text, default='')
    analysis = Column(Text, default='')
    mistake_reason = Column(Text, default='')
    source = Column(String(20), default='manual')
    status = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    subject = relationship('Subject', back_populates='questions')
    kp_links = relationship('QuestionKP', back_populates='question', cascade='all, delete-orphan')
    review_logs = relationship('ReviewLog', back_populates='question', cascade='all, delete-orphan')

    def to_dict(self, include_kps=True):
        d = {
            'id': self.id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'title_text': self.title_text,
            'title_image': self.title_image,
            'options': self.options,
            'user_answer': self.user_answer,
            'correct_answer': self.correct_answer,
            'analysis': self.analysis,
            'mistake_reason': self.mistake_reason,
            'source': self.source,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_kps:
            d['knowledge_points'] = [
                {
                    **link.knowledge_point.to_dict(),
                    'is_auto': link.is_auto,
                    'confidence': link.confidence
                }
                for link in self.kp_links if link.knowledge_point
            ]
        return d

class QuestionKP(Base):
    __tablename__ = 'question_kp'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    kp_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False)
    is_auto = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)
    question = relationship('Question', back_populates='kp_links')
    knowledge_point = relationship('KnowledgePoint', back_populates='question_links')

class ReviewLog(Base):
    __tablename__ = 'review_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    review_date = Column(DateTime, default=datetime.utcnow)
    result = Column(Integer, default=0)
    note = Column(Text, default='')
    question = relationship('Question', back_populates='review_logs')

class ReviewPlan(Base):
    __tablename__ = 'review_plans'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, index=True)
    plan_date = Column(String(10), nullable=False)
    status = Column(String(20), default='pending')  # pending / done / skipped
    note = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'plan_date': self.plan_date,
            'status': self.status,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Setting(Base):
    __tablename__ = 'settings'
    user_id = Column(Integer, primary_key=True)
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)

class AiMaterial(Base):
    __tablename__ = 'ai_materials'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    kp_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False)
    type = Column(String(20), nullable=False)  # concept / variant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'kp_id': self.kp_id,
            'type': self.type,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class KnowledgeTrace(Base):
    __tablename__ = 'knowledge_traces'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class MindMap(Base):
    __tablename__ = 'mind_maps'
    __table_args__ = (UniqueConstraint('user_id', 'question_id', name='uq_mindmap_user_question'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False, index=True)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class KpFeedback(Base):
    __tablename__ = 'kp_feedback'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=True)
    kp_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # confirm / remove
    created_at = Column(DateTime, default=datetime.utcnow)

class LearningResource(Base):
    __tablename__ = 'learning_resources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    kp_id = Column(Integer, ForeignKey('knowledge_points.id'), nullable=False, index=True)
    type = Column(String(20), nullable=False, default='note')
    title = Column(String(200), default='')
    url = Column(String(500), default='')
    page = Column(String(50), default='')
    content = Column(Text, default='')
    attachment = Column(String(500), default='')
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'kp_id': self.kp_id,
            'type': self.type,
            'title': self.title,
            'url': self.url,
            'page': self.page,
            'content': self.content,
            'attachment': self.attachment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.db')

# 备份导入允许读取的表；表名会被拼进 SQL，因此必须白名单化
EXPORT_TABLES = {
    'subjects', 'knowledge_points', 'questions', 'question_kp', 'review_logs',
    'settings', 'ai_materials', 'learning_resources', 'review_plans',
    'knowledge_traces', 'mind_maps', 'kp_feedback',
}

def configure_engine(target_engine):
    """为 SQLite 打开 WAL、忙等待和折中同步级别。

    WAL 让读取和写入在多数情况下互不阻塞；busy_timeout 让写锁冲突时
    先等待而不是立刻抛 “database is locked”；NORMAL 在 WAL 下兼顾
    安全与写入速度。
    """
    @event.listens_for(target_engine, 'connect')
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.close()
    return target_engine


engine = configure_engine(create_engine(
    f'sqlite:///{DB_PATH}', echo=False, connect_args={'timeout': 10}
))
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()

def _columns(table):
    insp = inspect(engine)
    return [c['name'] for c in insp.get_columns(table)]

def _backup_before_migration():
    """旧结构迁移会清空 users 表，迁移前留一份完整副本以便回退。"""
    if not os.path.exists(DB_PATH):
        return None
    backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target = os.path.join(backup_dir, f'pre_migration_{stamp}.db')
    try:
        # WAL 模式下不能只复制主库文件，必须用备份 API 才能包含尚未 checkpoint 的数据
        source = sqlite3.connect(DB_PATH)
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        print(f'[db] legacy schema migration: backup written to {target}')
        return target
    except (OSError, sqlite3.Error) as e:
        print(f'[db] legacy migration backup failed: {e}')
        return None

def _migrate_legacy_schema():
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    legacy = False
    if tables and 'users' in tables and 'subjects' in tables and 'user_id' not in _columns('subjects'):
        _backup_before_migration()
    with engine.begin() as conn:
        if 'subjects' in tables and 'user_id' not in _columns('subjects'):
            legacy = True
            conn.execute(text('''
                CREATE TABLE subjects_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, name)
                )
            '''))
            conn.execute(text('''
                INSERT INTO subjects_new (id, user_id, name, icon, created_at)
                SELECT id, NULL, name, icon, created_at FROM subjects
            '''))
            conn.execute(text('DROP TABLE subjects'))
            conn.execute(text('ALTER TABLE subjects_new RENAME TO subjects'))
        for t in ['knowledge_points', 'questions']:
            if t in tables and 'user_id' not in _columns(t):
                legacy = True
                conn.execute(text(f'ALTER TABLE {t} ADD COLUMN user_id INTEGER'))
        if 'questions' in tables and 'deleted_at' not in _columns('questions'):
            conn.execute(text('ALTER TABLE questions ADD COLUMN deleted_at DATETIME'))
        if 'settings' in tables and 'user_id' not in _columns('settings'):
            legacy = True
            conn.execute(text('DROP TABLE settings'))
        if legacy and 'users' in tables:
            conn.execute(text('DELETE FROM users'))

def init_db():
    Base.metadata.create_all(engine)
    _migrate_legacy_schema()
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for statement in [
            'CREATE INDEX IF NOT EXISTS idx_questions_user_deleted ON questions(user_id, deleted_at)',
            'CREATE INDEX IF NOT EXISTS idx_questions_user_deleted_created ON questions(user_id, deleted_at, created_at DESC)',
            'CREATE INDEX IF NOT EXISTS idx_questions_subject_status ON questions(subject_id, status)',
            'CREATE INDEX IF NOT EXISTS idx_questions_user_subject_status ON questions(user_id, subject_id, status, deleted_at)',
            'CREATE INDEX IF NOT EXISTS idx_questions_created ON questions(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_question_kp_kp ON question_kp(kp_id, question_id)',
            'CREATE INDEX IF NOT EXISTS idx_kp_subject_parent ON knowledge_points(subject_id, parent_id)',
            'CREATE INDEX IF NOT EXISTS idx_review_logs_question ON review_logs(question_id)',
            'CREATE INDEX IF NOT EXISTS idx_review_plans_user_date ON review_plans(user_id, plan_date, status)'
        ]:
            conn.execute(text(statement))

# ---------- users ----------
def count_users():
    session = get_session()
    n = session.execute(select(func.count()).select_from(User)).scalar() or 0
    session.close()
    return n

def claim_legacy_data(user_id):
    with engine.begin() as conn:
        for t in ['subjects', 'knowledge_points', 'questions']:
            conn.execute(
                text(f'UPDATE {t} SET user_id = :uid WHERE user_id IS NULL'),
                {'uid': user_id}
            )

def _ci_username(value):
    """用户名统一按小写比较，避免 Demo 与 demo 被当成两个账号。"""
    return func.lower(User.username) == (value or '').strip().lower()

def get_user_by_username(username):
    session = get_session()
    u = session.execute(select(User).where(_ci_username(username))).scalar_one_or_none()
    result = u.to_dict() if u else None
    session.close()
    return result

def get_user(user_id):
    session = get_session()
    u = session.get(User, user_id)
    result = u.to_dict() if u else None
    session.close()
    return result

def get_user_password(username):
    session = get_session()
    row = session.execute(
        select(User.password_hash).where(_ci_username(username))
    ).scalar_one_or_none()
    session.close()
    return row

def create_user(username, password_hash):
    session = get_session()
    u = User(username=username, password_hash=password_hash)
    session.add(u)
    session.commit()
    result = u.to_dict()
    session.close()
    return result

def get_user_password_by_id(user_id):
    session = get_session()
    row = session.execute(
        select(User.password_hash).where(User.id == user_id)
    ).scalar_one_or_none()
    session.close()
    return row

def update_user_password(user_id, password_hash):
    session = get_session()
    u = session.get(User, user_id)
    if u:
        u.password_hash = password_hash
        session.commit()
    session.close()
    return True

def rename_user(user_id, new_username):
    session = get_session()
    exists = session.execute(
        select(User).where(_ci_username(new_username), User.id != user_id)
    ).scalar_one_or_none()
    if exists:
        session.close()
        return False
    u = session.get(User, user_id)
    if u:
        u.username = new_username
        session.commit()
    session.close()
    return True

def delete_user_account(user_id):
    session = get_session()
    qids = session.execute(select(Question.id).where(Question.user_id == user_id)).scalars().all()
    kpids = session.execute(select(KnowledgePoint.id).where(KnowledgePoint.user_id == user_id)).scalars().all()
    if qids:
        session.execute(delete(QuestionKP).where(QuestionKP.question_id.in_(qids)))
        session.execute(delete(ReviewLog).where(ReviewLog.question_id.in_(qids)))
        session.execute(delete(MindMap).where(MindMap.question_id.in_(qids)))
        session.execute(delete(KnowledgeTrace).where(KnowledgeTrace.question_id.in_(qids)))
        session.execute(delete(ReviewPlan).where(ReviewPlan.question_id.in_(qids)))
    if kpids:
        session.execute(delete(QuestionKP).where(QuestionKP.kp_id.in_(kpids)))
        session.execute(delete(AiMaterial).where(AiMaterial.kp_id.in_(kpids)))
        session.execute(delete(LearningResource).where(LearningResource.kp_id.in_(kpids)))
        session.execute(delete(KpFeedback).where(KpFeedback.kp_id.in_(kpids)))
    session.execute(delete(Question).where(Question.user_id == user_id))
    session.execute(delete(KnowledgePoint).where(KnowledgePoint.user_id == user_id))
    session.execute(delete(Subject).where(Subject.user_id == user_id))
    session.execute(delete(Setting).where(Setting.user_id == user_id))
    session.execute(delete(KpFeedback).where(KpFeedback.user_id == user_id))
    session.execute(delete(User).where(User.id == user_id))
    session.commit()
    session.close()
    return True

# ---------- subjects ----------
def list_subjects():
    uid = current_user_id()
    session = get_session()
    rows = session.execute(
        select(Subject).where(Subject.user_id == uid).order_by(Subject.id)
    ).scalars().all()
    session.close()
    return [r.to_dict() for r in rows]

def add_subject(name, icon=''):
    uid = current_user_id()
    session = get_session()
    s = Subject(user_id=uid, name=name, icon=icon)
    session.add(s)
    try:
        session.commit()
    except Exception:
        session.rollback()
        session.close()
        raise
    result = s.to_dict()
    session.close()
    return result

def delete_subject(sid):
    """删除学科并级联清理其下全部知识点、错题及关联数据。

    SQLite 默认不启用外键约束，Subject 上的 ForeignKey 不会自动级联，
    必须显式清理，否则会留下 subject_id 悬空的知识点与错题。
    """
    uid = current_user_id()
    session = get_session()
    s = session.execute(select(Subject).where(Subject.id == sid, Subject.user_id == uid)).scalar_one_or_none()
    if not s:
        session.close()
        return True
    qids = session.execute(
        select(Question.id).where(Question.user_id == uid, Question.subject_id == sid)
    ).scalars().all()
    kpids = session.execute(
        select(KnowledgePoint.id).where(KnowledgePoint.user_id == uid, KnowledgePoint.subject_id == sid)
    ).scalars().all()
    if qids:
        session.execute(delete(QuestionKP).where(QuestionKP.question_id.in_(qids)))
        session.execute(delete(ReviewLog).where(ReviewLog.question_id.in_(qids)))
        session.execute(delete(ReviewPlan).where(ReviewPlan.question_id.in_(qids)))
        session.execute(delete(MindMap).where(MindMap.question_id.in_(qids)))
        session.execute(delete(KnowledgeTrace).where(KnowledgeTrace.question_id.in_(qids)))
        session.execute(delete(Question).where(Question.id.in_(qids), Question.user_id == uid))
    if kpids:
        session.execute(delete(QuestionKP).where(QuestionKP.kp_id.in_(kpids)))
        session.execute(delete(AiMaterial).where(AiMaterial.kp_id.in_(kpids), AiMaterial.user_id == uid))
        session.execute(delete(LearningResource).where(LearningResource.kp_id.in_(kpids), LearningResource.user_id == uid))
        session.execute(delete(KpFeedback).where(KpFeedback.kp_id.in_(kpids)))
        session.execute(delete(KnowledgePoint).where(KnowledgePoint.id.in_(kpids), KnowledgePoint.user_id == uid))
    session.delete(s)
    session.commit()
    session.close()
    return True

# ---------- knowledge_points ----------
def list_kps(subject_id=None):
    uid = current_user_id()
    session = get_session()
    q = select(KnowledgePoint).where(KnowledgePoint.user_id == uid).order_by(KnowledgePoint.level, KnowledgePoint.name)
    if subject_id:
        q = q.where(KnowledgePoint.subject_id == subject_id)
    rows = session.execute(q).scalars().all()
    session.close()
    return [r.to_dict() for r in rows]

def add_kp(subject_id, name, parent_id=None, level=0, description=''):
    uid = current_user_id()
    name = (name or '').strip()
    if not name:
        raise ValueError('请输入知识点名称')
    session = get_session()
    if parent_id is not None:
        parent = session.execute(
            select(KnowledgePoint).where(
                KnowledgePoint.id == parent_id,
                KnowledgePoint.user_id == uid
            )
        ).scalar_one_or_none()
        if not parent or parent.subject_id != subject_id:
            session.close()
            raise ValueError('父知识点无效或不属于当前用户')
        level = parent.level + 1
    else:
        subj = session.execute(
            select(Subject).where(Subject.id == subject_id, Subject.user_id == uid)
        ).scalar_one_or_none()
        if not subj:
            session.close()
            raise ValueError('学科无效或不属于当前用户')
    kp = KnowledgePoint(user_id=uid, subject_id=subject_id, name=name,
                        parent_id=parent_id, level=level, description=description)
    session.add(kp)
    session.commit()
    result = kp.to_dict()
    session.close()
    return result

def get_kp(kid):
    uid = current_user_id()
    session = get_session()
    kp = session.execute(select(KnowledgePoint).where(KnowledgePoint.id == kid, KnowledgePoint.user_id == uid)).scalar_one_or_none()
    result = kp.to_dict() if kp else None
    session.close()
    return result

def find_kp_by_name(subject_id, name):
    uid = current_user_id()
    session = get_session()
    kp = session.execute(
        select(KnowledgePoint).where(KnowledgePoint.subject_id == subject_id,
                                     KnowledgePoint.name == name,
                                     KnowledgePoint.user_id == uid)
    ).scalar_one_or_none()
    result = kp.to_dict() if kp else None
    session.close()
    return result

def delete_kp(kid):
    uid = current_user_id()
    session = get_session()
    kp = session.execute(select(KnowledgePoint).where(KnowledgePoint.id == kid, KnowledgePoint.user_id == uid)).scalar_one_or_none()
    if not kp:
        session.close()
        return True
    ids = [kid]
    while True:
        children = session.execute(
            select(KnowledgePoint.id).where(KnowledgePoint.parent_id.in_(ids), KnowledgePoint.user_id == uid)
        ).scalars().all()
        new_ids = [c for c in children if c not in ids]
        if not new_ids:
            break
        ids.extend(new_ids)
    session.execute(delete(QuestionKP).where(QuestionKP.kp_id.in_(ids)))
    session.execute(delete(KnowledgePoint).where(KnowledgePoint.id.in_(ids), KnowledgePoint.user_id == uid))
    session.commit()
    session.close()
    return True

def update_kp_description(kid, description):
    uid = current_user_id()
    session = get_session()
    kp = session.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == kid, KnowledgePoint.user_id == uid)
    ).scalar_one_or_none()
    if kp:
        kp.description = description or ''
        session.commit()
    session.close()
    return True

# ---------- questions ----------
def list_questions(subject_id=None, status=None, kp_id=None, keyword=None, limit=None, offset=None):
    uid = current_user_id()
    session = get_session()
    q = select(Question).options(joinedload(Question.subject), joinedload(Question.kp_links).joinedload(QuestionKP.knowledge_point))
    q = q.where(Question.user_id == uid, Question.deleted_at.is_(None))
    if subject_id:
        q = q.where(Question.subject_id == subject_id)
    if status is not None:
        q = q.where(Question.status == status)
    if kp_id:
        q = q.join(QuestionKP).where(QuestionKP.kp_id == kp_id)
    if keyword:
        q = q.where(Question.title_text.like(f'%{keyword}%'))
    q = q.order_by(Question.created_at.desc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    rows = session.execute(q).unique().scalars().all()
    session.close()
    return [r.to_dict() for r in rows]

def count_questions(subject_id=None, status=None, kp_id=None, keyword=None):
    uid = current_user_id()
    session = get_session()
    q = select(func.count(func.distinct(Question.id))).select_from(Question).where(
        Question.user_id == uid,
        Question.deleted_at.is_(None)
    )
    if subject_id:
        q = q.where(Question.subject_id == subject_id)
    if status is not None:
        q = q.where(Question.status == status)
    if kp_id:
        q = q.join(QuestionKP).where(QuestionKP.kp_id == kp_id)
    if keyword:
        q = q.where(Question.title_text.like(f'%{keyword}%'))
    count = session.execute(q).scalar() or 0
    session.close()
    return count

def get_question(qid):
    uid = current_user_id()
    session = get_session()
    q = session.execute(
        select(Question).options(joinedload(Question.subject), joinedload(Question.kp_links).joinedload(QuestionKP.knowledge_point))
        .where(Question.id == qid, Question.user_id == uid, Question.deleted_at.is_(None))
    ).unique().scalar_one_or_none()
    result = q.to_dict() if q else None
    session.close()
    return result

def _sync_kp_links(session, question, kp_list):
    session.execute(QuestionKP.__table__.delete().where(QuestionKP.question_id == question.id))
    if not kp_list:
        return
    # 只允许绑定属于当前用户的知识点，避免通过构造 kp_id 关联到他人知识点
    owned = set(session.execute(
        select(KnowledgePoint.id).where(KnowledgePoint.user_id == question.user_id)
    ).scalars().all())
    seen = set()
    for kp in kp_list:
        kid = kp.get('id')
        if not kid or kid not in owned or kid in seen:
            continue
        seen.add(kid)
        session.add(QuestionKP(
            question_id=question.id,
            kp_id=kid,
            is_auto=kp.get('is_auto', 0),
            confidence=kp.get('confidence', 0.0)
        ))

def add_question(data):
    uid = current_user_id()
    session = get_session()
    title_text = (data.get('title_text') or '').strip()
    title_image = (data.get('title_image') or '').strip()
    if not title_text and not title_image:
        session.close()
        raise ValueError('请输入题干文本或上传图片')
    subject_id = data.get('subject_id')
    if subject_id is not None:
        subj = session.execute(
            select(Subject).where(Subject.id == subject_id, Subject.user_id == uid)
        ).scalar_one_or_none()
        if not subj:
            session.close()
            raise ValueError('学科无效或不属于当前用户')
    q = Question(
        user_id=uid,
        subject_id=subject_id,
        title_text=data.get('title_text', ''),
        title_image=data.get('title_image', ''),
        options=str(data.get('options', [])),
        user_answer=data.get('user_answer', ''),
        correct_answer=data.get('correct_answer', ''),
        analysis=data.get('analysis', ''),
        mistake_reason=data.get('mistake_reason', ''),
        source=data.get('source', 'manual'),
        status=data.get('status', 0)
    )
    session.add(q)
    session.flush()
    _sync_kp_links(session, q, data.get('knowledge_points', []))
    session.commit()
    result = q.to_dict()
    session.close()
    return result

def update_question(qid, data):
    uid = current_user_id()
    session = get_session()
    q = session.execute(select(Question).where(Question.id == qid, Question.user_id == uid, Question.deleted_at.is_(None))).scalar_one_or_none()
    if not q:
        session.close()
        return None
    # 乐观锁：调用方带回读取时的 updated_at，版本不一致说明另一窗口已改过
    expected_version = (data.get('expected_updated_at') or '').strip()
    current_version = q.updated_at.isoformat() if q.updated_at else ''
    if expected_version and current_version != expected_version:
        current = q.to_dict()
        session.close()
        raise ConflictError('这道题已在其他窗口被修改，请刷新后重试', current)
    # 编辑后仍需保证题干文本或图片至少留有一项
    next_title = (data.get('title_text', q.title_text) or '').strip()
    next_image = (data.get('title_image', q.title_image) or '').strip()
    if not next_title and not next_image:
        session.close()
        raise ValueError('请输入题干文本或上传图片')
    if 'subject_id' in data and data['subject_id'] is not None:
        subj = session.execute(
            select(Subject).where(Subject.id == data['subject_id'], Subject.user_id == uid)
        ).scalar_one_or_none()
        if not subj:
            session.close()
            raise ValueError('学科无效或不属于当前用户')
    for field in ['subject_id', 'title_text', 'title_image', 'options', 'user_answer',
                  'correct_answer', 'analysis', 'mistake_reason', 'status']:
        if field in data:
            setattr(q, field, data[field])
    if 'knowledge_points' in data:
        _sync_kp_links(session, q, data['knowledge_points'])
    # 任何修改都推进版本号，只改知识点关联也能被冲突检测发现
    now = datetime.utcnow()
    if q.updated_at and now <= q.updated_at:
        now = q.updated_at + timedelta(microseconds=1)
    q.updated_at = now
    session.commit()
    result = q.to_dict()
    session.close()
    return result

def delete_question(qid):
    uid = current_user_id()
    session = get_session()
    q = session.execute(select(Question).where(Question.id == qid, Question.user_id == uid, Question.deleted_at.is_(None))).scalar_one_or_none()
    if q:
        q.deleted_at = datetime.utcnow()
        session.commit()
    session.close()
    return True

def list_trash_questions():
    uid = current_user_id()
    session = get_session()
    q = select(Question).options(
        joinedload(Question.subject),
        joinedload(Question.kp_links).joinedload(QuestionKP.knowledge_point)
    ).where(Question.user_id == uid, Question.deleted_at.is_not(None)).order_by(Question.deleted_at.desc())
    rows = session.execute(q).unique().scalars().all()
    result = [r.to_dict() for r in rows]
    session.close()
    return result

def restore_question(qid):
    uid = current_user_id()
    session = get_session()
    q = session.execute(select(Question).where(Question.id == qid, Question.user_id == uid, Question.deleted_at.is_not(None))).scalar_one_or_none()
    if q:
        q.deleted_at = None
        session.commit()
    session.close()
    return True

def purge_question(qid):
    uid = current_user_id()
    session = get_session()
    q = session.execute(select(Question).where(Question.id == qid, Question.user_id == uid, Question.deleted_at.is_not(None))).scalar_one_or_none()
    if q:
        session.delete(q)
        session.commit()
    session.close()
    return True

def add_review(qid, result, note=''):
    uid = current_user_id()
    session = get_session()
    q = session.execute(select(Question).where(Question.id == qid, Question.user_id == uid, Question.deleted_at.is_(None))).scalar_one_or_none()
    if not q:
        session.close()
        return False
    session.add(ReviewLog(question_id=qid, result=result, note=note))
    q.status = 1 if result == 1 else 0
    session.commit()
    session.close()
    return True

# ---------- review plans ----------
def add_review_plan(question_id, plan_date, note=''):
    uid = current_user_id()
    session = get_session()
    existing = session.execute(
        select(ReviewPlan).where(
            ReviewPlan.user_id == uid,
            ReviewPlan.question_id == question_id,
            ReviewPlan.plan_date == plan_date,
            ReviewPlan.status == 'pending'
        )
    ).scalar_one_or_none()
    if existing:
        session.close()
        return existing.to_dict()
    plan = ReviewPlan(user_id=uid, question_id=question_id, plan_date=plan_date, note=note)
    session.add(plan)
    session.commit()
    result = plan.to_dict()
    session.close()
    return result

def list_review_plans():
    uid = current_user_id()
    session = get_session()
    rows = session.execute(
        select(ReviewPlan, Question)
        .join(Question, ReviewPlan.question_id == Question.id)
        .where(ReviewPlan.user_id == uid, Question.deleted_at.is_(None))
        .order_by(ReviewPlan.plan_date, ReviewPlan.id)
    ).all()
    result = []
    for plan, question in rows:
        result.append({
            **plan.to_dict(),
            'question_text': question.title_text,
            'subject_id': question.subject_id,
            'status_text': {'pending': '待复习', 'done': '已完成', 'skipped': '已跳过'}.get(plan.status, plan.status)
        })
    session.close()
    return result

def complete_review_plan(plan_id, result=1, note=''):
    uid = current_user_id()
    session = get_session()
    plan = session.execute(
        select(ReviewPlan).where(ReviewPlan.id == plan_id, ReviewPlan.user_id == uid)
    ).scalar_one_or_none()
    if not plan:
        session.close()
        return False
    plan.status = 'done' if result == 1 else 'skipped'
    plan.note = note or plan.note
    q = session.get(Question, plan.question_id)
    if q and q.user_id == uid:
        q.status = 1 if result == 1 else 0
        session.add(ReviewLog(question_id=q.id, result=result, note=note))
    session.commit()
    session.close()
    return True

def delete_review_plan(plan_id):
    uid = current_user_id()
    session = get_session()
    plan = session.execute(
        select(ReviewPlan).where(ReviewPlan.id == plan_id, ReviewPlan.user_id == uid)
    ).scalar_one_or_none()
    if plan:
        session.delete(plan)
        session.commit()
    session.close()
    return True

def review_plan_counts():
    uid = current_user_id()
    today = datetime.utcnow().date().isoformat()
    session = get_session()
    today_count = session.execute(
        select(func.count()).select_from(ReviewPlan).where(
            ReviewPlan.user_id == uid, ReviewPlan.plan_date == today, ReviewPlan.status == 'pending'
        )
    ).scalar() or 0
    overdue = session.execute(
        select(func.count()).select_from(ReviewPlan).where(
            ReviewPlan.user_id == uid, ReviewPlan.plan_date < today, ReviewPlan.status == 'pending'
        )
    ).scalar() or 0
    session.close()
    return {'today': today_count, 'overdue': overdue, 'total': today_count + overdue}

def generate_today_plans(subject_id=None, limit=10):
    today = datetime.utcnow().date().isoformat()
    created = []
    existing_pairs = {
        (p['question_id'], p['plan_date'])
        for p in list_review_plans()
        if p.get('status') == 'pending'
    }
    weak = [kp for kp in weak_analysis(subject_id=subject_id, top_n=5) if kp.get('question_count')]
    seen = set()
    for kp in weak:
        for q in list_questions(subject_id=subject_id, kp_id=kp['id']):
            if q['id'] in seen:
                continue
            if q.get('status') == 1:
                continue
            if (q['id'], today) in existing_pairs:
                continue
            seen.add(q['id'])
            created.append(add_review_plan(q['id'], today, note=f"根据薄弱知识点「{kp['name']}」自动生成"))
            if len(created) >= limit:
                return created
    return created

# ---------- settings ----------
def get_setting(key, default=''):
    uid = current_user_id()
    session = get_session()
    s = session.get(Setting, (uid, key))
    result = s.value if s else default
    session.close()
    return result

def set_setting(key, value):
    uid = current_user_id()
    session = get_session()
    s = session.get(Setting, (uid, key))
    if s:
        s.value = str(value)
    else:
        session.add(Setting(user_id=uid, key=key, value=str(value)))
    session.commit()
    session.close()
    return True

# ---------- ai materials ----------
def add_ai_material(kp_id, material_type, content):
    uid = current_user_id()
    session = get_session()
    m = AiMaterial(user_id=uid, kp_id=kp_id, type=material_type, content=content)
    session.add(m)
    session.commit()
    result = m.to_dict()
    session.close()
    return result

def list_ai_materials(kp_id=None):
    uid = current_user_id()
    session = get_session()
    q = select(AiMaterial).where(AiMaterial.user_id == uid)
    if kp_id:
        q = q.where(AiMaterial.kp_id == kp_id)
    q = q.order_by(AiMaterial.created_at.desc())
    rows = session.execute(q).scalars().all()
    session.close()
    return [r.to_dict() for r in rows]

def update_ai_material(material_id, content):
    uid = current_user_id()
    session = get_session()
    m = session.execute(
        select(AiMaterial).where(AiMaterial.id == material_id, AiMaterial.user_id == uid)
    ).scalar_one_or_none()
    if m:
        m.content = content
        session.commit()
    result = m.to_dict() if m else None
    session.close()
    return result

def delete_ai_material(material_id):
    uid = current_user_id()
    session = get_session()
    m = session.execute(
        select(AiMaterial).where(AiMaterial.id == material_id, AiMaterial.user_id == uid)
    ).scalar_one_or_none()
    if m:
        session.delete(m)
        session.commit()
    session.close()
    return True

def typical_examples(kp_id, limit=5):
    uid = current_user_id()
    session = get_session()
    rows = session.execute(
        select(Question)
        .join(QuestionKP, QuestionKP.question_id == Question.id)
        .where(QuestionKP.kp_id == kp_id, Question.user_id == uid)
        .order_by(Question.created_at.desc())
        .limit(limit)
    ).scalars().all()
    result = [r.to_dict() for r in rows]
    session.close()
    return result

# ---------- knowledge traces ----------
def add_trace(question_id, content):
    uid = current_user_id()
    session = get_session()
    t = KnowledgeTrace(user_id=uid, question_id=question_id, content=content)
    session.add(t)
    session.commit()
    result = t.to_dict()
    session.close()
    return result

def list_traces(question_id=None):
    uid = current_user_id()
    session = get_session()
    q = select(KnowledgeTrace).where(KnowledgeTrace.user_id == uid)
    if question_id:
        q = q.where(KnowledgeTrace.question_id == question_id)
    q = q.order_by(KnowledgeTrace.created_at.desc())
    rows = session.execute(q).scalars().all()
    session.close()
    return [r.to_dict() for r in rows]

def save_mind_map(question_id, data):
    uid = current_user_id()
    session = get_session()
    m = session.execute(
        select(MindMap).where(MindMap.user_id == uid, MindMap.question_id == question_id)
    ).scalar_one_or_none()
    if m:
        m.data = data
    else:
        m = MindMap(user_id=uid, question_id=question_id, data=data)
        session.add(m)
    session.commit()
    result = m.to_dict()
    session.close()
    return result

def get_mind_map(question_id):
    uid = current_user_id()
    session = get_session()
    m = session.execute(
        select(MindMap).where(MindMap.user_id == uid, MindMap.question_id == question_id)
    ).scalar_one_or_none()
    result = m.to_dict() if m else None
    session.close()
    return result

# ---------- recommendation feedback ----------
def add_kp_feedback(question_id, kp_id, action):
    uid = current_user_id()
    session = get_session()
    session.add(KpFeedback(user_id=uid, question_id=question_id, kp_id=kp_id, action=action))
    session.commit()
    session.close()
    return True

def feedback_boost_map(subject_id=None):
    uid = current_user_id()
    session = get_session()
    q = select(KpFeedback.kp_id, KpFeedback.action).where(KpFeedback.user_id == uid)
    boost = {}
    for kp_id, action in session.execute(q).all():
        boost[kp_id] = boost.get(kp_id, 0) + (1 if action == 'confirm' else -1)
    session.close()
    return {kid: max(-0.2, min(0.2, count * 0.05)) for kid, count in boost.items()}

# ---------- learning resources ----------
def list_learning_resources(kp_id):
    uid = current_user_id()
    session = get_session()
    rows = session.execute(
        select(LearningResource)
        .where(LearningResource.user_id == uid, LearningResource.kp_id == kp_id)
        .order_by(LearningResource.created_at.desc())
    ).scalars().all()
    result = [r.to_dict() for r in rows]
    session.close()
    return result

def add_learning_resource(kp_id, data):
    uid = current_user_id()
    session = get_session()
    r = LearningResource(
        user_id=uid,
        kp_id=kp_id,
        type=data.get('type', 'note'),
        title=data.get('title', ''),
        url=data.get('url', ''),
        page=data.get('page', ''),
        content=data.get('content', ''),
        attachment=data.get('attachment', '')
    )
    session.add(r)
    session.commit()
    result = r.to_dict()
    session.close()
    return result

def update_learning_resource(rid, data):
    uid = current_user_id()
    session = get_session()
    r = session.execute(
        select(LearningResource).where(LearningResource.id == rid, LearningResource.user_id == uid)
    ).scalar_one_or_none()
    if not r:
        session.close()
        return None
    for field in ['type', 'title', 'url', 'page', 'content', 'attachment']:
        if field in data:
            setattr(r, field, data[field])
    session.commit()
    result = r.to_dict()
    session.close()
    return result

def delete_learning_resource(rid):
    uid = current_user_id()
    session = get_session()
    r = session.execute(
        select(LearningResource).where(LearningResource.id == rid, LearningResource.user_id == uid)
    ).scalar_one_or_none()
    if r:
        session.delete(r)
        session.commit()
    session.close()
    return True

# ---------- weak analysis ----------

# 薄弱指数各因子的参考规模 k。归一化采用饱和函数 x/(x+k)：
# 单调递增且上界为 1，因此指数既不随库内数据总量漂移（可跨时间比较），
# 也不会像线性截断那样在高位产生并列。调整这些常数即可整体调节灵敏度。
WEAK_Q_REF = 3.0          # 关联错题数参考规模
WEAK_E_REF = 3.0          # 累计错误次数参考规模
WEAK_D_REF = 2.0          # 时间衰减和参考规模
WEAK_R_REF = 2.0          # 近 7 天错误次数参考规模
WEAK_DECAY_DAYS = 30.0    # 时间衰减半衰尺度（天）


def _saturate(value, ref):
    """饱和归一化 x/(x+k)，返回值落在 [0, 1)。"""
    value = max(float(value or 0), 0.0)
    return value / (value + ref) if (value + ref) > 0 else 0.0


def _weak_events(created, logs):
    """返回一道错题的错误事件时间列表。

    口径统一：已复习的错题只把“复习仍错(result=0)”计为错误事件；
    从未复习的错题，以创建时间作为一次仍未解决的错误事件。
    """
    if logs:
        return [rd for rd, result in logs if result == 0 and rd]
    return [created] if created else []


def weak_analysis(subject_id=None, top_n=10):
    uid = current_user_id()
    session = get_session()

    # 1) 知识点 + 关联错题数 / 未掌握数
    q = select(
        KnowledgePoint, Subject.name.label('subject_name'),
        func.count(func.distinct(Question.id)).label('question_count'),
        func.sum(case((Question.status == 0, 1), else_=0)).label('unmastered_count')
    ).select_from(KnowledgePoint).join(Subject).outerjoin(QuestionKP, KnowledgePoint.id == QuestionKP.kp_id).outerjoin(
        Question,
        (QuestionKP.question_id == Question.id) &
        (Question.user_id == uid) &
        (Question.deleted_at.is_(None))
    )
    q = q.where(KnowledgePoint.user_id == uid)
    if subject_id:
        q = q.where(KnowledgePoint.subject_id == subject_id)
    q = q.group_by(KnowledgePoint.id)
    rows = session.execute(q).all()

    # 2) 一次取回全部“错题→知识点”映射及创建时间，避免逐知识点查询（N+1）
    link_rows = session.execute(
        select(QuestionKP.kp_id, Question.id, Question.created_at)
        .join(Question, QuestionKP.question_id == Question.id)
        .where(Question.user_id == uid, Question.deleted_at.is_(None))
    ).all()
    questions_by_kp = {}
    qid_set = set()
    seen_pairs = set()
    for kp_id, qid, created in link_rows:
        if (kp_id, qid) in seen_pairs:
            continue
        seen_pairs.add((kp_id, qid))
        questions_by_kp.setdefault(kp_id, []).append((qid, created))
        qid_set.add(qid)

    # 3) 一次取回这些错题的全部复习记录
    logs_by_qid = {}
    if qid_set:
        for qid, review_date, result in session.execute(
            select(ReviewLog.question_id, ReviewLog.review_date, ReviewLog.result)
            .where(ReviewLog.question_id.in_(qid_set))
        ).all():
            logs_by_qid.setdefault(qid, []).append((review_date, result))

    now = datetime.utcnow()
    base = []
    for kp, subject_name, qc, uc in rows:
        events = []
        for qid, created in questions_by_kp.get(kp.id, []):
            events.extend(_weak_events(created, logs_by_qid.get(qid)))
        decay_score = 0.0
        recent_errors = 0
        for when in events:
            days = max((now - when).total_seconds() / 86400, 0)
            decay_score += math.exp(-days / WEAK_DECAY_DAYS)
            if days <= 7:
                recent_errors += 1
        base.append({
            **kp.to_dict(),
            'subject_name': subject_name,
            'question_count': qc or 0,
            'unmastered_count': uc or 0,
            'error_count': len(events),
            'recent_errors': recent_errors,
            'decay_score': round(decay_score, 3)
        })

    # 固定参考规模归一化：新增错题不会改变既有知识点的指数
    for item in base:
        score = (
            _saturate(item['question_count'], WEAK_Q_REF) * 0.4 +
            _saturate(item['error_count'], WEAK_E_REF) * 0.3 +
            _saturate(item['decay_score'], WEAK_D_REF) * 0.2 +
            _saturate(item['recent_errors'], WEAK_R_REF) * 0.1
        )
        item['weak_index'] = round(score * 10, 2)
    base.sort(key=lambda x: (-x['weak_index'], -x['question_count'], -x['unmastered_count']))
    session.close()
    return base[:top_n]

def kp_tree(subject_id):
    uid = current_user_id()
    session = get_session()
    rows = session.execute(
        select(KnowledgePoint).where(KnowledgePoint.subject_id == subject_id,
                                     KnowledgePoint.user_id == uid)
    ).scalars().all()
    by_id = {}
    children = {}
    children['s' + str(subject_id)] = []
    for r in rows:
        d = r.to_dict()
        by_id[d['id']] = d
        children['k' + str(d['id'])] = []
    for r in rows:
        pid = r.parent_id if r.parent_id in by_id else None
        d = r.to_dict()
        if pid:
            children['k' + str(pid)].append(d)
        else:
            children['s' + str(r.subject_id)].append(d)
    # 按树的前序遍历输出，保证父级后面紧跟其子级
    ordered = []
    visited = set()
    def visit(kp):
        if kp['id'] in visited:
            return
        visited.add(kp['id'])
        ordered.append(kp)
        child_list = sorted(children.get('k' + str(kp['id']), []), key=lambda x: x['name'])
        for c in child_list:
            visit(c)
    roots = sorted(children.get('s' + str(subject_id), []), key=lambda x: x['name'])
    for root in roots:
        visit(root)
    # 一次聚合出每个知识点的错题数，避免逐节点查询（N+1）
    counts = dict(session.execute(
        select(QuestionKP.kp_id, func.count(func.distinct(Question.id)))
        .join(Question, QuestionKP.question_id == Question.id)
        .where(Question.user_id == uid, Question.deleted_at.is_(None))
        .group_by(QuestionKP.kp_id)
    ).all())
    for n in ordered:
        n['question_count'] = counts.get(n['id'], 0)
    session.close()
    return ordered

# ---------- backup / restore ----------
def export_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    def rows(sql, params=()):
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    qids = [r['id'] for r in conn.execute('SELECT id FROM questions WHERE user_id=?', (user_id,)).fetchall()]
    kpids = [r['id'] for r in conn.execute('SELECT id FROM knowledge_points WHERE user_id=?', (user_id,)).fetchall()]
    data = {
        'version': 1,
        'subjects': rows('SELECT * FROM subjects WHERE user_id=?', (user_id,)),
        'knowledge_points': rows('SELECT * FROM knowledge_points WHERE user_id=?', (user_id,)),
        'questions': rows('SELECT * FROM questions WHERE user_id=?', (user_id,)),
        'question_kp': rows(
            'SELECT * FROM question_kp WHERE question_id IN (%s)' % ','.join('?' * len(qids)),
            qids
        ) if qids else [],
        'review_logs': rows(
            'SELECT * FROM review_logs WHERE question_id IN (%s)' % ','.join('?' * len(qids)),
            qids
        ) if qids else [],
        'settings': rows('SELECT * FROM settings WHERE user_id=?', (user_id,)),
        'ai_materials': rows('SELECT * FROM ai_materials WHERE user_id=?', (user_id,)),
        'learning_resources': rows('SELECT * FROM learning_resources WHERE user_id=?', (user_id,)),
        'review_plans': rows('SELECT * FROM review_plans WHERE user_id=?', (user_id,)),
        'knowledge_traces': rows('SELECT * FROM knowledge_traces WHERE user_id=?', (user_id,)),
        'mind_maps': rows('SELECT * FROM mind_maps WHERE user_id=?', (user_id,)),
        'kp_feedback': rows('SELECT * FROM kp_feedback WHERE user_id=?', (user_id,))
    }
    conn.close()
    return data

def export_user_sqlite(user_id):
    os.makedirs(os.path.join(os.path.dirname(DB_PATH), 'backups'), exist_ok=True)
    target = os.path.join(os.path.dirname(DB_PATH), 'backups', f'backup_{user_id}_{uuid.uuid4().hex[:8]}.db')
    # 使用 SQLite 备份 API，保证 WAL 中未落盘的数据也进入备份
    source = sqlite3.connect(DB_PATH)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    conn = sqlite3.connect(target)
    qids = [r[0] for r in conn.execute('SELECT id FROM questions WHERE user_id=?', (user_id,)).fetchall()]
    kpids = [r[0] for r in conn.execute('SELECT id FROM knowledge_points WHERE user_id=?', (user_id,)).fetchall()]
    for table in ['subjects', 'knowledge_points', 'questions', 'ai_materials',
                  'learning_resources', 'review_plans', 'knowledge_traces',
                  'mind_maps', 'kp_feedback', 'settings']:
        conn.execute(f'DELETE FROM {table} WHERE user_id IS NULL OR user_id != ?', (user_id,))
    if qids:
        marks = ','.join('?' * len(qids))
        conn.execute(f'DELETE FROM question_kp WHERE question_id NOT IN ({marks})', qids)
        conn.execute(f'DELETE FROM review_logs WHERE question_id NOT IN ({marks})', qids)
        conn.execute(f'DELETE FROM mind_maps WHERE question_id NOT IN ({marks})', qids)
        conn.execute(f'DELETE FROM knowledge_traces WHERE question_id NOT IN ({marks})', qids)
        conn.execute(f'DELETE FROM review_plans WHERE question_id NOT IN ({marks})', qids)
    else:
        for table in ['question_kp', 'review_logs', 'mind_maps', 'knowledge_traces', 'review_plans']:
            conn.execute(f'DELETE FROM {table}')
    if kpids:
        marks = ','.join('?' * len(kpids))
        conn.execute(f'DELETE FROM question_kp WHERE kp_id NOT IN ({marks})', kpids)
        conn.execute(f'DELETE FROM ai_materials WHERE kp_id NOT IN ({marks})', kpids)
        conn.execute(f'DELETE FROM learning_resources WHERE kp_id NOT IN ({marks})', kpids)
        conn.execute(f'DELETE FROM kp_feedback WHERE kp_id NOT IN ({marks})', kpids)
    else:
        for table in ['question_kp', 'ai_materials', 'learning_resources', 'kp_feedback']:
            conn.execute(f'DELETE FROM {table}')
    conn.execute('DELETE FROM users WHERE id != ?', (user_id,))
    conn.commit()
    conn.close()
    return target

def read_sqlite_export(path, user_id=None):
    """读取备份文件。传入 user_id 时只读取该用户的数据，并剔除敏感设置项。

    裸 SQLite 备份包可能来自任意账号或旧的全库导出，必须按 user_id 过滤，
    否则导入方可看到他人错题与明文 API Key。
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    found = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    # 表名来自外部文件，必须限定在白名单内再拼进 SQL，避免被构造的表名注入
    tables = {n for n in found if n in EXPORT_TABLES}
    has_user_col = {}
    for name in tables:
        cols = {r[1] for r in conn.execute(f'PRAGMA table_info({name})').fetchall()}
        has_user_col[name] = 'user_id' in cols

    def rows(name):
        if name not in tables:
            return []
        if user_id is not None and has_user_col.get(name):
            return [dict(r) for r in conn.execute(
                f'SELECT * FROM {name} WHERE user_id=?', (user_id,)).fetchall()]
        if user_id is not None:
            return []  # 无 user_id 列的关联表由下面的 IN 子句按归属过滤
        return [dict(r) for r in conn.execute(f'SELECT * FROM {name}').fetchall()]

    def child_rows(name):
        if name not in tables:
            return []
        if user_id is None:
            return [dict(r) for r in conn.execute(f'SELECT * FROM {name}').fetchall()]
        if not qids:
            return []
        marks = ','.join('?' * len(qids))
        return [dict(r) for r in conn.execute(
            f'SELECT * FROM {name} WHERE question_id IN ({marks})', qids).fetchall()]

    subjects = rows('subjects')
    kps = rows('knowledge_points')
    questions = rows('questions')
    qids = [q['id'] for q in questions]
    kpids = [k['id'] for k in kps]

    settings = rows('settings')
    if user_id is not None:
        sensitive = {'llm_api_key'}
        settings = [s for s in settings if s.get('key') not in sensitive]

    data = {
        'version': 1,
        'subjects': subjects,
        'knowledge_points': kps,
        'questions': questions,
        'question_kp': child_rows('question_kp'),
        'review_logs': child_rows('review_logs'),
        'settings': settings,
        'ai_materials': rows('ai_materials'),
        'learning_resources': rows('learning_resources'),
        'review_plans': child_rows('review_plans'),
        'knowledge_traces': child_rows('knowledge_traces'),
        'mind_maps': child_rows('mind_maps'),
        'kp_feedback': rows('kp_feedback')
    }
    if user_id is not None:
        # 关联表按 kp 归属再过滤一次，去掉指向他人知识点的悬空关联
        keep = set(kpids)
        data['question_kp'] = [l for l in data['question_kp'] if l.get('kp_id') in keep]
    conn.close()
    return data

def import_user_data(user_id, data):
    session = get_session()
    subject_map = {}
    kp_map = {}
    question_map = {}
    stats = {'subjects': 0, 'knowledge_points': 0, 'questions': 0}
    for s in data.get('subjects', []):
        existing = session.execute(
            select(Subject).where(Subject.user_id == user_id, Subject.name == s.get('name'))
        ).scalar_one_or_none()
        if existing:
            subject_map[s['id']] = existing.id
        else:
            obj = Subject(user_id=user_id, name=s.get('name', '未命名学科'), icon=s.get('icon', ''))
            session.add(obj)
            session.flush()
            subject_map[s['id']] = obj.id
            stats['subjects'] += 1
    kps = sorted(data.get('knowledge_points', []), key=lambda x: x.get('level', 0))
    for kp in kps:
        old_parent = kp.get('parent_id')
        obj = KnowledgePoint(
            user_id=user_id,
            subject_id=subject_map.get(kp.get('subject_id')),
            name=kp.get('name', '未命名知识点'),
            parent_id=kp_map.get(old_parent) if old_parent else None,
            level=kp.get('level', 0),
            description=kp.get('description', '')
        )
        session.add(obj)
        session.flush()
        kp_map[kp['id']] = obj.id
        stats['knowledge_points'] += 1
    links_by_question = {}
    for link in data.get('question_kp', []):
        links_by_question.setdefault(link.get('question_id'), []).append(link)
    for q in data.get('questions', []):
        links = links_by_question.get(q['id'], [])
        obj = Question(
            user_id=user_id,
            subject_id=subject_map.get(q.get('subject_id')),
            title_text=q.get('title_text', ''),
            title_image=q.get('title_image', ''),
            options=q.get('options', '[]'),
            user_answer=q.get('user_answer', ''),
            correct_answer=q.get('correct_answer', ''),
            analysis=q.get('analysis', ''),
            mistake_reason=q.get('mistake_reason', ''),
            source=q.get('source', 'import'),
            status=q.get('status', 0)
        )
        session.add(obj)
        session.flush()
        question_map[q['id']] = obj.id
        stats['questions'] += 1
        for link in links:
            if link.get('kp_id') in kp_map:
                session.add(QuestionKP(
                    question_id=obj.id,
                    kp_id=kp_map[link['kp_id']],
                    is_auto=bool(link.get('is_auto')),
                    confidence=link.get('confidence', 0)
                ))
    session.commit()
    session.close()
    # 恢复复习记录（累计错误次数、正确率依赖这些数据）
    session = get_session()
    for log in data.get('review_logs', []):
        old_qid = log.get('question_id')
        if old_qid not in question_map:
            continue
        review_date = log.get('review_date')
        if isinstance(review_date, str):
            try:
                review_date = datetime.fromisoformat(review_date.replace('Z', ''))
            except ValueError:
                review_date = datetime.utcnow()
        session.add(ReviewLog(
            question_id=question_map[old_qid],
            review_date=review_date or datetime.utcnow(),
            result=log.get('result', 0),
            note=log.get('note', '')
        ))
    session.commit()
    session.close()
    # 其他附属数据按映射恢复
    for s in data.get('settings', []):
        if s.get('key'):
            set_setting(s['key'], s.get('value', ''))
    for m in data.get('ai_materials', []):
        if m.get('kp_id') in kp_map:
            add_ai_material(kp_map[m['kp_id']], m.get('type', 'custom'), m.get('content', ''))
    for r in data.get('learning_resources', []):
        if r.get('kp_id') in kp_map:
            add_learning_resource(kp_map[r['kp_id']], r)
    for p in data.get('review_plans', []):
        if p.get('question_id') in question_map:
            add_review_plan(question_map[p['question_id']], p.get('plan_date'), p.get('note', ''))
    for t in data.get('knowledge_traces', []):
        if t.get('question_id') in question_map:
            add_trace(question_map[t['question_id']], t.get('content', '{}'))
    for m in data.get('mind_maps', []):
        if m.get('question_id') in question_map:
            save_mind_map(question_map[m['question_id']], m.get('data', '{}'))
    for f in data.get('kp_feedback', []):
        if f.get('kp_id') in kp_map:
            add_kp_feedback(
                question_map.get(f.get('question_id')),
                kp_map[f['kp_id']],
                f.get('action', 'confirm')
            )
    return stats

def trend_data(subject_id=None, days=30):
    uid = current_user_id()
    start = datetime.utcnow().date() - timedelta(days=days - 1)
    session = get_session()
    added = {}
    q = select(
        func.date(Question.created_at).label('day'),
        func.count(Question.id)
    ).where(
        Question.user_id == uid,
        Question.deleted_at.is_(None),
        func.date(Question.created_at) >= start.isoformat()
    )
    if subject_id:
        q = q.where(Question.subject_id == subject_id)
    for day, count in session.execute(q.group_by(func.date(Question.created_at))).all():
        added[day] = count
    wrong = {}
    rq = select(
        func.date(ReviewLog.review_date).label('day'),
        func.count(ReviewLog.id)
    ).join(Question, ReviewLog.question_id == Question.id).where(
        Question.user_id == uid,
        Question.deleted_at.is_(None),
        ReviewLog.result == 0,
        func.date(ReviewLog.review_date) >= start.isoformat()
    )
    if subject_id:
        rq = rq.where(Question.subject_id == subject_id)
    for day, count in session.execute(rq.group_by(func.date(ReviewLog.review_date))).all():
        wrong[day] = count
    session.close()
    result = []
    for i in range(days):
        day = (start + timedelta(days=i)).isoformat()
        result.append({
            'date': day,
            'added': added.get(day, 0),
            'wrong_reviews': wrong.get(day, 0)
        })
    return result

def review_stats(subject_id=None):
    uid = current_user_id()
    session = get_session()
    q = select(
        func.count(ReviewLog.id),
        func.sum(case((ReviewLog.result == 1, 1), else_=0))
    ).join(Question, ReviewLog.question_id == Question.id).where(
        Question.user_id == uid,
        Question.deleted_at.is_(None)
    )
    if subject_id:
        q = q.where(Question.subject_id == subject_id)
    total, correct = session.execute(q).one()
    session.close()
    total = total or 0
    correct = correct or 0
    return {
        'total': total,
        'correct': correct,
        'wrong': total - correct,
        'accuracy': round(correct / total * 100, 1) if total else 0
    }
