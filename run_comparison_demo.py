#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparison Demo - Simulates before/after dictionary addition test
"""
import json
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from evaluators import TextComparator
from reporters import ReportGenerator

# Test data - Japanese reference texts
TEST_JAPANESE = [
    "ヘルメットを着用してください",
    "安全帯を必ず装着すること",
    "足場の点検を行う",
    "作業前に危険箇所を確認",
    "鉄筋コンクリート",
    "基礎工事",
    "配管工事",
    "電気設備",
    "今日の作業内容を確認します",
    "体調不良の方は申し出てください",
    "熱中症に注意してください",
    "水分補給を忘れずに",
    "事故が発生したら直ちに報告",
    "避難経路を確認してください",
    "消火器の場所を覚えておく",
    "応急処置キットの使い方",
]

# Simulated translation results BEFORE dictionary addition (lower accuracy)
BEFORE_TRANSLATIONS = [
    "ヘルメットを着用して下さい",      # OK but different kanji
    "安全体を必ず装着すること",         # Error: 帯->体
    "足場の点検を行なう",               # OK but different okurigana
    "作業前に危険個所を確認",           # Error: 箇所->個所
    "鉄近コンクリート",                 # Error: 筋->近
    "基礎工事",                         # Correct
    "排管工事",                         # Error: 配->排
    "電気設備",                         # Correct
    "今日の作業内容を確認します",       # Correct
    "体調普良の方は申し出てください",   # Error: 不->普
    "熱中賞に注意してください",         # Error: 症->賞
    "水分補給を忘れずに",               # Correct
    "事故が発生したら直に報告",         # Error: 直ちに->直に
    "避難経路を確認して下さい",         # OK but different
    "消化器の場所を覚えておく",         # Error: 火->化
    "応急処理キットの使い方",           # Error: 置->理
]

# Simulated translation results AFTER dictionary addition (higher accuracy)
AFTER_TRANSLATIONS = [
    "ヘルメットを着用してください",     # Correct
    "安全帯を必ず装着すること",         # Correct (fixed)
    "足場の点検を行う",                 # Correct
    "作業前に危険箇所を確認",           # Correct (fixed)
    "鉄筋コンクリート",                 # Correct (fixed)
    "基礎工事",                         # Correct
    "配管工事",                         # Correct (fixed)
    "電気設備",                         # Correct
    "今日の作業内容を確認します",       # Correct
    "体調不良の方は申し出てください",   # Correct (fixed)
    "熱中症に注意してください",         # Correct (fixed)
    "水分補給を忘れずに",               # Correct
    "事故が発生したら直ちに報告",       # Correct (fixed)
    "避難経路を確認してください",       # Correct
    "消火器の場所を覚えておく",         # Correct (fixed)
    "応急処置キットの使い方",           # Correct (fixed)
]


def run_evaluation(references, translations, label):
    """Run evaluation and generate reports"""
    print(f"\n{'='*60}")
    print(f"Evaluating: {label}")
    print(f"{'='*60}")

    comparator = TextComparator()
    results = []

    for i, (ref, hyp) in enumerate(zip(references, translations)):
        result = comparator.compare(
            reference=ref,
            hypothesis=hyp,
            source_info={"file": "test_data", "item": i + 1}
        )
        results.append(result)

        status = "OK" if result.accuracy == 100.0 else f"ERR ({result.accuracy:.0f}%)"
        print(f"  [{i+1:2d}] {status}: {ref[:20]}...")

    summary = comparator.summarize(results)

    print(f"\n  Summary:")
    print(f"    Accuracy: {summary['avg_accuracy']:.1f}%")
    print(f"    WER: {summary['avg_wer']:.2%}")
    print(f"    CER: {summary['avg_cer']:.2%}")
    print(f"    Errors: {summary['total_errors']}")

    return results, summary


def main():
    output_base = Path(__file__).parent / "output"

    # Create output directories
    before_dir = output_base / "before"
    after_dir = output_base / "after"
    before_dir.mkdir(parents=True, exist_ok=True)
    after_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("Dictionary Addition Effect - Comparison Demo")
    print("="*60)

    # Run BEFORE evaluation
    before_results, before_summary = run_evaluation(
        TEST_JAPANESE, BEFORE_TRANSLATIONS, "BEFORE Dictionary Addition"
    )

    # Save before summary
    with open(before_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(before_summary, f, ensure_ascii=False, indent=2)

    # Generate before reports
    reporter_before = ReportGenerator(output_dir=before_dir)
    reporter_before.generate_markdown_report(
        before_results, before_summary, "before", ["simulation_data"]
    )
    reporter_before.generate_csv_report(before_results, "before")

    # Run AFTER evaluation
    after_results, after_summary = run_evaluation(
        TEST_JAPANESE, AFTER_TRANSLATIONS, "AFTER Dictionary Addition"
    )

    # Save after summary
    with open(after_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(after_summary, f, ensure_ascii=False, indent=2)

    # Generate after reports
    reporter_after = ReportGenerator(output_dir=after_dir)
    reporter_after.generate_markdown_report(
        after_results, after_summary, "after", ["simulation_data"]
    )
    reporter_after.generate_csv_report(after_results, "after")

    # Generate COMPARISON report
    print(f"\n{'='*60}")
    print("Generating Comparison Report...")
    print(f"{'='*60}")

    reporter_compare = ReportGenerator(output_dir=output_base)
    comparison_path = reporter_compare.generate_comparison_report(
        before_summary, after_summary,
        "Dictionary Addition - Before",
        "Dictionary Addition - After"
    )

    # Print comparison summary
    print(f"\n  Accuracy Improvement:")
    print(f"    Before: {before_summary['avg_accuracy']:.1f}%")
    print(f"    After:  {after_summary['avg_accuracy']:.1f}%")
    improvement = after_summary['avg_accuracy'] - before_summary['avg_accuracy']
    print(f"    Change: +{improvement:.1f}%")

    print(f"\n  Error Reduction:")
    print(f"    Before: {before_summary['total_errors']} errors")
    print(f"    After:  {after_summary['total_errors']} errors")
    reduction = before_summary['total_errors'] - after_summary['total_errors']
    print(f"    Reduced: {reduction} errors")

    print(f"\n{'='*60}")
    print("Reports Generated:")
    print(f"{'='*60}")
    print(f"  Before: {before_dir}")
    print(f"  After:  {after_dir}")
    print(f"  Comparison: {comparison_path}")
    print(f"\nDemo completed successfully!")


if __name__ == "__main__":
    main()
