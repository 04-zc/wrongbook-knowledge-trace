# test1 全功能测试报告

- 测试时间：2026-09-12 15:20:14
- 结果：42/42 项通过
- 修复记录：测试发现“AI 单题解答”错误要求知识点 ID，已修复并复测通过。

| 功能 | 结果 | 说明 |
|---|---|---|
| test1 登录 | 通过 | {"user":{"username":"test1"}}
 |
| 创建测试学科 | 通过 |  |
| 知识点树父子层级 | 通过 |  |
| 错题录入 | 通过 |  |
| 按知识点筛选错题 | 通过 |  |
| 编辑错题 | 通过 |  |
| 批量修改状态 | 通过 |  |
| 批量关联知识点 | 通过 |  |
| 薄弱指数完整计算 | 通过 | {'error_count': 2, 'recent_errors': 2, 'decay_score': 2.0, 'weak_index': 10.0} |
| 30 天趋势接口 | 通过 |  |
| 复习优先级接口 | 通过 |  |
| 创建复习计划 | 通过 | {'overdue': 1, 'today': 3, 'total': 4} |
| 完成复习计划 | 通过 |  |
| 知识库内容新增 | 通过 |  |
| 知识库内容修改 | 通过 |  |
| 学习资源新增 | 通过 |  |
| 学习资源修改 | 通过 |  |
| 知识溯源导图生成 | 通过 |  |
| 导图保存 | 通过 |  |
| 溯源未写入知识树 | 通过 |  |
| AI 知识点推荐接口 | 通过 | {"auto_bound":[{"confidence":0.98,"decision":"auto","feedback_boost":0,"id":44,"is_auto":1,"name":"\u5e42\u51fd\u6570\u6 |
| AI 概念回顾 | 通过 | {"content":"\u81ea\u52a8\u5316\u5bfc\u6570\u6307\u7528\u7b97\u6cd5\u7cbe\u786e\u8ba1\u7b97\u51fd\u6570\u5728\u67d0\u70b9 |
| AI 典型例题 | 通过 | {"mode":"typical","questions":[{"analysis":"\u9010\u9879\u6c42\u5bfc\uff1a\n(x\u00b3)' = 3x\u00b2\n(-3x\u00b2)' = -6x\n( |
| AI 变式练习 | 通过 | {"mode":"variant","questions":[{"analysis":"\u65b9\u6cd5\u4e00\uff1a\u5148\u5c55\u5f00\u518d\u6c42\u5bfc\u3002\nf(x) = ( |
| AI 知识点精要 | 通过 | {"content":"\u81ea\u52a8\u5316\u5bfc\u6570\u77e5\u8bc6\u5361\u7247\n\n\u4e00\u3001\u6838\u5fc3\u6982\u5ff5\n\u81ea\u52a8 |
| AI 学习资源推荐 | 通过 | {"mode":"resources","resources":[{"content":"\u5efa\u8bae\u5728\u5b66\u5b8c\u94fe\u5f0f\u6cd5\u5219\u548c\u8ba1\u7b97\u5 |
| AI 单题解答 | 通过 | {"content":"1. \u8fd9\u9053\u9898\u8003\u67e5\u7684\u77e5\u8bc6\u70b9\n\u672c\u9898\u8003\u67e5\u7684\u662f\u57fa\u672c\ |
| OCR 图片识别 | 通过 | {"text":"\u5df2\u77e5\u51fd\u6570f(x)=2x+1\uff0c\u6c42\u5bfc","url":"/uploads/ocr_2cbb7b10.png"}
 |
| Word 导入解析 | 通过 | {"count":2,"filename":"auto.docx","mode":"\u6587\u672c\u63d0\u53d6","questions":[{"title_text":"Word \u81ea\u52a8\u6d4b\ |
| PDF 导入解析 | 通过 | {"count":2,"filename":"auto.pdf","mode":"\u6587\u672c\u63d0\u53d6","questions":[{"title_text":"PDF auto test question on |
| 知识图谱接口 | 通过 |  |
| 统计报表接口 | 通过 |  |
| 移入回收站 | 通过 |  |
| 回收站恢复 | 通过 |  |
| 彻底删除 | 通过 |  |
| 导出单一数据包 | 通过 |  |
| 导入数据包 | 通过 | {"ok":true,"stats":{"knowledge_points":24,"questions":9,"subjects":8}}
 |
| 恢复复习记录和薄弱指数 | 通过 | error_count=2 |
| 账号修改密码 | 通过 |  |
| 账号改名 | 通过 |  |
| 账号重置密码 | 通过 |  |
| 账号删除 | 通过 |  |
