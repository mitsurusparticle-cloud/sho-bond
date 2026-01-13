#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音声翻訳精度検証テストツール

Felo subtitlesの翻訳精度を検証するための自動テストツール
音声辞書・翻訳辞書機能追加前後の精度比較検証が目的

使用方法:
    # 基本実行
    python main.py --input ./test_files/ --output ./reports/

    # 辞書追加前後の比較
    python main.py --input ./test_files/ --label "辞書追加前" --output ./reports/before/
    python main.py --input ./test_files/ --label "辞書追加後" --output ./reports/after/

    # 比較レポート生成
    python main.py --compare ./reports/before/ ./reports/after/
"""
import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from extractors import extract_from_pptx, extract_from_pdf
from tts import EdgeTTSClient
from translators import FeloTranslator
from evaluators import TextComparator
from reporters import ReportGenerator


def find_input_files(input_path: Path) -> List[Path]:
    """
    入力ディレクトリからPPTX/PDFファイルを検索

    Args:
        input_path: 入力ディレクトリまたはファイルのパス

    Returns:
        ファイルパスのリスト
    """
    if input_path.is_file():
        return [input_path]

    files = []
    for ext in ["*.pptx", "*.pdf", "*.PPTX", "*.PDF"]:
        files.extend(input_path.glob(ext))
    return sorted(files)


def extract_text_pairs(file_path: Path) -> List[dict]:
    """
    ファイルからテキストペアを抽出

    Args:
        file_path: ファイルパス

    Returns:
        テキストペア情報のリスト
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pptx":
        pairs = extract_from_pptx(file_path)
    elif suffix == ".pdf":
        pairs = extract_from_pdf(file_path)
    else:
        print(f"[警告] 未対応のファイル形式: {file_path}")
        return []

    return [
        {
            "japanese": p.japanese,
            "vietnamese": p.vietnamese,
            "source_info": {
                "file": p.source_file,
                "slide": getattr(p, "slide_number", None),
                "page": getattr(p, "page_number", None)
            }
        }
        for p in pairs
    ]


def run_test_pipeline(
    input_path: Path,
    output_path: Path,
    label: str = "",
    use_mock: bool = False
) -> dict:
    """
    テストパイプラインを実行

    Args:
        input_path: 入力ファイル/ディレクトリ
        output_path: 出力ディレクトリ
        label: テストラベル
        use_mock: モックモードを使用するか

    Returns:
        テスト結果のサマリー
    """
    print(f"\n{'='*60}")
    print(f"音声翻訳精度検証テスト開始")
    if label:
        print(f"ラベル: {label}")
    print(f"{'='*60}\n")

    # 出力ディレクトリ作成
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    audio_dir = output_path / "audio"
    audio_dir.mkdir(exist_ok=True)

    # 入力ファイル検索
    input_files = find_input_files(Path(input_path))
    if not input_files:
        print(f"[エラー] 入力ファイルが見つかりません: {input_path}")
        return {}

    print(f"[1/5] 入力ファイル: {len(input_files)} 件")
    for f in input_files:
        print(f"  - {f.name}")

    # テキスト抽出
    print(f"\n[2/5] テキスト抽出中...")
    all_pairs = []
    for file_path in input_files:
        pairs = extract_text_pairs(file_path)
        all_pairs.extend(pairs)
        print(f"  - {file_path.name}: {len(pairs)} ペア")

    if not all_pairs:
        print("[エラー] テキストペアが抽出できませんでした")
        return {}

    print(f"  合計: {len(all_pairs)} ペア")

    # TTS音声化
    print(f"\n[3/5] ベトナム語テキストを音声化中...")
    tts = EdgeTTSClient(voice="vi-VN-HoaiMyNeural")
    vietnamese_texts = [p["vietnamese"] for p in all_pairs]

    audio_paths = []
    for i, text in enumerate(vietnamese_texts):
        audio_path = audio_dir / f"audio_{i:04d}.mp3"
        try:
            tts.synthesize(text, audio_path)
            audio_paths.append(audio_path)
            print(f"  [{i+1}/{len(vietnamese_texts)}] 生成完了: {audio_path.name}")
        except Exception as e:
            print(f"  [{i+1}/{len(vietnamese_texts)}] エラー: {e}")
            audio_paths.append(None)

    # Felo API翻訳
    print(f"\n[4/5] Felo APIで翻訳中...")
    translator = FeloTranslator(
        api_endpoint=config.felo_api_endpoint,
        api_key=config.felo_api_key
    )

    if translator.is_mock_mode:
        print("  [注意] モックモードで実行中（API未設定）")

    translation_results = []
    for i, audio_path in enumerate(audio_paths):
        if audio_path is None:
            translation_results.append(None)
            continue

        try:
            result = translator.translate_audio(audio_path)
            translation_results.append(result.translated_text)
            print(f"  [{i+1}/{len(audio_paths)}] 翻訳完了")
        except Exception as e:
            print(f"  [{i+1}/{len(audio_paths)}] エラー: {e}")
            translation_results.append("")

    # 精度評価
    print(f"\n[5/5] 精度評価中...")
    comparator = TextComparator()
    comparison_results = []

    for i, (pair, translated) in enumerate(zip(all_pairs, translation_results)):
        if translated is None:
            continue

        result = comparator.compare(
            reference=pair["japanese"],
            hypothesis=translated,
            source_info=pair["source_info"]
        )
        comparison_results.append(result)

    # 集計
    summary = comparator.summarize(comparison_results)
    print(f"\n  平均精度: {summary['avg_accuracy']:.1f}%")
    print(f"  WER: {summary['avg_wer']:.2%}")
    print(f"  CER: {summary['avg_cer']:.2%}")
    print(f"  BLEU: {summary['avg_bleu']:.1f}")
    print(f"  エラー数: {summary['total_errors']}")

    # レポート生成
    print(f"\n[完了] レポート生成中...")
    reporter = ReportGenerator(output_dir=output_path)

    source_files = [f.name for f in input_files]
    md_path = reporter.generate_markdown_report(
        comparison_results, summary, label, source_files
    )
    csv_path = reporter.generate_csv_report(comparison_results, label)
    json_path = reporter.generate_json_report(comparison_results, summary, label)

    print(f"  - Markdown: {md_path}")
    print(f"  - CSV: {csv_path}")
    print(f"  - JSON: {json_path}")

    # サマリーを保存（比較用）
    summary_path = output_path / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"テスト完了")
    print(f"{'='*60}\n")

    return summary


