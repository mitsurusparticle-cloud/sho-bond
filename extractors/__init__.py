"""テキスト抽出モジュール"""
from .pptx_extractor import extract_from_pptx
from .pdf_extractor import extract_from_pdf

__all__ = ["extract_from_pptx", "extract_from_pdf"]
