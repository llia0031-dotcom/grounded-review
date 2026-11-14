"""Build the policy source files used by the agent and the quote checker.

Input: text extracted from official pages (policies/raw/, made from the HTML saved on 2026-11-13).
Output: policies/sources/*.md. The article and section text is copied unchanged; only page chrome
(menus, footers, market tables) is dropped and a short header with the URL is added.

Run: python policies/build_sources.py
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "sources"
FETCHED = "2026-11-13 (MYT)"


def write(name: str, header: list[str], body: str) -> None:
    OUT.mkdir(exist_ok=True)
    text = "\n".join(header) + "\n\n" + body.strip() + "\n"
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"{name}: {len(body)} characters")


def advertising_law() -> None:
    t = (RAW / "bj.txt").read_text(encoding="utf-8")
    start = t.index("第一章 总则\n第一条")
    end = t.index("本法自2015年9月1日起施行。") + len("本法自2015年9月1日起施行。")
    body = t[start:end]
    # Chapter headings become Markdown headings; article lines stay as they are.
    body = re.sub(r"(?m)^(第[一二三四五六]章 .+)$", r"## \1", body)
    write(
        "cn-advertising-law-2021.md",
        [
            "# 中华人民共和国广告法（2021年修正）",
            "",
            "- Source: Beijing Municipal Administration for Market Regulation, https://scjgj.beijing.gov.cn/cxfw/flfgcxfw/ggl/202204/t20220401_2646388.html",
            "- Cross-checked against: Shanghai Municipal Administration for Market Regulation, https://scjgj.sh.gov.cn/903/20250924/7e43b9954ca24b349488e5b464e83ac8.html (all 74 articles identical after removing whitespace, except one punctuation mark in Article 57)",
            f"- Fetched: {FETCHED}",
            "- Text of the law as published; public domain under Article 5 of the Copyright Law of the PRC.",
        ],
        body,
    )


def samr_guide() -> None:
    t = (RAW / "samr-abs-guide.txt").read_text(encoding="utf-8")
    start = t.index("广告绝对化用语执法指南\n为规范")
    end = t.index("十二、市场监管部门可以依照有关规定，制定广告绝对化用语轻微违法行为依法免予处罚清单并进行动态调整。")
    end = t.index("\n", end)
    write(
        "cn-samr-absolute-terms-guide-2023.md",
        [
            "# 广告绝对化用语执法指南（市场监管总局公告2023年第6号）",
            "",
            "- Source: State Administration for Market Regulation, https://www.samr.gov.cn/ggjgs/tzgg/art/2023/art_183b5cb48d9e4f0dba67f9f912a913ba.html",
            f"- Fetched: {FETCHED}",
            "- Official enforcement guidance; text as published.",
        ],
        t[start:end],
    )


TIKTOK = {
    "tt-misleading.md": ("tiktok-misleading-and-false-content.md", "https://ads.tiktok.com/help/article/tiktok-ads-policy-misleading-and-false-content?lang=en"),
    "tt-weight-management.md": ("tiktok-weight-management.md", "https://ads.tiktok.com/help/article/tiktok-ads-policy-weight-management?lang=en"),
    "tt-alcohol.md": ("tiktok-alcohol.md", "https://ads.tiktok.com/help/article/tiktok-ads-policy-alcohol?lang=en"),
    "tt-deceptive-practices.md": ("tiktok-deceptive-practices.md", "https://ads.tiktok.com/help/article/tiktok-ads-policy-deceptive-practices?lang=en"),
    "tt-financial-services.md": ("tiktok-financial-services.md", "https://ads.tiktok.com/help/article/tiktok-ads-policy-financial-services?lang=en"),
    "tt-healthcare-pharmaceuticals.md": ("tiktok-healthcare-pharmaceuticals.md", "https://ads.tiktok.com/help/article/tiktok-ads-policy-healthcare-pharmaceuticals?lang=en"),
}


def tiktok() -> None:
    for raw_name, (out_name, url) in TIKTOK.items():
        if not (RAW / raw_name).exists():
            print(f"{raw_name}: missing. Save {url} as Markdown (section headings as '## ') to policies/raw/{raw_name}")
            continue
        t = (RAW / raw_name).read_text(encoding="utf-8")
        title = t.splitlines()[0].lstrip("# ").replace(" | TikTok Advertising Policies", "")
        if title == "Business Resource Center":
            title = {"tiktok-alcohol.md": "Alcohol", "tiktok-financial-services.md": "Financial Services"}[out_name]
        body = t[t.index("## Principle"):]
        for stop in ("## Market-specific requirements", "Log in for a personalized experience"):
            if stop in body:
                body = body[: body.index(stop)]
        write(
            out_name,
            [
                f"# TikTok Advertising Policies: {title}",
                "",
                f"- Source: {url}",
                f"- Fetched: {FETCHED}. Global sections only; market-specific tables omitted.",
                "- Copyright TikTok. Kept locally for research; a public version links to the page and names the section instead of copying it.",
            ],
            body,
        )


if __name__ == "__main__":
    advertising_law()
    samr_guide()
    tiktok()
