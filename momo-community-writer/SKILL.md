---
name: momo-community-writer
description: |
  社区文章创作与发布工作流，支持公众号与小红书。触发场景：用户提到"写公众号文章"、"小红书笔记"、"社区内容创作"、"帮我写篇推文"、"从选题到发布"等意图，或使用 /momo-community-writer 命令。工作流包括：需求发现、大纲迭代、初稿、正式文章、配图规划、图片生成、图文整合、全文审核、一键发布或降级导出。
---

# Community Article Writer

执行面向公众号与小红书的全流程写作任务。
默认遵循"先问清、再产出、可迭代、可追溯、可降级发布"。

## Workflow

按以下阶段顺序执行；每个阶段都允许与用户讨论并迭代：

1. `discovery`
2. `outline`
3. `draft`
4. `finalize`
5. `image-plan`
6. `image-gen`
7. `compose`
8. `review`
9. `publish`

在阶段切换前，输出当前阶段结果摘要与待确认项。

## Stage Instructions

### 1) discovery
通过问答收集并确认：
- 主题与核心观点
- 目标平台（公众号/小红书/双平台）
- 目标读者画像
- 内容目标（涨粉/转化/品牌认知/信息传达）
- 文风偏好（专业/故事化/口语化/犀利等）
- 长度与结构偏好
- 禁区与合规要求（敏感词、免责声明、品牌约束）

产出：
- `intent_brief`
- `constraints`
- `success_criteria`

### 2) outline
基于 discovery 产出结构化大纲，至少包含：
- 标题候选（3-5 个）
- 一级段落结构
- 每段关键论点与证据建议
- 平台差异化改写建议（公众号 vs 小红书）

与用户迭代直到确认。
产出：
- `approved_outline`

### 3) draft
按 `approved_outline` 生成初稿，保留可编辑标记位（示例、数据、案例待补）。
产出：
- `draft_v1`

### 4) finalize
与用户讨论修改方向后生成正式稿：
- 处理语气、节奏、逻辑衔接
- 输出平台版本（可单平台或双平台）
- 明确 CTA 与结尾策略

产出：
- `final_article_wechat`
- `final_article_xiaohongshu`（如需要）

### 5) image-plan
从正式稿中抽取配图需求，按段落输出：
- 配图位置（段前/段中/封面）
- 配图目的（解释/情绪/数据/转化）
- 构图建议与视觉元素
- 风格选项（由问答确认或用户自定义）
- 图片数量与比例建议

**执行方式**：Claude 直接分析文章，生成配图需求列表。

产出（写入 state.json）：
```json
{
  "image_requirements": [
    {"position": "封面", "purpose": "吸引点击", "prompt": "...", "style": "..."},
    {"position": "段中-第2段", "purpose": "解释概念", "prompt": "...", "style": "..."}
  ]
}
```

### 6) image-gen
先通过问答确认：
- provider（google/openai，默认 google）
- 风格偏好
- API Key 是否已配置（检查环境变量）

**执行步骤**：
1. 确认 provider 后，运行脚本：
   ```bash
   cd /Users/weitong/skills/mo-context/momo-community-writer
   python scripts/generate_images.py --provider <google|openai> --state state.json
   ```
2. 脚本读取 `state.json` 中的 `image_requirements`
3. 调用对应 provider API 生成图片
4. 结果写入 `state.json` 的 `image_assets` 字段

**失败处理**：
- 若 API Key 未配置：提示用户设置环境变量 `GOOGLE_API_KEY` 或 `OPENAI_API_KEY`
- 若生成失败：保留完整 prompt 到 `image_generation_log`，供手动重试

产出（脚本自动写入 state.json）：
```json
{
  "image_assets": [
    {"url": "https://...", "prompt": "...", "provider": "google"},
    {"url": "https://...", "prompt": "...", "provider": "google"}
  ],
  "image_generation_log": [...]
}
```

### 7) compose
将图片整合回文章。

**执行方式**：Claude 直接处理，读取 `state.json` 中的 `image_assets`，将图片 URL 插入到文章对应位置。

产出（写入 state.json）：
```json
{
  "composed_article": "# 标题\n\n![封面](图片URL)\n\n正文内容...\n\n![配图1](图片URL)\n\n..."
}
```

### 8) review
执行全文审核：
- 事实一致性与逻辑漏洞
- 风险与合规检查
- 平台规范检查（标题、字数、表达方式）
- 可读性与转化效果检查

**执行步骤**：
1. 可选运行脚本进行自动化检查：
   ```bash
   cd /Users/weitong/skills/mo-context/momo-community-writer
   python scripts/review_article.py --state state.json
   ```
2. Claude 结合脚本输出 + references/review_checklist.md 进行人工审核

**参考资源**：
- `references/review_checklist.md` - 审核清单
- `references/platform_wechat.md` - 公众号规范
- `references/platform_xiaohongshu.md` - 小红书规范

产出（写入 state.json）：
```json
{
  "review_report": {
    "passed": true,
    "issues": [],
    "suggestions": ["建议1", "建议2"]
  },
  "final_publishable_article": "最终可发布正文..."
}
```

### 9) publish
优先使用平台发布 adapter。若不可用或失败，自动降级为发布包导出。

**执行步骤**：
1. 确认目标平台（wechat/xiaohongshu）
2. 运行发布脚本：
   ```bash
   cd /Users/weitong/skills/mo-context/momo-community-writer
   python scripts/publish.py --platform <wechat|xiaohongshu> --state state.json
   ```
