"""
テキスト処理ユーティリティ
"""
import re
from typing import List


def normalize_text(text: str) -> str:
    """
    テキストを正規化

    - 全角スペースを半角に
    - 連続スペースを単一に
    - 前後の空白を削除
    - 改行を統一

    Args:
        text: 入力テキスト

    Returns:
        正規化されたテキスト
    """
    if not text:
        return ""

    # 全角スペースを半角に
    text = text.replace('\u3000', ' ')

    # 改行を統一
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 連続スペースを単一に
    text = re.sub(r'[ \t]+', ' ', text)

    # 連続改行を単一に
    text = re.sub(r'\n+', '\n', text)

    # 前後の空白を削除
    text = text.strip()

    return text


def split_sentences(text: str, lang: str = "ja") -> List[str]:
    """
    テキストを文単位に分割

    Args:
        text: 入力テキスト
        lang: 言語コード (ja: 日本語, vi: ベトナム語)

    Returns:
        文のリスト
    """
    if not text:
        return []

    if lang == "ja":
        # 日本語の文末パターン
        pattern = r'(?<=[。！？\n])'
    elif lang == "vi":
        # ベトナム語の文末パターン
        pattern = r'(?<=[.!?\n])'
    else:
        # デフォルト
        pattern = r'(?<=[.!?\n])'

    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def remove_special_chars(text: str) -> str:
    """
    特殊文字を削除

    Args:
        text: 入力テキスト

    Returns:
        特殊文字を削除したテキスト
    """
    # 制御文字を削除
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return text


def is_japanese(text: str) -> bool:
    """
    テキストが日本語を含むかチェック

    Args:
        text: 入力テキスト

    Returns:
        日本語を含む場合True
    """
    # ひらがな、カタカナ、漢字のパターン
    japanese_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]')
    return bool(japanese_pattern.search(text))


def is_vietnamese(text: str) -> bool:
    """
    テキストがベトナム語を含むかチェック

    Args:
        text: 入力テキスト

    Returns:
        ベトナム語を含む場合True
    """
    # ベトナム語特有の文字パターン
    vietnamese_chars = (
        'àáảãạăằắẳẵặâầấẩẫậ'
        'èéẻẽẹêềếểễệ'
        'ìíỉĩị'
        'òóỏõọôồốổỗộơờớởỡợ'
        'ùúủũụưừứửữự'
        'ỳýỷỹỵ'
        'đ'
        'ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ'
        'ÈÉẺẼẸÊỀẾỂỄỆ'
        'ÌÍỈĨỊ'
        'ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ'
        'ÙÚỦŨỤƯỪỨỬỮỰ'
        'ỲÝỶỸỴ'
        'Đ'
    )
    pattern = re.compile(f'[{vietnamese_chars}]')
    return bool(pattern.search(text))


def extract_words(text: str, lang: str = "ja") -> List[str]:
    """
    テキストから単語を抽出

    Args:
        text: 入力テキスト
        lang: 言語コード

    Returns:
        単語のリスト
    """
    if lang == "ja":
        # 日本語は形態素解析が必要だが、簡易的にスペースと句読点で分割
        words = re.split(r'[\s、。！？「」（）\[\]【】]', text)
    else:
        # その他の言語はスペースで分割
        words = text.split()

    return [w.strip() for w in words if w.strip()]
