"""
Felo Subtitles API 連携モジュール

注意: Felo APIの実際の仕様に合わせて調整が必要です。
現在はモック実装 + 一般的なREST API形式を想定しています。
"""
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import requests


@dataclass
class TranslationResult:
    """翻訳結果"""
    source_text: str       # 認識されたソース言語テキスト
    translated_text: str   # 翻訳後のテキスト
    source_lang: str       # ソース言語
    target_lang: str       # ターゲット言語
    confidence: float      # 信頼度 (0.0 ~ 1.0)
    processing_time: float # 処理時間 (秒)


class FeloTranslator:
    """Felo Subtitles API クライアント"""

    def __init__(
        self,
        api_endpoint: str = "",
        api_key: str = "",
        source_lang: str = "vi",
        target_lang: str = "ja",
        timeout: int = 60
    ):
        """
        初期化

        Args:
            api_endpoint: Felo APIのエンドポイント
            api_key: APIキー
            source_lang: ソース言語コード
            target_lang: ターゲット言語コード
            timeout: タイムアウト秒数
        """
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.timeout = timeout
        self._mock_mode = not api_endpoint  # APIが設定されていない場合はモックモード

    def translate_audio(
        self,
        audio_path: str | Path,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> TranslationResult:
        """
        音声ファイルを翻訳

        Args:
            audio_path: 音声ファイルのパス
            source_lang: ソース言語（省略時はインスタンスのデフォルト）
            target_lang: ターゲット言語（省略時はインスタンスのデフォルト）

        Returns:
            TranslationResult
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")

        source_lang = source_lang or self.source_lang
        target_lang = target_lang or self.target_lang

        if self._mock_mode:
            return self._mock_translate(audio_path, source_lang, target_lang)

        return self._api_translate(audio_path, source_lang, target_lang)

    def _mock_translate(
        self,
        audio_path: Path,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """
        モック翻訳（API未設定時のテスト用）

        実際のAPIが利用可能になるまでのプレースホルダー
        """
        # モックの遅延をシミュレート
        time.sleep(0.5)

        return TranslationResult(
            source_text=f"[モック] {audio_path.stem} のベトナム語認識結果",
            translated_text=f"[モック] {audio_path.stem} の日本語翻訳結果",
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=0.85,
            processing_time=0.5
        )

    def _api_translate(
        self,
        audio_path: Path,
        source_lang: str,
        target_lang: str
    ) -> TranslationResult:
        """
        実際のFelo APIを呼び出して翻訳

        注意: 実際のAPIエンドポイントとリクエスト形式に合わせて調整が必要
        """
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        # 音声ファイルをmultipart/form-dataで送信
        with open(audio_path, "rb") as f:
            files = {
                "audio": (audio_path.name, f, "audio/mpeg")
            }
            data = {
                "source_lang": source_lang,
                "target_lang": target_lang
            }

            try:
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
            except requests.RequestException as e:
                raise RuntimeError(f"Felo API呼び出しエラー: {e}")

        processing_time = time.time() - start_time

        # レスポンスのパース（実際のAPI仕様に合わせて調整）
        result = response.json()

        return TranslationResult(
            source_text=result.get("source_text", ""),
            translated_text=result.get("translated_text", ""),
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=result.get("confidence", 0.0),
            processing_time=processing_time
        )

    def translate_audio_batch(
        self,
        audio_paths: list[Path],
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> list[TranslationResult]:
        """
        複数の音声ファイルを一括翻訳

        Args:
            audio_paths: 音声ファイルのパスのリスト
            source_lang: ソース言語
            target_lang: ターゲット言語

        Returns:
            TranslationResultのリスト
        """
        results = []
        for audio_path in audio_paths:
            result = self.translate_audio(audio_path, source_lang, target_lang)
            results.append(result)
        return results

    @property
    def is_mock_mode(self) -> bool:
        """モックモードかどうか"""
        return self._mock_mode

    def set_credentials(self, api_endpoint: str, api_key: str):
        """
        API認証情報を設定

        Args:
            api_endpoint: APIエンドポイント
            api_key: APIキー
        """
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self._mock_mode = not api_endpoint
