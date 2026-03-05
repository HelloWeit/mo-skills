#!/usr/bin/env python3
"""
全文审核脚本

检查文章合规性、敏感词、平台规范等。

Usage:
    python scripts/review_article.py --state state.json
    python scripts/review_article.py --help
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import load_state, save_state


# ============================================================
# 敏感词库
# ============================================================

# 广告法违禁词（绝对化用语）
ABSOLUTE_WORDS = [
    "最", "第一", "唯一", "绝对", "保证", "必定", "一定",
    "顶级", "极品", "极致", "完美", "永久", "终身",
    "100%", "首选", "独家", "首发", "巅峰", "终极",
    "国家级", "世界级", "全网", "全民", "史无前例",
]

# 平台敏感词
PLATFORM_SENSITIVE_WORDS = {
    "wechat": [
        "诱导分享", "诱导关注", "强制关注", "必转",
        "朋友圈", "刷屏", "火爆", "疯传",
    ],
    "xiaohongshu": [
        "加微信", "私信我", "找我", "联系我",
        "二维码", "扫码", "外链", "引流",
        "淘宝", "京东", "拼多多", "天猫",
    ]
}

# 政治敏感词
POLITICAL_SENSITIVE_WORDS = [
    # 这里不列举具体词汇，实际使用时需要补充
]

# 低俗词汇
VULGAR_WORDS = [
    # 这里不列举具体词汇，实际使用时需要补充
]

# 合并所有敏感词
ALL_SENSITIVE_WORDS = (
    ABSOLUTE_WORDS +
    POLITICAL_SENSITIVE_WORDS +
    VULGAR_WORDS
)


# ============================================================
# 平台规则
# ============================================================

PLATFORM_LIMITS = {
    "wechat": {
        "title_max": 64,
        "content_max": None,  # 无限制
        "cover_ratio": ["2.35:1", "16:9", "1:1"],
        "image_max_size_mb": 5,
    },
    "xiaohongshu": {
        "title_max": 20,
        "content_max": 1000,
        "image_count_min": 3,
        "image_count_max": 9,
    }
}

# 标题党/震惊体模式
CLICKBAIT_PATTERNS = [
    r"震惊.*",
    r"必看.*",
    r"不转不是.*",
    r"看完.*沉默",
    r"看完.*流泪",
    r"吓死.*",
    r"疯传.*",
]


# ============================================================
# 检查函数
# ============================================================

def check_sensitive_words(text: str, platform: str = None) -> dict:
    """检查敏感词，返回发现的敏感词分类"""
    found = {
        "absolute": [],
        "platform": [],
        "political": [],
        "vulgar": [],
    }

    # 检查绝对化用语
    for word in ABSOLUTE_WORDS:
        if word in text:
            found["absolute"].append(word)

    # 检查平台敏感词
    if platform and platform in PLATFORM_SENSITIVE_WORDS:
        for word in PLATFORM_SENSITIVE_WORDS[platform]:
            if word in text:
                found["platform"].append(word)

    # 检查政治敏感词
    for word in POLITICAL_SENSITIVE_WORDS:
        if word in text:
            found["political"].append(word)

    # 检查低俗词汇
    for word in VULGAR_WORDS:
        if word in text:
            found["vulgar"].append(word)

    return found


def check_length(article: str, title: str, platform: str) -> list[str]:
    """检查字数限制"""
    issues = []
    limits = PLATFORM_LIMITS.get(platform, {})

    # 检查标题长度
    if title and limits.get("title_max"):
        if len(title) > limits["title_max"]:
            issues.append(
                f"标题超长: {len(title)} > {limits['title_max']} 字"
            )

    # 检查正文长度
    if limits.get("content_max"):
        content_len = len(article)
        if content_len > limits["content_max"]:
            issues.append(
                f"正文超长: {content_len} > {limits['content_max']} 字"
            )

    return issues


def check_clickbait(title: str) -> list[str]:
    """检查标题党"""
    issues = []
    if title:
        for pattern in CLICKBAIT_PATTERNS:
            if re.search(pattern, title):
                issues.append(f"标题党嫌疑: 匹配模式 '{pattern}'")
    return issues


def check_structure(article: str) -> list[str]:
    """检查文章结构"""
    issues = []
    suggestions = []

    paragraphs = [p.strip() for p in article.split("\n\n") if p.strip()]

    # 检查段落数量
    if len(paragraphs) < 3:
        suggestions.append("文章段落较少，建议增加结构层次")

    # 检查段落长度
    for i, para in enumerate(paragraphs):
        if len(para) > 500:
            issues.append(f"第 {i+1} 段落过长 ({len(para)} 字)，建议拆分")

    # 检查是否有过长的句子
    sentences = re.split(r"[。！？]", article)
    for i, sent in enumerate(sentences):
        if len(sent) > 200:
            suggestions.append(f"第 {i+1} 句子较长，考虑拆分以提高可读性")

    return issues, suggestions


def check_readability(article: str) -> list[str]:
    """检查可读性"""
    suggestions = []

    # 检查是否有过多的连续感叹号
    if "！！" in article or "！！！" in article:
        suggestions.append("建议减少连续感叹号的使用")

    # 检查是否有过多的问号
    if "？？" in article or "？？？" in article:
        suggestions.append("建议减少连续问号的使用")

    # 检查数字和英文混合
    if re.search(r"[a-zA-Z]\d+|\d+[a-zA-Z]", article):
        suggestions.append("建议在数字和英文之间添加空格")

    return suggestions


def review_article(
    article: str,
    platform: str = "wechat",
    title: str = None
) -> dict:
    """执行全文审核"""
    issues = []
    warnings = []
    suggestions = []

    # 1. 敏感词检查
    sensitive = check_sensitive_words(article, platform)
    for category, words in sensitive.items():
        if words:
            category_names = {
                "absolute": "绝对化用语",
                "platform": "平台敏感词",
                "political": "政治敏感词",
                "vulgar": "低俗词汇"
            }
            issues.append(
                f"发现{category_names.get(category, category)}: {', '.join(set(words))}"
            )

    # 2. 标题检查
    if title:
        # 标题长度
        title_issues = check_length(article, title, platform)
        issues.extend(title_issues)

        # 标题党检查
        clickbait_issues = check_clickbait(title)
        warnings.extend(clickbait_issues)

    # 3. 结构检查
    structure_issues, structure_suggestions = check_structure(article)
    issues.extend(structure_issues)
    suggestions.extend(structure_suggestions)

    # 4. 可读性检查
    readability_suggestions = check_readability(article)
    suggestions.extend(readability_suggestions)

    # 5. 内容长度建议
    word_count = len(article)
    if word_count < 300:
        suggestions.append("文章内容较短，建议补充更多实质性内容")
    elif word_count > 5000:
        suggestions.append("文章较长，考虑拆分为系列文章或精简内容")

    # 6. 平台特定检查
    if platform == "xiaohongshu":
        # 检查是否有 emoji
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "]+"
        )
        emojis = emoji_pattern.findall(article)
        if len(emojis) > 20:
            suggestions.append("emoji 使用较多，建议适当减少")

    # 计算严重程度
    critical_count = len(issues)
    warning_count = len(warnings)

    passed = critical_count == 0

    return {
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "platform": platform,
        "word_count": word_count,
        "title": title,
        "summary": {
            "critical": critical_count,
            "warnings": warning_count,
            "suggestions": len(suggestions)
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="全文审核脚本 - 检查文章合规性、敏感词、平台规范",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/review_article.py
    python scripts/review_article.py --platform xiaohongshu --state state.json
    python scripts/review_article.py --title "标题文字" --state state.json

检查项目:
    - 绝对化用语 (最、第一、唯一等)
    - 平台敏感词 (公众号: 诱导分享; 小红书: 外链、引流)
    - 字数限制 (小红书标题 20 字、正文 1000 字)
    - 标题党/震惊体
    - 文章结构和可读性

输出:
    审核通过: state.json 中的 review_report.passed = true
    审核失败: state.json 中的 review_report.issues 列出问题
        """
    )
    parser.add_argument(
        "--platform", "-p",
        choices=["wechat", "xiaohongshu"],
        default="wechat",
        help="目标平台 (default: wechat)"
    )
    parser.add_argument(
        "--state", "-s",
        default="state.json",
        help="状态文件路径 (default: state.json)"
    )
    parser.add_argument(
        "--title", "-t",
        help="文章标题 (用于标题长度和标题党检查)"
    )

    args = parser.parse_args()

    # 加载状态
    state = load_state(args.state)

    article = state.composed_article or state.final_publishable_article
    if not article:
        print("[error] 未找到文章内容，请先完成 compose 阶段")
        sys.exit(1)

    # 获取标题
    title = args.title
    if not title and state.approved_outline:
        # 尝试从大纲获取标题
        titles = state.approved_outline.get("titles", [])
        if titles:
            title = titles[0]

    print(f"[info] 开始审核文章")
    print(f"[info] 平台: {args.platform}")
    print(f"[info] 字数: {len(article)}")
    if title:
        print(f"[info] 标题: {title} ({len(title)} 字)")

    # 执行审核
    report = review_article(article, args.platform, title)
    state.review_report = report

    # 输出结果
    print("\n" + "=" * 50)

    if report["passed"]:
        state.final_publishable_article = article
        print("[✓] 审核通过")
    else:
        print(f"[✗] 审核未通过，发现 {len(report['issues'])} 个问题")

    # 输出问题
    if report["issues"]:
        print("\n[问题]:")
        for issue in report["issues"]:
            print(f"  ✗ {issue}")

    # 输出警告
    if report["warnings"]:
        print("\n[警告]:")
        for warning in report["warnings"]:
            print(f"  ⚠ {warning}")

    # 输出建议
    if report["suggestions"]:
        print("\n[建议]:")
        for sug in report["suggestions"]:
            print(f"  💡 {sug}")

    # 保存状态
    save_state(state, args.state)
    print(f"\n[info] 审核报告已写入 {args.state}")


if __name__ == "__main__":
    main()
