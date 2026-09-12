# 错题本知识溯源整理助手

一个面向个人学习者的本地错题管理与知识溯源工具，核心目标是“搞清楚每道错题背后到底哪个知识点没掌握”。

## 功能概览

- 用户账号：注册、登录、改名、改密、重置密码、删除账号、数据隔离
- 错题录入：手动录入、拍照 OCR、图片上传、PDF/Word 导入
- 错题管理：筛选、详情、编辑、批量操作、回收站恢复
- 知识溯源：AI 溯源、思维导图、用户确认与反馈学习
- 知识树：学科为中心、多级知识点、搜索和目录管理
- 薄弱分析：完整薄弱指数、30 天趋势、复习优先级
- 复习模式：今日推荐、复习计划、提醒、掌握状态标记
- 知识库：概念回顾、典型例题、变式练习、AI 精简
- 学习资源：教材页码、网课链接、笔记、附件、AI 推荐
- 知识图谱：分层导图、树图、旭日图
- 统计报表：状态分布、薄弱排行、汇总指标
- 数据备份：单一 ZIP 数据包导出与恢复

## 技术栈

- 后端：Flask + SQLAlchemy
- 数据库：SQLite
- 前端：Vue 3 + Axios
- 图表：ECharts
- 公式渲染：KaTeX
- OCR：PaddleOCR
- 文档解析：python-docx + PyMuPDF
- 大模型：DeepSeek / 通义千问

## 运行

Windows 用户可以直接双击：

```text
启动错题本.bat
```

脚本会自动检查依赖、启动服务并打开浏览器。

命令行方式：

```bash
pip install -r requirements.txt
python app.py
```

访问：http://localhost:5000

如需生成演示数据，可单独运行：

```bash
python tools/seed_demo.py
```

演示账号：

- 账号：`demo`
- 密码：`demo123`

## 文档

- [软件使用说明](docs/软件使用说明.md)
- [功能模块说明](docs/功能模块说明.md)
- [演示截图](output/playwright/screenshots)
- [演示视频](output/playwright/video/demo_video.webm)

## 项目结构

```text
app.py                  Flask 后端入口
db.py                   数据模型与数据访问
static/                 前端页面、样式和脚本
tools/seed_demo.py      演示数据生成
tools/record_demo.js    Playwright 演示录屏
docs/                   使用说明和功能模块文档
output/playwright/      演示截图和视频
```

## 数据安全

数据库、上传附件、密钥文件和备份默认加入 `.gitignore`，不会提交到 Git 仓库。
