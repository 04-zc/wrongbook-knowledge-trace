# 错题本知识溯源整理助手

面向个人学习者的本地错题管理与知识溯源工具。系统围绕“错题录入 → 知识点识别 → 知识溯源 → 薄弱分析 → 复习计划 → 掌握反馈”形成闭环。

## 当前功能

- 用户账号：注册、登录、改名、改密、重置密码、删除账号、用户数据隔离
- 错题录入：手动录入、摄像头拍照、图片上传、OCR、PDF/Word 导入
- 错题管理：分页、关键词搜索、学科/知识点/状态筛选、批量关联、批量状态修改、回收站
- 公式排版：支持 LaTeX 输入和 KaTeX 实时渲染
- 知识树：学科为根、多级知识点、逐层展开、搜索定位、增删改查
- 知识溯源：AI 置信度分档、用户确认、独立思维导图、反馈学习
- 薄弱分析：累计错误、时间衰减、近 7 天重复错误、30 天趋势、复习优先级
- 复习模式：今日推荐、自定义计划、浏览器提醒、逾期提示、`.ics` 日历导出
- AI 学习：概念回顾、知识点精要、典型例题、变式练习、单题解答，支持流式输出
- 知识库与资源：知识点说明、AI 内容、教材页码、网课、笔记、附件
- 知识图谱：分层导图、树图、旭日图
- 统计报表：汇总报表、状态分布、薄弱排行，支持 Word/PDF 导出
- PWA：可添加到手机主屏幕，离线时可查看已缓存数据
- 数据备份：单一 ZIP 数据包导出与恢复
- 性能优化：错题分页、首页轻量加载、SQLite 查询索引

## 技术栈

- 后端：Flask + SQLAlchemy
- 数据库：SQLite
- 前端：Vue 3 + Axios
- 图表：ECharts
- 公式：KaTeX
- OCR：PaddleOCR
- 文档：python-docx、PyMuPDF
- 大模型：DeepSeek / 通义千问（OpenAI 兼容接口）
- 离线：Web App Manifest + Service Worker

## 启动

Windows 可直接双击：

```text
启动错题本.bat
```

脚本会自动定位 Python、检查依赖、启动服务并打开浏览器。

命令行方式：

```bash
pip install -r requirements.txt
python app.py
```

访问：http://localhost:5000

生成演示数据：

```bash
python tools/seed_demo.py
```

演示账号：`demo` / `demo123`

## 文档

- [软件使用说明](docs/软件使用说明.md)
- [功能模块说明](docs/功能模块说明.md)
- [Word 版使用说明](docs/软件使用说明.docx)
- [Word 版功能模块说明](docs/功能模块说明.docx)
- [演示截图](output/playwright/screenshots)
- [演示视频](output/playwright/video/demo_video.webm)

## 项目结构

```text
app.py                       Flask 后端入口
db.py                        数据模型与数据访问
report_export.py             Word / PDF 报表导出
static/                       前端页面、样式、脚本和 PWA 资源
static/manifest.webmanifest   PWA 应用清单
static/sw.js                  Service Worker 离线缓存
tools/seed_demo.py            演示数据生成
tools/e2e_test1.py            全功能回归测试
tools/record_demo.js          演示录屏
tools/build_docs.py           生成 Word 说明文档
docs/                         使用说明和功能模块文档
output/playwright/            演示截图和视频
uploads/                      用户上传图片与附件
```

## PWA 说明

在 `localhost` 或 HTTPS 环境下，手机浏览器可以“添加到主屏幕”。断网时可查看已缓存数据；账号切换或退出时会清理当前用户的离线数据。

通过局域网 IP 使用普通 HTTP 时，部分手机浏览器不会开放完整 PWA 安装和系统通知能力，此时仍可正常使用在线页面和 `.ics` 日历导出。

## 数据安全

`data.db`、`secret.key`、`uploads/` 和 `backups/` 默认加入 `.gitignore`，不会提交到远端仓库。建议定期在账号设置中导出数据包。

## 实现边界

- OCR 依赖本机 PaddleOCR 和 PaddlePaddle，大模型功能依赖用户配置的 API Key。
- PWA 安装和系统通知需要 `localhost` 或 HTTPS；浏览器通知只在页面打开时检查。
- 回收站使用软删除，当前不会按时间自动清理，需要用户手动彻底删除。
- SQLite 适合单机个人使用，不适合多机或高并发部署。
- 上传接口尚未统一设置扩展名白名单和请求体大小限制，部署到公网前应补充。
