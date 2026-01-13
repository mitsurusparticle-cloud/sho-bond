"""
Google Cloud Text-to-Speech 連携モジュール
"""
from pathlib import Path
from typing import Optional


class GoogleTTS:
    """Google Cloud Text-to-Speech クライアント"""

    def __init__(
        self,
        language_code: str = "vi-VN",
        voice_name: str = "vi-VN-Standard-A",
        speaking_rate: float = 1.0
    ):
        """
        初期化

        Args:
            language_code: 言語コード (vi-VN: ベトナム語)
            voice_name: 音声名
            speaking_rate: 発話速度 (0.25 ~ 4.0)
        """
        self.language_code = language_code
        self.voice_name = voice_name
        self.speaking_rate = speaking_rate
        self._client = None

    def _get_client(self):
        """クライアントを遅延初期化"""
        if self._client is None:
            try:
                from google.cloud import texttospeech
                self._client = texttospeech.TextToSpeechClient()
            except ImportError:
                raise ImportError(
                    "google-cloud-texttospeech がインストールされていません。\n"
                    "pip install google-cloud-texttospeech を実行してください。"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Google Cloud TTS クライアントの初期化に失敗しました: {e}\n"
                    "GOOGLE_APPLICATION_CREDENTIALS 環境変数を確認してください。"
                )
        return self._client

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        audio_format: str = "mp3"
    ) -> Path:
        """
        テキストを音声に変換

        Args:
            text: 変換するテキスト
            output_path: 出力ファイルパス
            audio_format: 出力形式 (mp3 or wav)

        Returns:
            生成された音声ファイルのパス
        """
        from google.cloud import texttospeech

        client = self._get_client()
        output_path = Path(output_path)

        # 入力テキストの設定
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # 音声の設定
        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name
        )

        # 音声形式の設定
        if audio_format.lower() == "mp3":
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.speaking_rate
            )
        else:
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                speaking_rate=self.speaking_rate
            )

        # 音声合成の実行
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # ファイルに保存
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.audio_content)

        return output_path

    def synthesize_batch(
        self,
        texts: list[str],
        output_dir: str | Path,
        prefix: str = "audio"
    ) -> list[Path]:
        """
        複数のテキストを一括で音声に変換

        Args:
            texts: 変換するテキストのリスト
            output_dir: 出力ディレクトリ
            prefix: ファイル名のプレフィックス

        Returns:
            生成された音声ファイルのパスのリスト
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = []
        for i, text in enumerate(texts):
            output_path = output_dir / f"{prefix}_{i:04d}.mp3"
            self.synthesize(text, output_path)
            output_paths.append(output_path)

        return output_paths
