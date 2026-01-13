"""
設定管理モジュール
APIキーやパス設定を管理
"""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """アプリケーション設定"""

    # Google Cloud TTS設定
    google_cloud_credentials: str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Felo API設定
    felo_api_endpoint: str = os.environ.get("FELO_API_ENDPOINT", "")
    felo_api_key: str = os.environ.get("FELO_API_KEY", "")

    # TTS設定
    tts_language: str = "vi-VN"  # ベトナム語
    tts_voice_name: str = "vi-VN-Standard-A"
    tts_speaking_rate: float = 1.0

    # 出力設定
    output_dir: Path = Path("./output")
    audio_dir: Path = Path("./output/audio")
    report_dir: Path = Path("./output/reports")

    # 評価設定
    default_source_lang: str = "vi"  # ベトナム語
    default_target_lang: str = "ja"  # 日本語

    def __post_init__(self):
        """ディレクトリ作成"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)


# グローバル設定インスタンス
config = Config()