def run_comparison(before_path: Path, after_path: Path, output_path: Path):
    """
    辞書追加前後の比較レポートを生成

    Args:
        before_path: 追加前のレポートディレクトリ
        after_path: 追加後のレポートディレクトリ
        output_path: 出力ディレクトリ
    """
    print(f"\n{'='*60}")
    print(f"辞書機能 精度比較")
    print(f"{'='*60}\n")

    # サマリー読み込み
    before_summary_path = Path(before_path) / "summary.json"
    after_summary_path = Path(after_path) / "summary.json"

    if not before_summary_path.exists():
        print(f"[エラー] 追加前のサマリーが見つかりません: {before_summary_path}")
        return

    if not after_summary_path.exists():
        print(f"[エラー] 追加後のサマリーが見つかりません: {after_summary_path}")
        return

    with open(before_summary_path, "r", encoding="utf-8") as f:
        before_summary = json.load(f)

    with open(after_summary_path, "r", encoding="utf-8") as f:
        after_summary = json.load(f)

    # 比較レポート生成
    reporter = ReportGenerator(output_dir=output_path)
    report_path = reporter.generate_comparison_report(
        before_summary, after_summary,
        "辞書追加前", "辞書追加後"
    )

    print(f"比較レポート生成完了: {report_path}")


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="音声翻訳精度検証テストツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本実行
  python main.py --input ./test_files/ --output ./reports/

  # 辞書追加前のテスト
  python main.py --input ./test_files/ --label "辞書追加前" --output ./reports/before/

  # 辞書追加後のテスト
  python main.py --input ./test_files/ --label "辞書追加後" --output ./reports/after/

  # 比較レポート生成
  python main.py --compare ./reports/before/ ./reports/after/
        """
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        help="入力ファイルまたはディレクトリのパス"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output",
        help="出力ディレクトリのパス (デフォルト: ./output)"
    )
    parser.add_argument(
        "--label", "-l",
        type=str,
        default="",
        help="テストのラベル (例: 辞書追加前, 辞書追加後)"
    )
    parser.add_argument(
        "--compare", "-c",
        nargs=2,
        metavar=("BEFORE", "AFTER"),
        help="比較レポート生成: 追加前ディレクトリ 追加後ディレクトリ"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="モックモードで実行（API呼び出しをスキップ）"
    )

    args = parser.parse_args()

    # 比較モード
    if args.compare:
        run_comparison(
            Path(args.compare[0]),
            Path(args.compare[1]),
            Path(args.output)
        )
        return

    # 通常モード
    if not args.input:
        parser.print_help()
        print("\n[エラー] --input オプションで入力ファイルを指定してください")
        sys.exit(1)

    run_test_pipeline(
        Path(args.input),
        Path(args.output),
        args.label,
        args.mock
    )


if __name__ == "__main__":
    main()
