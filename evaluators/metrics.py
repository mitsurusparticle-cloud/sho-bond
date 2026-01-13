"""
精度評価メトリクス計算モジュール

WER (Word Error Rate): 単語誤り率
CER (Character Error Rate): 文字誤り率
BLEU: 機械翻訳評価スコア
"""
from typing import List, Tuple


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    WER (Word Error Rate) を計算

    Args:
        reference: 正解テキスト
        hypothesis: 推定テキスト

    Returns:
        WER (0.0 ~ 1.0+、低いほど良い)
    """
    try:
        from jiwer import wer
        return wer(reference, hypothesis)
    except ImportError:
        # jiwerがない場合は簡易実装
        return _simple_wer(reference, hypothesis)


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    CER (Character Error Rate) を計算

    Args:
        reference: 正解テキスト
        hypothesis: 推定テキスト

    Returns:
        CER (0.0 ~ 1.0+、低いほど良い)
    """
    try:
        from jiwer import cer
        return cer(reference, hypothesis)
    except ImportError:
        # jiwerがない場合は簡易実装
        return _simple_cer(reference, hypothesis)


def calculate_bleu(reference: str, hypothesis: str) -> float:
    """
    BLEUスコアを計算

    Args:
        reference: 正解テキスト
        hypothesis: 推定テキスト

    Returns:
        BLEUスコア (0.0 ~ 100.0、高いほど良い)
    """
    try:
        from sacrebleu.metrics import BLEU
        bleu = BLEU()
        result = bleu.sentence_score(hypothesis, [reference])
        return result.score
    except ImportError:
        # sacrebleuがない場合は簡易実装
        return _simple_bleu(reference, hypothesis)


def calculate_accuracy(reference: str, hypothesis: str) -> float:
    """
    文字レベルの一致率（精度）を計算

    Args:
        reference: 正解テキスト
        hypothesis: 推定テキスト

    Returns:
        精度 (0.0 ~ 100.0、高いほど良い)
    """
    if not reference:
        return 100.0 if not hypothesis else 0.0

    cer_value = calculate_cer(reference, hypothesis)
    accuracy = max(0.0, (1.0 - cer_value) * 100)
    return round(accuracy, 2)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """レーベンシュタイン距離を計算"""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _simple_wer(reference: str, hypothesis: str) -> float:
    """簡易WER計算（jiwerなしの場合）"""
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    distance = _levenshtein_distance(
        " ".join(ref_words),
        " ".join(hyp_words)
    )
    # 単語単位で正規化
    return distance / len(ref_words)


def _simple_cer(reference: str, hypothesis: str) -> float:
    """簡易CER計算（jiwerなしの場合）"""
    if not reference:
        return 0.0 if not hypothesis else 1.0

    distance = _levenshtein_distance(reference, hypothesis)
    return distance / len(reference)


def _simple_bleu(reference: str, hypothesis: str) -> float:
    """簡易BLEU計算（sacrebleuなしの場合）"""
    # n-gramベースの簡易スコア
    def get_ngrams(text: str, n: int) -> dict:
        words = text.split()
        ngrams = {}
        for i in range(len(words) - n + 1):
            gram = tuple(words[i:i + n])
            ngrams[gram] = ngrams.get(gram, 0) + 1
        return ngrams

    if not hypothesis.split():
        return 0.0

    # 1-gramから4-gramまでの精度を計算
    scores = []
    for n in range(1, 5):
        ref_ngrams = get_ngrams(reference, n)
        hyp_ngrams = get_ngrams(hypothesis, n)

        if not hyp_ngrams:
            scores.append(0.0)
            continue

        match_count = 0
        for gram, count in hyp_ngrams.items():
            if gram in ref_ngrams:
                match_count += min(count, ref_ngrams[gram])

        total_count = sum(hyp_ngrams.values())
        scores.append(match_count / total_count if total_count > 0 else 0.0)

    # 幾何平均
    if all(s > 0 for s in scores):
        import math
        bleu = math.exp(sum(math.log(s) for s in scores) / len(scores))
    else:
        bleu = 0.0

    return bleu * 100


def get_error_details(reference: str, hypothesis: str) -> List[dict]:
    """
    誤り箇所の詳細を取得

    Args:
        reference: 正解テキスト
        hypothesis: 推定テキスト

    Returns:
        誤り詳細のリスト
    """
    errors = []
    ref_chars = list(reference)
    hyp_chars = list(hypothesis)

    # 動的計画法で編集操作を追跡
    m, n = len(ref_chars), len(hyp_chars)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    ops = [[None] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
        if i > 0:
            ops[i][0] = ('delete', ref_chars[i - 1], '')
    for j in range(n + 1):
        dp[0][j] = j
        if j > 0:
            ops[0][j] = ('insert', '', hyp_chars[j - 1])

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
                ops[i][j] = ('match', ref_chars[i - 1], hyp_chars[j - 1])
            else:
                costs = [
                    (dp[i - 1][j] + 1, ('delete', ref_chars[i - 1], '')),
                    (dp[i][j - 1] + 1, ('insert', '', hyp_chars[j - 1])),
                    (dp[i - 1][j - 1] + 1, ('substitute', ref_chars[i - 1], hyp_chars[j - 1]))
                ]
                dp[i][j], ops[i][j] = min(costs, key=lambda x: x[0])

    # バックトラックで誤り箇所を特定
    i, j = m, n
    position = max(m, n)
    while i > 0 or j > 0:
        op = ops[i][j]
        if op and op[0] != 'match':
            errors.append({
                'type': op[0],
                'position': position,
                'reference': op[1],
                'hypothesis': op[2],
                'error_type': _classify_error(op[0], op[1], op[2])
            })

        if op and op[0] in ('match', 'substitute'):
            i -= 1
            j -= 1
        elif op and op[0] == 'delete':
            i -= 1
        elif op and op[0] == 'insert':
            j -= 1
        else:
            break
        position -= 1

    errors.reverse()
    return errors


def _classify_error(op_type: str, ref_char: str, hyp_char: str) -> str:
    """誤りの種類を分類"""
    if op_type == 'delete':
        return '脱落'
    elif op_type == 'insert':
        return '挿入'
    elif op_type == 'substitute':
        # 同音異字の可能性をチェック（簡易版）
        return '置換（同音異字の可能性）'
    return '不明'
