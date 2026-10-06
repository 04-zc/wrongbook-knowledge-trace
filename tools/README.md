# tools 目录说明

本目录存放开发期辅助脚本，不是系统运行依赖，也不参与 Flask 应用启动。

## 测试脚本

四个脚本都使用临时数据库，不会读写项目的 `data.db`。

| 脚本 | 用途 |
| --- | --- |
| `e2e_check.py` | 主流程端到端回归：注册、登录、学科、知识点、错题、回收站、备份、报表 |
| `test_fixes.py` | 安全与稳定性回归：密码、会话、跨用户隔离、级联删除、上传校验、设置白名单 |
| `test_round3.py` | 输入校验、用户名大小写、薄弱指数公式、Cookie、备份表白名单 |
| `test_weak.py` | 薄弱指数算法回归：固定参考规模公式、错误事件口径、稳定性 |
| `test_integration.py` | AI/OCR 调用链：mock 模型与 OCR 引擎，可选真实调用 |
| `test_reports.py` | 报表逐页核对：Word 段落表格、PDF 每页文本、汇总接口一致性 |
| `test_pwa_offline.js` | Service Worker 离线回归：缓存策略、上传文件隔离、版本升级清理 |

运行方式：

```powershell
python tools/e2e_check.py
python tools/test_fixes.py
python tools/test_round3.py
python tools/test_weak.py
python tools/test_integration.py
python tools/test_reports.py
node tools/test_pwa_offline.js
```

## 演示脚本

以下脚本只用于答辩演示数据准备和录屏，不属于测试，也不应放进运行部署包。

| 脚本 | 用途 |
| --- | --- |
| `seed_demo.py` | 重建 `demo / demo123` 演示账号和示例数据 |
| `record_demo.js` | 用 Playwright 录制一段界面演示视频 |
| `reshoot.js` | 用 Playwright 重新截取首页、复习、薄弱分析、报表截图 |

`record_demo.js`、`reshoot.js` 需要本机已有 Playwright 运行环境，并通过环境变量传入依赖路径。
