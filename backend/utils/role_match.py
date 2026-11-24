"""Match scraped listings to the positions chosen on the search form."""

from __future__ import annotations

import re
from typing import Optional

# English query is used on GaijinPot. Japanese query is used on Mynavi.
ROLES = (
    {
        "label": "Software Engineer",
        "en": "software engineer",
        "ja": "ソフトウェアエンジニア",
        "terms": (
            "software",
            "ソフトウェア",
            "developer",
            "programmer",
            "プログラマ",
            "バックエンド",
            "フロントエンド",
            "backend",
            "frontend",
            "full stack",
            "fullstack",
            "フルスタック",
            "webエンジニア",
            "システムエンジニア",
        ),
    },
    {
        "label": "Data Analyst",
        "en": "data analyst",
        "ja": "データアナリスト",
        "terms": ("data analyst", "データ分析", "データアナリスト", "data scientist", "データサイエンティスト"),
    },
    {
        "label": "AI / Machine Learning Engineer",
        "en": "machine learning engineer",
        "ja": "機械学習エンジニア",
        "terms": ("machine learning", "機械学習", "ai engineer", "aiエンジニア", "人工知能", "ml engineer"),
    },
    {
        "label": "Sales Representative",
        "en": "sales",
        "ja": "営業",
        "terms": ("sales", "営業", "セールス", "account executive", "法人営業"),
    },
    {
        "label": "Marketing Specialist",
        "en": "marketing",
        "ja": "マーケティング",
        "terms": ("marketing", "マーケティング", "宣伝"),
    },
    {
        "label": "Business Analyst",
        "en": "business analyst",
        "ja": "ビジネスアナリスト",
        "terms": ("business analyst", "ビジネスアナリスト", "事業分析"),
    },
    {
        "label": "Business Development Associate",
        "en": "business development",
        "ja": "事業開発",
        "terms": ("business development", "事業開発", "新規開拓"),
    },
    {
        "label": "Human Resources Specialist",
        "en": "human resources",
        "ja": "人事",
        "terms": ("human resources", "人事", "recruiter", "採用"),
    },
    {
        "label": "Accountant / Financial Analyst",
        "en": "accountant",
        "ja": "経理",
        "terms": ("accountant", "経理", "財務", "financial analyst", "会計"),
    },
    {
        "label": "Customer Support Representative",
        "en": "customer support",
        "ja": "カスタマーサポート",
        "terms": ("customer support", "カスタマーサポート", "customer success", "カスタマーサクセス", "コールセンター"),
    },
    {
        "label": "Administrative Assistant",
        "en": "administrative assistant",
        "ja": "一般事務",
        "terms": ("administrative", "事務", "総務", "office assistant"),
    },
    {
        "label": "Project Manager",
        "en": "project manager",
        "ja": "プロジェクトマネージャー",
        "terms": ("project manager", "プロジェクトマネージャー", "プロジェクトマネージャ", "project lead"),
    },
    {
        "label": "Mechanical Engineer",
        "en": "mechanical engineer",
        "ja": "機械エンジニア",
        "terms": ("mechanical", "機械"),
    },
    {
        "label": "Electrical Engineer",
        "en": "electrical engineer",
        "ja": "電気エンジニア",
        "terms": ("electrical", "電気"),
    },
    {
        "label": "Civil Engineer",
        "en": "civil engineer",
        "ja": "土木",
        "terms": ("civil", "土木", "建築"),
    },
    {
        "label": "Graphic / UI Designer",
        "en": "ui designer",
        "ja": "デザイナー",
        "terms": ("designer", "デザイナー", "ui designer", "ux designer"),
    },
    {
        "label": "Translator / Interpreter",
        "en": "translator",
        "ja": "翻訳",
        "terms": ("translator", "interpreter", "翻訳", "通訳"),
    },
    {
        "label": "Teacher / English Instructor",
        "en": "english teacher",
        "ja": "英語講師",
        "terms": ("teacher", "instructor", "講師", "教師", "英会話"),
    },
    {
        "label": "Hotel / Hospitality Staff",
        "en": "hotel staff",
        "ja": "ホテル",
        "terms": ("hotel", "hospitality", "ホテル", "宿泊"),
    },
    {
        "label": "Supply Chain / Logistics Specialist",
        "en": "logistics",
        "ja": "物流",
        "terms": ("supply chain", "logistics", "物流", "サプライチェーン"),
    },
)

ROLE_BY_LABEL = {role["label"]: role for role in ROLES}
ROLE_LABELS = tuple(role["label"] for role in ROLES)

# Generic "engineer" titles belong to software only when they are not another trade.
_SOFTWARE_BLOCK = (
    "営業",
    "sales",
    "機械",
    "mechanical",
    "電気",
    "electrical",
    "土木",
    "civil",
    "デザイン",
    "designer",
    "翻訳",
    "translator",
    "教師",
    "teacher",
    "講師",
    "ホテル",
    "hotel",
    "物流",
    "logistics",
    "人事",
    "経理",
    "会計",
    "マーケティング",
    "marketing",
    "機械学習",
    "machine learning",
    "aiエンジニア",
    "ai engineer",
)

_JUNIOR = ("未経験", "新卒", "第二新卒", "intern", "インターン", "entry", "junior", "trainee")
_SENIOR = ("senior", "director", "manager", "マネージャー", "管理職", "部長", "lead", "リーダー")
_WORK_ARRANGEMENTS = {"Any", "Remote", "On-site", "Hybrid"}


def search_query(label: str, language: str) -> str:
    """Keyword to type into a job board for this position."""
    role = ROLE_BY_LABEL.get(label)
    if role is None:
        return label
    return role["ja"] if language == "ja" else role["en"]


def title_matches(title: str, selected: list[str]) -> bool:
    """True when the listing title fits one of the selected positions."""
    if not title or not selected:
        return False
    folded = title.lower()
    for label in selected:
        role = ROLE_BY_LABEL.get(label)
        if role is None:
            if label.lower() in folded:
                return True
            continue
        if any(term.lower() in folded for term in role["terms"]):
            return True
        if label == "Software Engineer" and (
            "エンジニア" in title or re.search(r"\bengineer\b", folded)
        ):
            if not any(block.lower() in folded for block in _SOFTWARE_BLOCK):
                return True
    return False


def experience_fits(title: str, level: Optional[str]) -> bool:
    """Drop titles that clearly contradict the chosen experience."""
    if not level:
        return True
    folded = (title or "").lower()
    junior = any(word.lower() in folded for word in _JUNIOR)
    senior = any(word.lower() in folded for word in _SENIOR)
    if level == "entry":
        return not senior
    if level in {"senior", "director"}:
        return not junior
    if level == "associate":
        return "director" not in folded and "部長" not in folded
    return True


def arrangement_fits(location: Optional[str], remote_option: Optional[bool], arrangement: str) -> bool:
    """Keep listings that agree with Remote, On-site, or Hybrid."""
    choice = arrangement or "Any"
    if choice not in _WORK_ARRANGEMENTS or choice == "Any":
        return True
    text = location or ""
    remote = bool(remote_option) or any(
        word in text.lower() for word in ("remote", "ハイブリッド", "hybrid")
    ) or "リモート" in text or "在宅" in text
    hybrid = "hybrid" in text.lower() or "ハイブリッド" in text
    if choice == "Remote":
        return remote
    if choice == "On-site":
        return not remote
    return remote or hybrid
