"""
PDFファイルからテキストを抽出するモジュール
"""
from pathlib import Path
from typing import List
from dataclasses import dataclass

import fitz  # PyMuPDF
from langdetect import detect, LangDetectException


@dataclass
class TextPair:
    """日本語・ベトナム語のテキストペア"""
    japanese: str
    vietnamese: str
    source_file: str
    page_number: int
    confidence: float = 1.0


def detect_language(text: str) -> str:
    """
    テキストの言語を検出

    Args:
        text: 検出対象のテキスト

    Returns:
        言語コード (ja, vi, en, etc.) または "unknown"
    """
    if not text or len(text.strip()) < 3:
        return "unknown"

    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def extract_text_from_page(page) -> List[str]:
    """
    PDFページからテキストブロックを抽出

    Args:
        page: PyMuPDFのPageオブジェクト

    Returns:
        テキストブロックのリスト
    """
    texts = []
    blocks = page.get_text("blocks")

    for block in blocks:
        # block[4]がテキスト内容
        if len(block) >= 5 and isinstance(block[4], str):
            text = block[4].strip()
            if text:
                texts.append(text)

    return texts


def extract_from_pdf(file_path: str | Path) -> List[TextPair]:
    """
    PDFファイルから日本語・ベトナム語のテキストペアを抽出

    Args:
        file_path: PDFファイルのパス

    Returns:
        TextPairのリスト
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    doc = fitz.open(str(file_path))
    pairs = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        texts = extract_text_from_page(page)

        japanese_texts = []
        vietnamese_texts = []

        for text in texts:
            lang = detect_language(text)
            if lang == "ja":
                japanese_texts.append(text)
            elif lang == "vi":
                vietnamese_texts.append(text)

        # テキストをペアリング
        for ja, vi in zip(japanese_texts, vietnamese_texts):
            pairs.append(TextPair(
                japanese=ja,
                vietnamese=vi,
                source_file=file_path.name,
                page_number=page_num + 1
            ))

    doc.close()
    return pairs


def extract_all_text_from_pdf(file_path: str | Path) -> dict:
    """
    PDFファイルから全テキストを言語別に抽出

    Args:
        file_path: PDFファイルのパス

    Returns:
        {"japanese": [...], "vietnamese": [...], "other": [...]}
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    doc = fitz.open(str(file_path))
    result = {"japanese": [], "vietnamese": [], "other": []}

    for page_num in range(len(doc)):
        page = doc[page_num]
        texts = extract_text_from_page(page)

        for text in texts:
            lang = detect_language(text)
            entry = {
                "text": text,
                "page": page_num + 1,
                "language": lang
            }
            if lang == "ja":
                result["japanese"].append(entry)
            elif lang == "vi":
                result["vietnamese"].append(entry)
            else:
                result["other"].append(entry)

    doc.close()
    return result
