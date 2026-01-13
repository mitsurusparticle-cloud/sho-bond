"""
Edge TTS 連携モジュール (無料代替オプション)
Microsoft Edge の音声合成を利用
"""
import asyncio
from pathlib import Path
from typing import Optional


class EdgeTTSClient:
    """Edge TTS クライアント（無料で使用可能）"""

    # ベトナム語の利用可能な音声
    VIETNAMESE_VOICES = [
        "vi-VN-HoaiMyNeural",   # 女性
        "vi-VN-NamMinhNeural",  # 男性
    ]

    def __init__(
        self,
        voice: str = "vi-VN-HoaiMyNeural",
        rate: str = "+0%",
        volume: str = "+0%"
    ):
        """
        初期化

        Args:
            voice: 音声名
            rate: 発話速度 (例: "+10%", "-20%")
            volume: 音量 (例: "+10%", "-20%")
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def _synthesize_async(
        self,
        text: str,
        output_path: str | Path
    ) -> Path:
        """
        非同期で音声合成

        Args:
            text: 変換するテキスト
            output_path: 出力ファイルパス

        Returns:
            生成された音声ファイルのパス
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError(
                "edge-tts がインストールされていません。\n"
                "pip install edge-tts を実行してください。"
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume
        )

        await communicate.save(str(output_path))
        return output_path

    def synthesize(
        self,
        text: str,
        output_path: str | Path
    ) -> Path:
        """
        テキストを音声に変換（同期版）

        Args:
            text: 変換するテキスト
            output_path: 出力ファイルパス

        Returns:
            生成された音声ファイルのパス
        """
        return asyncio.run(self._synthesize_async(text, output_path))

    async def _synthesize_batch_async(
        self,
        texts: list[str],
        output_dir: str | Path,
        prefix: str = "audio"
    ) -> list[Path]:
        """
        非同期で複数テキストを一括変換

        Args:
            texts: 変換するテキストのリスト
            output_dir: 出力ディレクトリ
            prefix: ファイル名のプレフィックス

        Returns:
            生成された音声ファイルのパスのリスト
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        output_paths = []
        for i, text in enumerate(texts):
            output_path = output_dir / f"{prefix}_{i:04d}.mp3"
            output_paths.append(output_path)
            tasks.append(self._synthesize_async(text, output_path))

        await asyncio.gather(*tasks)
        return output_paths

    def synthesize_batch(
        self,
        texts: list[str],
        output_dir: str | Path,
        prefix: str = "audio"
    ) -> list[Path]:
        """
        複数のテキストを一括で音声に変換（同期版）

        Args:
            texts: 変換するテキストのリスト
            output_dir: 出力ディレクトリ
            prefix: ファイル名のプレフィックス

        Returns:
            生成された音声ファイルのパスのリスト
        """
        return asyncio.run(
            self._synthesize_batch_async(texts, output_dir, prefix)
        )

    @classmethod
    def list_voices(cls) -> list[str]:
        """利用可能なベトナム語音声を返す"""
        return cls.VIETNAMESE_VOICES
