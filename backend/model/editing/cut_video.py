"""Video cutting module for applying edit instructions."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from model.common.schemas import EditInstruction, KeepInterval
from model.editing.instruction_utils import load_edit_instruction, validate_edit_instruction


class VideoCutter:
    """Cuts raw video according to generated keep intervals."""

    def cut(self, instruction: EditInstruction) -> str:
        """Cut a video using keep intervals.

        Input: raw video path and keep intervals.
        Output: edited video path.
        """
        validate_edit_instruction(instruction)

        input_path = Path(instruction.video_path)
        output_path = Path(instruction.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {instruction.video_path}")

        if not instruction.keep_intervals:
            raise ValueError(
                "Edit instruction has no keep intervals. "
                "Cannot cut video with an empty keep list."
            )

        duration = self._read_video_duration(input_path)
        normalized_intervals = self._normalize_intervals(
            intervals=instruction.keep_intervals,
            duration=duration,
        )
        if not normalized_intervals:
            raise ValueError(
                "No valid keep intervals remain after clamping to video duration."
            )

        try:
            self._cut_with_moviepy(
                input_path=input_path,
                output_path=output_path,
                intervals=normalized_intervals,
            )
        except Exception as moviepy_exc:
            self._cut_with_ffmpeg(
                input_path=input_path,
                output_path=output_path,
                intervals=normalized_intervals,
            )
            print(f"MoviePy failed; used ffmpeg fallback: {moviepy_exc}")

        total_kept = sum(interval.end - interval.start for interval in normalized_intervals)
        print("Video cut summary:")
        print(f"- source video: {input_path}")
        print(f"- output video: {output_path}")
        print(f"- number of intervals: {len(normalized_intervals)}")
        print(f"- total kept duration: {total_kept:.2f}s")
        return str(output_path)

    def cut_from_instruction_json(self, instruction_json_path: str) -> str:
        """JSON-driven cutting flow."""
        instruction = load_edit_instruction(instruction_json_path)
        validate_edit_instruction(instruction)
        return self.cut(instruction)

    def _read_video_duration(self, input_path: Path) -> float:
        try:
            from moviepy import VideoFileClip
        except Exception as exc:
            raise RuntimeError(
                "MoviePy is required to inspect source video duration."
            ) from exc

        clip = VideoFileClip(str(input_path))
        try:
            return float(clip.duration or 0.0)
        finally:
            clip.close()

    def _cut_with_moviepy(
        self,
        input_path: Path,
        output_path: Path,
        intervals: list[KeepInterval],
    ) -> None:
        from moviepy import VideoFileClip, concatenate_videoclips

        source = VideoFileClip(str(input_path))
        clips = []
        final_video = None
        try:
            for interval in intervals:
                clips.append(source.subclipped(interval.start, interval.end))
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
        finally:
            if final_video is not None:
                try:
                    final_video.close()
                except Exception:
                    pass
            for clip in clips:
                try:
                    clip.close()
                except Exception:
                    pass
            source.close()

    def _cut_with_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        intervals: list[KeepInterval],
    ) -> None:
        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin is None:
            raise RuntimeError("ffmpeg executable not found in PATH.")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            segment_paths: list[Path] = []

            for idx, interval in enumerate(intervals):
                segment_path = tmp_path / f"segment_{idx:04d}.mp4"
                command = [
                    ffmpeg_bin,
                    "-y",
                    "-i",
                    str(input_path),
                    "-ss",
                    f"{interval.start:.6f}",
                    "-to",
                    f"{interval.end:.6f}",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    str(segment_path),
                ]
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                segment_paths.append(segment_path)

            list_file = tmp_path / "concat_list.txt"
            list_file.write_text(
                "\n".join(f"file '{path.as_posix()}'" for path in segment_paths),
                encoding="utf-8",
            )
            concat_command = [
                ffmpeg_bin,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(output_path),
            ]
            subprocess.run(
                concat_command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def _normalize_intervals(
        self,
        intervals: list[KeepInterval],
        duration: float,
    ) -> list[KeepInterval]:
        normalized: list[KeepInterval] = []
        for interval in intervals:
            start = max(0.0, min(interval.start, duration))
            end = max(0.0, min(interval.end, duration))
            if end <= start:
                continue
            if (end - start) < 0.05:
                continue
            normalized.append(
                KeepInterval(start=start, end=end, reason=interval.reason)
            )
        return normalized
