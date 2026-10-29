<div align="center">

# 📚 错题本知识溯源整理助手

**面向个人学习者的本地错题管理与知识溯源系统**

围绕「错题录入 → 知识点识别 → 知识溯源 → 薄弱分析 → 复习计划 → 掌握反馈」形成完整学习闭环

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vue.js&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Scope](https://img.shields.io/badge/用途-个人学习-blue)

</div>

---

## ✨ 功能总览

<table>
<tr>
<td width="50%" valign="top">

### 📝 错题管理

- **三种录入方式**：先选方式再录入
  - 手动输入（LaTeX 公式实时渲染）
  - 拍照输入（PaddleOCR 文字识别）
  - 文件上传（PDF / DOCX 试卷自动拆分）
- 分页浏览、关键词搜索
- 学科 / 知识点 / 状态三重筛选
- 批量关联知识点、批量改状态
- 回收站（软删除，可恢复 / 彻底删除）

### 🌳 知识体系

- 学科为根的多级知识树
- 弹窗式目录管理，支持任意层级
- 知识点说明、教材页码、网课链接
- 知识库内容（笔记 / 知识点精要 / 概念回顾）

</td>
<td width="50%" valign="top">

### 🧠 智能分析

- **知识溯源**：AI 定位错误根因，置信度分档 + 用户确认
- **薄弱分析**：累计错误 × 时间衰减 × 近 7 天重复
- **知识图谱**：分层导图 / 树图 / 旭日图
- **统计报表**：汇总、状态分布、薄弱排行，导出 Word / PDF

### 📅 复习与反馈

- 今日推荐、自定义计划
- 浏览器提醒、逾期提示
- ICS 日历导出
- AI 概念回顾 / 典型例题 / 变式练习 / 单题解答

### 🌐 其他

- PWA 可安装到手机主屏
- ZIP 数据包备份与恢复
- 未引用图片一键清理

</td>
</tr>
</table>

---
## 🚀 快速开始

### Windows 一键启动

双击 **启动错题本.bat** —— 自动定位 Python、检查依赖、启动服务并打开浏览器。

### 命令行

```bash
pip install -r requirements.txt
python app.py
```

访问 <http://localhost:5000>

### 首次使用

1. 注册账号（账号 3–20 位、密码 6–20 位，仅限字母数字）
2. 到「学科设置」新建学科、搭建知识点
3. 到「错题录入」录入第一道错题
4. 到「模型与 OCR 配置」填入大模型 API Key 以启用 AI 功能

> 💡 **首次打开若界面异常，请按 Ctrl + Shift + R 硬刷新**（PWA 缓存可能仍在提供旧版本）

---

## 🛠 技术栈

| 层次 | 技术选型 |
|---|---|
| **后端** | Flask 3.x · SQLAlchemy 2.x |
| **数据库** | SQLite（WAL 模式） |
| **前端** | Vue 3 · Axios · 原生 CSS 设计令牌 |
| **图表** | ECharts |
| **公式** | KaTeX |
| **图标** | Lucide（SVG） |
| **OCR** | PaddleOCR · PaddlePaddle |
| **文档解析** | python-docx · PyMuPDF |
| **大模型** | DeepSeek / 通义千问（OpenAI 兼容接口） |
| **离线** | Web App Manifest · Service Worker |

---

## 📂 项目结构

```
错题本知识溯源整理助手/
│
├── app.py                  Flask 后端入口 · 全部 API 路由
├── db.py                   数据模型与数据访问层
├── report_export.py        Word / PDF 报表生成
├── requirements.txt        Python 依赖
├── 启动错题本.bat           Windows 一键启动脚本
│
├── static/                 前端资源
│   ├── index.html          单页应用模板
│   ├── app.js              Vue 应用逻辑
│   ├── style.css           主样式
│   ├── styles/             设计令牌 · 基础样式 · 动效
│   ├── sw.js               Service Worker 离线缓存
│   ├── manifest.webmanifest PWA 清单
│   ├── icons/              应用图标
│   └── vendor/             第三方库（Vue / ECharts / KaTeX / Lucide）
│
├── docs/                   项目文档
│   ├── 软件使用说明.md
│   ├── 功能模块说明.md
│   └── 录屏测试流程.md      全功能测试步骤
│
├── tools/                  开发与测试脚本
│   ├── e2e_check.py        端到端主流程回归
│   ├── test_fixes.py       安全与稳定性回归
│   ├── test_round3.py      输入校验与边界回归
│   ├── test_weak.py        薄弱指数算法回归
│   ├── test_integration.py AI / OCR 调用链
│   ├── test_reports.py     报表逐页核对
│   ├── test_pwa_offline.js Service Worker 离线回归
│   └── seed_demo.py        生成演示账号与数据
│
├── data.db                 数据库（gitignore）
├── secret.key              会话密钥（gitignore）
├── uploads/                用户上传文件（gitignore）
└── backups/                自动备份（gitignore）
```

---
## 🧪 测试

项目包含 **140 项自动化测试**，全部使用临时数据库，不影响真实数据：

```bash
python tools/e2e_check.py        # 20 项 · 主流程端到端
python tools/test_fixes.py       # 50 项 · 安全与稳定性
python tools/test_round3.py      # 24 项 · 输入校验与边界
python tools/test_weak.py        # 11 项 · 薄弱指数算法
python tools/test_integration.py #  8 项 · AI/OCR 调用链（2 项可选真实调用）
python tools/test_reports.py     # 27 项 · Word/PDF 报表逐页核对
```

| 测试文件 | 用例数 | 覆盖范围 |
|---|:---:|---|
| `e2e_check.py` | 20 | 注册登录 · 学科 · 知识点 · 错题 · 回收站 · 备份 · 报表 |
| `test_fixes.py` | 50 | 密码策略 · 会话 · 跨用户隔离 · 级联删除 · 上传校验 · CSRF · 限速 |
| `test_round3.py` | 24 | 输入校验 · 大小写账号 · 薄弱指数公式 · Cookie · 备份白名单 |
| `test_weak.py` | 11 | 薄弱指数算法稳定性 |
| `test_integration.py` | 8 | AI 推荐 · 流式输出 · 知识溯源 · OCR 解析 |
| `test_reports.py` | 27 | Word 段落表格 · PDF 每页文本 · 汇总一致性 |

---

## 📖 文档

| 文档 | 说明 |
|---|---|
| [软件使用说明](docs/软件使用说明.md) | 面向使用者的完整操作指南 |
| [功能模块说明](docs/功能模块说明.md) | 各模块设计与实现细节 |
| [录屏测试流程](docs/录屏测试流程.md) | 全功能演示步骤与验收清单 |

---

## 🔒 数据安全

- `data.db`、`secret.key`、`uploads/`、`backups/` 均已加入 `.gitignore`，**不会进入版本库**
- 会话级 CSRF Token 校验
- 上传文件按用户分目录隔离，跨用户访问返回 403
- 上传内容校验扩展名 + 文件头特征，请求体上限 32 MB
- 登录失败限速（同账号 + IP 15 分钟 5 次 → 锁定 5 分钟）
- 错题编辑乐观锁，版本冲突返回 409 并提示刷新
- 备份包导出时自动剔除 API Key

> ⚠️ **API Key 以明文存于本地 data.db**，仅适合个人单机使用，请勿将数据库文件外传。

---

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `5000` | 服务端口 |
| `WRONGBOOK_MAX_UPLOAD_MB` | `32` | 单请求体上限（MB） |
| `WRONGBOOK_HTTPS` | 未设置 | 设为 `1` 时启用 Secure Cookie（HTTPS 部署） |

---

## 📌 实现边界

- **OCR** 依赖本机安装 PaddleOCR 与 PaddlePaddle，未安装时自动降级为「仅保存图片」
- **AI 功能** 需用户自行配置大模型 API Key，未配置时只使用本地规则推荐
- **PWA 安装与系统通知** 需要 localhost 或 HTTPS 环境；通过局域网 IP 以 HTTP 访问时，部分手机浏览器不支持完整 PWA 能力，但可正常使用在线功能与 ICS 导出
- **回收站** 使用软删除，不会按时间自动清理，需手动彻底删除
- **SQLite** 适合单机个人使用，不适合多机或高并发部署
- 界面面向桌面端优化，同时适配移动端（≤640px）

---

<div align="center">

**本项目面向个人学习场景设计与实现**

如遇问题，请先尝试 Ctrl + Shift + R 硬刷新，或查看 [录屏测试流程](docs/录屏测试流程.md) 中的排查表

</div>