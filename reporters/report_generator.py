"""
レポート生成モジュール

翻訳精度検証結果を日本語レポートとして出力
"""
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from evaluators.comparator import ComparisonResult


class ReportGenerator:
    """レポート生成器"""

    def __init__(self, output_dir: str | Path = "./output/reports"):
        """
        初期化

        Args:
            output_dir: 出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown_report(
        self,
        results: List[ComparisonResult],
        summary: dict,
        label: str = "",
        source_files: Optional[List[str]] = None
    ) -> Path:
        """
        Markdown形式のレポートを生成

        Args:
            results: 比較結果のリスト
            summary: 集計結果
            label: レポートのラベル（辞書追加前/後等）
            source_files: 対象ファイル名のリスト

        Returns:
            生成されたレポートファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{label}_{timestamp}.md" if label else f"report_{timestamp}.md"
        output_path = self.output_dir / filename

        lines = []

        # ヘッダー
        lines.append("=" * 60)
        lines.append("翻訳精度検証レポート")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"**実行日時:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if label:
            lines.append(f"**ラベル:** {label}")
        if source_files:
            lines.append(f"**対象ファイル:** {', '.join(source_files)}")
        lines.append("")

        # 総合評価
        lines.append("## 総合評価")
        lines.append("")
        lines.append(f"| 指標 | 値 |")
        lines.append("|------|-----|")
        lines.append(f"| 翻訳精度 | **{summary['avg_accuracy']:.1f}%** |")
        lines.append(f"| WER (単語誤り率) | {summary['avg_wer']:.2%} |")
        lines.append(f"| CER (文字誤り率) | {summary['avg_cer']:.2%} |")
        lines.append(f"| BLEUスコア | {summary['avg_bleu']:.1f} |")
        lines.append(f"| 検証項目数 | {summary['total_items']} |")
        lines.append(f"| 総エラー数 | {summary['total_errors']} |")
        lines.append("")

        # エラー種別内訳
        if summary['error_breakdown']:
            lines.append("## エラー種別内訳")
            lines.append("")
            lines.append("| エラー種別 | 件数 |")
            lines.append("|-----------|------|")
            for error_type, count in summary['error_breakdown'].items():
                lines.append(f"| {error_type} | {count} |")
            lines.append("")

        # 誤変換リスト
        lines.append("## 誤変換リスト")
        lines.append("")
        lines.append("| No. | 正解（日本語） | 翻訳結果 | エラー種別 | 精度 |")
        lines.append("|-----|--------------|---------|-----------|------|")

        error_no = 1
        for result in results:
            if result.errors:
                # エラーがある場合は詳細を表示
                ref_short = result.reference[:30] + "..." if len(result.reference) > 30 else result.reference
                hyp_short = result.hypothesis[:30] + "..." if len(result.hypothesis) > 30 else result.hypothesis
                error_types = ", ".join(set(e.error_type for e in result.errors[:3]))
                lines.append(f"| {error_no} | {ref_short} | {hyp_short} | {error_types} | {result.accuracy:.1f}% |")
                error_no += 1

        if error_no == 1:
            lines.append("| - | エラーなし | - | - | - |")

        lines.append("")

        # 詳細分析
        lines.append("## 詳細分析")
        lines.append("")
        for i, result in enumerate(results, start=1):
            lines.append(f"### 項目 {i}")
            if result.source_info:
                info = result.source_info
                if 'file' in info:
                    lines.append(f"**ファイル:** {info['file']}")
                if 'slide' in info:
                    lines.append(f"**スライド:** {info['slide']}")
                if 'page' in info:
                    lines.append(f"**ページ:** {info['page']}")
            lines.append("")
            lines.append(f"**正解:** {result.reference}")
            lines.append("")
            lines.append(f"**翻訳結果:** {result.hypothesis}")
            lines.append("")
            lines.append(f"**精度:** {result.accuracy:.1f}% | WER: {result.wer:.2%} | CER: {result.cer:.2%}")
            lines.append("")
            if result.errors:
                lines.append("**誤り詳細:**")
                for error in result.errors[:10]:  # 最大10件表示
                    lines.append(f"- [{error.error_type}] 「{error.reference_text}」→「{error.hypothesis_text}」")
            lines.append("")
            lines.append("---")
            lines.append("")

        # フッター
        lines.append("")
        lines.append("---")
        lines.append(f"*レポート生成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        # ファイル出力
        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def generate_csv_report(
        self,
        results: List[ComparisonResult],
        label: str = ""
    ) -> Path:
        """
        CSV形式のレポートを生成

        Args:
            results: 比較結果のリスト
            label: レポートのラベル

        Returns:
            生成されたCSVファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{label}_{timestamp}.csv" if label else f"report_{timestamp}.csv"
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # ヘッダー
            writer.writerow([
                "No.",
                "正解（日本語）",
                "翻訳結果",
                "精度(%)",
                "WER",
                "CER",
                "BLEU",
                "エラー数",
                "エラー種別",
                "ファイル",
                "位置"
            ])

            # データ行
            for i, result in enumerate(results, start=1):
                error_types = ", ".join(set(e.error_type for e in result.errors)) if result.errors else ""
                file_name = result.source_info.get('file', '') if result.source_info else ''
                position = ""
                if result.source_info:
                    if 'slide' in result.source_info:
                        position = f"スライド{result.source_info['slide']}"
                    elif 'page' in result.source_info:
                        position = f"ページ{result.source_info['page']}"

                writer.writerow([
                    i,
                    result.reference,
                    result.hypothesis,
                    f"{result.accuracy:.1f}",
                    f"{result.wer:.4f}",
                    f"{result.cer:.4f}",
                    f"{result.bleu:.1f}",
                    len(result.errors),
                    error_types,
                    file_name,
                    position
                ])

        return output_path

    def generate_json_report(
        self,
        results: List[ComparisonResult],
        summary: dict,
        label: str = ""
    ) -> Path:
        """
        JSON形式のレポートを生成

        Args:
            results: 比較結果のリスト
            summary: 集計結果
            label: レポートのラベル

        Returns:
            生成されたJSONファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{label}_{timestamp}.json" if label else f"report_{timestamp}.json"
        output_path = self.output_dir / filename

        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "label": label,
                "tool_version": "1.0.0"
            },
            "summary": summary,
            "results": [
                {
                    "reference": r.reference,
                    "hypothesis": r.hypothesis,
                    "accuracy": r.accuracy,
                    "wer": r.wer,
                    "cer": r.cer,
                    "bleu": r.bleu,
                    "errors": [
                        {
                            "position": e.position,
                            "reference_text": e.reference_text,
                            "hypothesis_text": e.hypothesis_text,
                            "error_type": e.error_type
                        }
                        for e in r.errors
                    ],
                    "source_info": r.source_info
                }
                for r in results
            ]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return output_path

    def generate_comparison_report(
        self,
        before_summary: dict,
        after_summary: dict,
        before_label: str = "辞書追加前",
        after_label: str = "辞書追加後"
    ) -> Path:
        """
        辞書追加前後の比較レポートを生成

        Args:
            before_summary: 追加前の集計結果
            after_summary: 追加後の集計結果
            before_label: 追加前のラベル
            after_label: 追加後のラベル

        Returns:
            生成されたレポートファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_report_{timestamp}.md"
        output_path = self.output_dir / filename

        lines = []

        lines.append("=" * 60)
        lines.append("辞書機能 精度比較レポート")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"**実行日時:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 比較表
        lines.append("## 精度比較")
        lines.append("")
        lines.append(f"| 指標 | {before_label} | {after_label} | 改善 |")
        lines.append("|------|----------|----------|------|")

        # 精度
        acc_before = before_summary['avg_accuracy']
        acc_after = after_summary['avg_accuracy']
        acc_diff = acc_after - acc_before
        acc_sign = "+" if acc_diff >= 0 else ""
        lines.append(f"| 翻訳精度 | {acc_before:.1f}% | {acc_after:.1f}% | {acc_sign}{acc_diff:.1f}% |")

        # WER
        wer_before = before_summary['avg_wer']
        wer_after = after_summary['avg_wer']
        wer_diff = wer_before - wer_after  # WERは低い方が良いので逆
        wer_sign = "+" if wer_diff >= 0 else ""
        lines.append(f"| WER改善 | {wer_before:.2%} | {wer_after:.2%} | {wer_sign}{wer_diff:.2%} |")

        # CER
        cer_before = before_summary['avg_cer']
        cer_after = after_summary['avg_cer']
        cer_diff = cer_before - cer_after
        cer_sign = "+" if cer_diff >= 0 else ""
        lines.append(f"| CER改善 | {cer_before:.2%} | {cer_after:.2%} | {cer_sign}{cer_diff:.2%} |")

        # BLEU
        bleu_before = before_summary['avg_bleu']
        bleu_after = after_summary['avg_bleu']
        bleu_diff = bleu_after - bleu_before
        bleu_sign = "+" if bleu_diff >= 0 else ""
        lines.append(f"| BLEU | {bleu_before:.1f} | {bleu_after:.1f} | {bleu_sign}{bleu_diff:.1f} |")

        # エラー数
        err_before = before_summary['total_errors']
        err_after = after_summary['total_errors']
        err_diff = err_before - err_after
        err_sign = "+" if err_diff >= 0 else ""
        lines.append(f"| エラー削減 | {err_before} | {err_after} | {err_sign}{err_diff} |")

        lines.append("")

        # 結論
        lines.append("## 結論")
        lines.append("")
        if acc_diff > 0:
            lines.append(f"辞書機能の追加により、翻訳精度が **{acc_diff:.1f}%** 向上しました。")
        elif acc_diff < 0:
            lines.append(f"辞書機能の追加後、翻訳精度が **{abs(acc_diff):.1f}%** 低下しました。設定の見直しが必要です。")
        else:
            lines.append("辞書機能の追加による精度変化は見られませんでした。")

        lines.append("")
        lines.append("---")
        lines.append(f"*レポート生成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path
