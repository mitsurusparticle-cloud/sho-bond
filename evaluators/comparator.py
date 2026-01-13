"""
テキスト比較モジュール

正解テキストと翻訳結果を比較し、詳細な分析結果を提供
"""
from dataclasses import dataclass, field
from typing import List, Optional

from .metrics import (
    calculate_wer,
    calculate_cer,
    calculate_bleu,
    calculate_accuracy,
    get_error_details
)


@dataclass
class ErrorDetail:
    """誤り詳細"""
    position: int
    reference_text: str
    hypothesis_text: str
    error_type: str  # 脱落, 挿入, 置換（同音異字）等


@dataclass
class ComparisonResult:
    """比較結果"""
    reference: str
    hypothesis: str
    accuracy: float          # 精度 (%)
    wer: float               # Word Error Rate
    cer: float               # Character Error Rate
    bleu: float              # BLEUスコア
    errors: List[ErrorDetail] = field(default_factory=list)
    source_info: Optional[dict] = None  # ファイル名、スライド番号等


class TextComparator:
    """テキスト比較器"""

    def __init__(self, normalize: bool = True):
        """
        初期化

        Args:
            normalize: テキストを正規化するか
        """
        self.normalize = normalize

    def _normalize_text(self, text: str) -> str:
        """
        テキストを正規化

        - 全角スペース→半角スペース
        - 連続スペースを単一に
        - 前後の空白を削除
        """
        if not self.normalize:
            return text

        # 全角スペースを半角に
        text = text.replace('\u3000', ' ')
        # 連続スペースを単一に
        import re
        text = re.sub(r'\s+', ' ', text)
        # 前後の空白を削除
        text = text.strip()

        return text

    def compare(
        self,
        reference: str,
        hypothesis: str,
        source_info: Optional[dict] = None
    ) -> ComparisonResult:
        """
        2つのテキストを比較

        Args:
            reference: 正解テキスト
            hypothesis: 推定テキスト（翻訳結果）
            source_info: ソース情報（オプション）

        Returns:
            ComparisonResult
        """
        ref_normalized = self._normalize_text(reference)
        hyp_normalized = self._normalize_text(hypothesis)

        # メトリクス計算
        accuracy = calculate_accuracy(ref_normalized, hyp_normalized)
        wer = calculate_wer(ref_normalized, hyp_normalized)
        cer = calculate_cer(ref_normalized, hyp_normalized)
        bleu = calculate_bleu(ref_normalized, hyp_normalized)

        # 誤り詳細の取得
        error_details_raw = get_error_details(ref_normalized, hyp_normalized)
        errors = [
            ErrorDetail(
                position=e['position'],
                reference_text=e['reference'],
                hypothesis_text=e['hypothesis'],
                error_type=e['error_type']
            )
            for e in error_details_raw
        ]

        return ComparisonResult(
            reference=reference,
            hypothesis=hypothesis,
            accuracy=accuracy,
            wer=wer,
            cer=cer,
            bleu=bleu,
            errors=errors,
            source_info=source_info
        )

    def compare_batch(
        self,
        pairs: List[tuple],
        source_infos: Optional[List[dict]] = None
    ) -> List[ComparisonResult]:
        """
        複数のテキストペアを一括比較

        Args:
            pairs: (reference, hypothesis) のタプルのリスト
            source_infos: ソース情報のリスト（オプション）

        Returns:
            ComparisonResultのリスト
        """
        if source_infos is None:
            source_infos = [None] * len(pairs)

        results = []
        for (ref, hyp), info in zip(pairs, source_infos):
            result = self.compare(ref, hyp, info)
            results.append(result)

        return results

    def summarize(self, results: List[ComparisonResult]) -> dict:
        """
        複数の比較結果を集計

        Args:
            results: ComparisonResultのリスト

        Returns:
            集計結果の辞書
        """
        if not results:
            return {
                "total_items": 0,
                "avg_accuracy": 0.0,
                "avg_wer": 0.0,
                "avg_cer": 0.0,
                "avg_bleu": 0.0,
                "total_errors": 0,
                "error_breakdown": {}
            }

        # 平均値計算
        avg_accuracy = sum(r.accuracy for r in results) / len(results)
        avg_wer = sum(r.wer for r in results) / len(results)
        avg_cer = sum(r.cer for r in results) / len(results)
        avg_bleu = sum(r.bleu for r in results) / len(results)

        # 誤り種別の集計
        error_breakdown = {}
        total_errors = 0
        for result in results:
            for error in result.errors:
                error_type = error.error_type
                error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1
                total_errors += 1

        return {
            "total_items": len(results),
            "avg_accuracy": round(avg_accuracy, 2),
            "avg_wer": round(avg_wer, 4),
            "avg_cer": round(avg_cer, 4),
            "avg_bleu": round(avg_bleu, 2),
            "total_errors": total_errors,
            "error_breakdown": error_breakdown
        }
