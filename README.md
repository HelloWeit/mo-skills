# mo-skills

个人工作辅助技能集合，为 Claude Code 提供领域专精能力。

## 简介

mo-skills 是一套可扩展的 Claude Code Skill 集合，旨在将重复性工作流程化、专业化。每个 Skill 封装了特定领域的最佳实践、工作流程和工具脚本，让 Claude 能够像专业人士一样完成任务。

**核心价值**：
- 将隐性知识显性化 —— 工作经验沉淀为可复用的流程
- 将碎片操作流程化 —— 多步骤任务一键完成
- 将专业门槛降低 —— 领域最佳实践内置其中

## 安装

### 方法一：注册插件市场（推荐）

在 Claude Code 中运行以下命令注册插件市场：

```
/plugin marketplace add HelloWeit/mo-skills
```

然后通过 UI 或命令安装：

```
# 通过 UI 安装
/plugin
# 选择 Browse and install plugins → mo-skills → 选择要安装的 Skill

# 或直接安装
/plugin install community-skills@mo-skills
```

### 方法二：快速安装

```bash
npx skills add HelloWeit/mo-skills
```

### 方法三：手动安装

```bash
# 克隆到 Claude Code skills 目录
git clone https://github.com/HelloWeit/mo-skills.git ~/.claude/skills/mo-skills

# 安装依赖（如需要）
cd ~/.claude/skills/mo-skills/momo-community-writer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 更新 Skills

1. 运行 `/plugin`
2. 切换到 **Marketplaces** 标签页
3. 选择 **mo-skills**
4. 选择 **Update marketplace**

也可以开启 **Enable auto-update** 自动获取最新版本。

## 当前 Skills

### momo-community-writer

社区文章创作与发布工作流，支持公众号与小红书。

**能力**：
- 需求发现 → 大纲迭代 → 初稿 → 正式文章 → 配图规划 → 图片生成 → 图文整合 → 全文审核 → 一键发布
- 双平台适配（公众号深度版 / 小红书精简版）
- 自动配图（支持 Google / OpenAI 图片生成）
- 合规审核与敏感词检测
- 发布失败自动降级为导出包

**触发方式**：
```
/momo-community-writer
```
或提及："写公众号文章"、"小红书笔记"、"社区内容创作"等意图。

[详细说明](./momo-community-writer/SKILL.md)

---

## 项目结构

```
mo-skills/
├── README.md                 # 本文件
├── momo-community-writer/    # 社区文章创作 Skill
│   ├── SKILL.md              # Skill 定义文件
│   ├── cli.py                # CLI 入口
│   ├── state.py              # 状态管理
│   ├── scripts/              # 功能脚本
│   │   ├── run_pipeline.py   # 流程编排
│   │   ├── generate_images.py
│   │   ├── review_article.py
│   │   ├── publish.py
│   │   └── ...
│   ├── adapters/             # 平台适配器
│   │   ├── wechat_official.py
│   │   ├── xiaohongshu.py
│   │   └── generic_export.py
│   ├── providers/            # 服务提供者
│   │   └── image/            # 图片生成
│   ├── references/           # 参考文档
│   │   ├── platform_wechat.md
│   │   ├── platform_xiaohongshu.md
│   │   ├── review_checklist.md
│   │   └── style_playbooks.md
│   └── requirements.txt
└── [future-skill]/           # 未来的 Skill...
```

## 添加新 Skill

每个 Skill 是一个独立目录，核心是 `SKILL.md` 文件：

```
your-new-skill/
├── SKILL.md          # 必需：Skill 定义
├── scripts/          # 可选：功能脚本
├── references/       # 可选：参考文档
└── requirements.txt  # 可选：Python 依赖
```

### SKILL.md 模板

```markdown
---
name: your-skill-name
description: |
  简短描述 Skill 的功能与触发场景。
---

# Skill 标题

详细说明 Claude 如何执行此 Skill...

## Workflow

1. `stage-1` - 阶段描述
2. `stage-2` - 阶段描述
...

## Resources to Use

| 文件 | 用途 |
|------|------|
| `scripts/xxx.py` | 功能说明 |
```

## 环境配置

部分 Skill 需要配置环境变量。环境变量按以下优先级加载：

1. CLI 环境变量（如 `OPENAI_API_KEY=xxx /skill ...`）
2. 系统环境变量 `process.env`
3. 项目级配置 `<cwd>/.mo-skills/.env`
4. 用户级配置 `~/.mo-skills/.env`

### 配置示例

```bash
# 创建用户级配置目录
mkdir -p ~/.mo-skills

# 创建 .env 文件
cat > ~/.mo-skills/.env << 'EOF'
# 图片生成
GOOGLE_API_KEY=xxx
OPENAI_API_KEY=xxx

# 公众号发布
WECHAT_APP_ID=xxx
WECHAT_APP_SECRET=xxx

# 小红书发布
XIAOHONGSHU_COOKIE=xxx
EOF
```

**注意**：请将 `.env` 文件添加到 `.gitignore`，避免泄露密钥。

## 自定义扩展

所有 Skill 支持通过 `EXTEND.md` 文件进行自定义扩展，可以覆盖默认配置、添加自定义预设等。

**扩展文件路径**（按优先级）：

1. `.mo-skills/<skill-name>/EXTEND.md` - 项目级（团队/项目特定设置）
2. `~/.mo-skills/<skill-name>/EXTEND.md` - 用户级（个人偏好）

## 设计原则

1. **可中断可恢复** —— 所有流程支持状态持久化，随时中断、随时继续
2. **先问清再产出** —— 关键决策前与用户确认，避免方向偏差
3. **可降级可导出** —— 自动化失败时有兜底方案
4. **不伪造不杜撰** —— 不确定的信息明确标注，保持可信

## 许可证

MIT