3. 脚本尝试 API 发布，失败则自动生成降级包

**失败处理**：
- 若 API 未配置：自动降级，生成 `export_package`
- 若发布失败：同样降级，输出手动发布步骤

产出（脚本自动写入 state.json）：

成功时：
```json
{
  "publish_result": {
    "success": true,
    "url": "https://mp.weixin.qq.com/...",
    "post_id": "xxx"
  }
}
```

降级时：
```json
{
  "export_package": {
    "article": "可发布正文",
    "title": "标题备选",
    "images": ["图片URL列表"],
    "tags": ["标签1", "标签2"],
    "manual_steps": ["1. 登录...", "2. 复制...", "3. 发布"]
  }
}

## Interaction Rules

- 每阶段先给"最小可评审版本"，再根据用户反馈迭代。
- 讨论时优先提出 3-5 个关键澄清问题，避免一次性问题过多。
- 用户未决定时提供默认建议并标注"可改"。
- 不伪造数据、案例、引用；不确定信息必须标注待确认。

## Configuration

使用前按需配置以下环境变量：

```bash
# 图片生成 Provider（至少配置一个）
GOOGLE_API_KEY=xxx          # Google 图片生成
OPENAI_API_KEY=xxx          # OpenAI 图片生成

# 公众号发布
WECHAT_APP_ID=xxx
WECHAT_APP_SECRET=xxx

# 小红书发布（如有 API 或 Cookie 方式）
XIAOHONGSHU_COOKIE=xxx
```

API Key 不写入仓库文件，不在对话中回显完整密钥。

## Provider Rules

- 图片 provider 默认支持：`google`, `openai`，可扩展其他 provider。
- 默认优先级可配置；若用户明确指定则严格遵循用户选择。

## Publishing Rules

- v1 目标平台：`wechat_official`, `xiaohongshu`
- 发布失败自动触发 `generic_export_adapter`
- 降级包至少包含：
  - 可发布正文（平台版本）
  - 图片与插入位置说明
  - 标题备选与标签建议
  - 手动发布步骤

## State Management

使用 `state.json` 记录工作流状态，支持中断续跑和回溯。

**文件位置**：`/Users/weitong/skills/mo-context/momo-community-writer/state.json`

**完整结构**：
```json
{
  "current_stage": "discovery",
  "version": 1,
  "history": [
    {"stage": "discovery", "version": 1, "changes": [], "artifacts": {}}
  ],

  "intent_brief": {},
  "constraints": {},
  "success_criteria": [],
  "approved_outline": {},
  "draft_v1": "",
  "final_article_wechat": "",
  "final_article_xiaohongshu": "",
  "image_requirements": [],
  "image_assets": [],
  "image_generation_log": [],
  "composed_article": "",
  "review_report": {},
  "final_publishable_article": "",
  "publish_result": {},
  "export_package": {}
}
```

**操作方式**：
- Claude 直接读写 `state.json`
- Python 脚本通过 `state.py` 模块读写

**恢复中断**：
```bash
# 查看当前阶段
cat state.json | grep current_stage

# 从指定阶段继续
python scripts/run_pipeline.py --stage <stage> --state state.json
```

## Example

用户：/momo-community-writer
助手：欢迎使用社区内容创作工作流！请告诉我你想写什么主题？

用户：我想写一篇关于 AI 编程工具的公众号文章
助手：好的，让我们开始 discovery 阶段。请问：
     1. 这篇文章的目标读者是谁？（如：初级开发者/技术管理者/普通用户）
     2. 你希望读者读完后的主要行动是什么？
     3. 文风偏好？专业严谨 / 轻松有趣 / 故事化 / 其他

用户：面向初级开发者，希望他们尝试使用 AI 编程工具，风格轻松有趣
助手：收到。以下是 intent_brief 摘要：
     - 主题：AI 编程工具入门
     - 平台：公众号
     - 读者：初级开发者
     - 目标：引导尝试
     - 风格：轻松有趣

     进入 outline 阶段，我先生成大纲草稿...

## Resources to Use

### 参考文档（Claude 按需读取）
| 文件 | 用途 |
|------|------|
| `references/platform_wechat.md` | 公众号规则（标题字数、排版、禁忌） |
| `references/platform_xiaohongshu.md` | 小红书规则（emoji、标签、封面） |
| `references/review_checklist.md` | 审核清单模板 |
| `references/style_playbooks.md` | 文风模板（专业/轻松/故事/犀利/干货） |

### Python 脚本（Claude 按需调用）

**工作目录**：
```bash
cd /Users/weitong/skills/mo-context/momo-community-writer
```

**脚本清单**：

| 脚本 | 用途 | 调用示例 |
|------|------|----------|
| `scripts/generate_images.py` | 图片生成 | `python scripts/generate_images.py --provider google --state state.json` |
| `scripts/review_article.py` | 自动审核 | `python scripts/review_article.py --state state.json` |
| `scripts/publish.py` | 发布/导出 | `python scripts/publish.py --platform wechat --state state.json` |
| `scripts/run_pipeline.py` | 流程编排 | `python scripts/run_pipeline.py --stage discovery --state state.json` |

**查看脚本帮助**：
```bash
python scripts/generate_images.py --help
python scripts/publish.py --help
```

### 状态文件

**位置**：`state.json`

**读取**：
```bash
cat state.json
```

**写入**：Claude 直接编辑，或脚本自动更新
