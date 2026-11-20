import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np
from app.agents.base import BaseAgent
from app.core.logging import logger

try:
    import mediapipe as mp
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_detection"):
        mp_face_detection = mp.solutions.face_detection
        HAS_MEDIAPIPE = True
    else:
        mp_face_detection = None
        HAS_MEDIAPIPE = False
        logger.info("MediaPipe installed without solutions API; using OpenCV Haar cascade / center crop fallback.")
except Exception as e:
    mp_face_detection = None
    HAS_MEDIAPIPE = False
    logger.warning(f"MediaPipe not available ({e}), face detection will use center crop fallback.")

class ReframeAgent(BaseAgent):
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        super().__init__("reframe")
        self.target_width = target_width
        self.target_height = target_height

    def _detect_faces_trajectory(self, video_path: str, sample_interval_sec: float = 0.5) -> Tuple[float, float, int, int]:
        """
        Samples video every `sample_interval_sec` and tracks streamer face center (normalized 0.0 - 1.0).
        Returns: (smoothed_avg_center_x, smoothed_avg_center_y, video_width, video_height)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0.5, 0.3, 1920, 1080

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_step = max(1, int(fps * sample_interval_sec))

        centers_x: List[float] = []
        centers_y: List[float] = []

        if HAS_MEDIAPIPE:
            with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detector:
                frame_idx = 0
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_idx % frame_step == 0:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_detector.process(rgb_frame)

                        if results.detections:
                            # Pick largest face
                            best_detection = max(
                                results.detections,
                                key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height
                            )
                            box = best_detection.location_data.relative_bounding_box
                            cx = box.xmin + (box.width / 2.0)
                            cy = box.ymin + (box.height / 2.0)
                            centers_x.append(cx)
                            centers_y.append(cy)

                    frame_idx += 1

        cap.release()

        # If no face detected, default to center
        if not centers_x:
            return 0.5, 0.35, width, height

        # Exponential moving average smoothing to prevent camera jump
        smoothed_x = centers_x[0]
        smoothed_y = centers_y[0]
        alpha = 0.2
        for x, y in zip(centers_x[1:], centers_y[1:]):
            smoothed_x = alpha * x + (1.0 - alpha) * smoothed_x
            smoothed_y = alpha * y + (1.0 - alpha) * smoothed_y

        return float(np.clip(smoothed_x, 0.0, 1.0)), float(np.clip(smoothed_y, 0.0, 1.0)), width, height

    def run(
        self,
        job_id: str,
        clip_paths: List[str],
        layout: str = "focus", # 'focus', 'split', or 'header_banner'
        banner_text: Optional[str] = None,
        font_size: Optional[int] = 48,
        font_family: Optional[str] = "Arial",
        font_color: Optional[str] = None
    ) -> List[str]:
        reframed_paths: List[str] = []

        # Safe defaults and fallbacks for custom fonts and sizes
        fs = font_size if (font_size and font_size >= 16 and font_size <= 120) else 48
        font_param = f":font='{font_family}'" if font_family and font_family != "Default" else ""

        for idx, clip_path in enumerate(clip_paths):
            output_path = clip_path.replace("_raw.mp4", "_reframed.mp4")
            logger.info(f"[{job_id}] Reframing clip #{idx} to 9:16 ({layout} layout, fontsize={fs})...")

            # 1. Detect face coordinates
            center_x, center_y, src_w, src_h = self._detect_faces_trajectory(clip_path)

            if layout == "split":
                # Layout Split:
                # Top (35% = 672px): Crop focused on face
                # Bottom (65% = 1248px): Center crop of gameplay / main video
                face_crop_w = int(src_h * 0.7)
                face_crop_h = int(src_h * 0.7)
                face_x = int(np.clip(center_x * src_w - (face_crop_w / 2), 0, src_w - face_crop_w))
                face_y = int(np.clip(center_y * src_h - (face_crop_h / 2), 0, src_h - face_crop_h))

                filter_complex = (
                    f"[0:v]split=2[vtop_in][vbot_in];"
                    f"[vtop_in]crop={face_crop_w}:{face_crop_h}:{face_x}:{face_y},scale=1080:672[vtop];"
                    f"[vbot_in]crop=ih*(1080/1248):ih,scale=1080:1248[vbot];"
                    f"[vtop][vbot]vstack=inputs=2[v]"
                )
            elif layout == "header_banner":
                # Layout Template: Header Box/Banner atas (240px) untuk judul/reaksi + video 9:16 di bawah
                crop_w = int(src_h * (9.0 / 16.0))
                crop_h = src_h
                crop_x = int(np.clip(center_x * src_w - (crop_w / 2), 0, src_w - crop_w))
                crop_y = 0
                clean_banner = (banner_text or "HIGHLIGHT MOMENT").replace("'", "").replace(":", "")
                text_col = font_color or "white"

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1680:flags=lanczos[vmain];"
                    f"color=c=black:s=1080x240[vbox];"
                    f"[vbox]drawtext=text='{clean_banner}'{font_param}:fontcolor={text_col}:fontsize={fs}:box=1:boxcolor=black@0.8:boxborderw=10:x=(w-text_w)/2:y=(h-text_h)/2[vbanner];"
                    f"[vbanner][vmain]vstack=inputs=2[v]"
                )
            elif layout == "header_white":
                # Layout Template: Banner putih di atas (240px) dengan teks hitam/custom + video 9:16 di bawah
                crop_w = int(src_h * (9.0 / 16.0))
                crop_h = src_h
                crop_x = int(np.clip(center_x * src_w - (crop_w / 2), 0, src_w - crop_w))
                crop_y = 0
                clean_banner = (banner_text or "HIGHLIGHT MOMENT").replace("'", "").replace(":", "")
                text_col = font_color or "black"

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1680:flags=lanczos[vmain];"
                    f"color=c=white:s=1080x240[vbox];"
                    f"[vbox]drawtext=text='{clean_banner}'{font_param}:fontcolor={text_col}:fontsize={fs}:x=(w-text_w)/2:y=(h-text_h)/2[vbanner];"
                    f"[vbanner][vmain]vstack=inputs=2[v]"
                )
            elif layout == "footer_banner":
                # Layout Template: Video di atas (1680px) + Footer Banner tulisan custom di bawah (240px)
                crop_w = int(src_h * (9.0 / 16.0))
                crop_h = src_h
                crop_x = int(np.clip(center_x * src_w - (crop_w / 2), 0, src_w - crop_w))
                crop_y = 0
                clean_banner = (banner_text or "HIGHLIGHT MOMENT").replace("'", "").replace(":", "")
                text_col = font_color or "yellow"

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1680:flags=lanczos[vmain];"
                    f"color=c=black:s=1080x240[vbox];"
                    f"[vbox]drawtext=text='{clean_banner}'{font_param}:fontcolor={text_col}:fontsize={fs}:box=1:boxcolor=black@0.8:boxborderw=10:x=(w-text_w)/2:y=(h-text_h)/2[vfooter];"
                    f"[vmain][vfooter]vstack=inputs=2[v]"
                )
            elif layout == "top_bottom_banner":
                # Layout Template: Header Banner atas hitam (160px) + Video Tengah (1600px) + Footer Banner bawah (160px)
                crop_w = int(src_h * (9.0 / 16.0))
                crop_h = src_h
                crop_x = int(np.clip(center_x * src_w - (crop_w / 2), 0, src_w - crop_w))
                crop_y = 0
                clean_banner = (banner_text or "HIGHLIGHT MOMENT").replace("'", "").replace(":", "")
                text_col = font_color or "white"

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1600:flags=lanczos[vmain];"
                    f"color=c=black:s=1080x160[vtop];"
                    f"[vtop]drawtext=text='{clean_banner}'{font_param}:fontcolor={text_col}:fontsize={fs}:box=1:boxcolor=black@0.8:boxborderw=8:x=(w-text_w)/2:y=(h-text_h)/2[vheader];"
                    f"color=c=black:s=1080x160[vbot];"
                    f"[vbot]drawtext=text='TONTON SAMPAI HABIS!':fontcolor=yellow:fontsize=36:box=1:boxcolor=black@0.8:boxborderw=8:x=(w-text_w)/2:y=(h-text_h)/2[vfooter];"
                    f"[vheader][vmain][vfooter]vstack=inputs=3[v]"
                )
            elif layout == "fit_center_black":
                # Layout Clipper Klasik: Video 16:9 utuh di tengah, latar belakang HITAM di atas & bawah dengan teks clipper
                clean_banner = (banner_text or "HIGHLIGHT MOMENT").replace("'", "").replace(":", "")
                text_col = font_color or "white"
                filter_complex = (
                    f"color=c=black:s=1080x1920[vbg];"
                    f"[0:v]scale=1080:-1:flags=lanczos[vvid];"
                    f"[vbg][vvid]overlay=0:(H-h)/2[vmid];"
                    f"[vmid]drawtext=text='{clean_banner}'{font_param}:fontcolor={text_col}:fontsize={fs}:x=(w-text_w)/2:y=200,"
                    f"drawtext=text='SWIPE UP / TONTON SAMPAI HABIS!':fontcolor=yellow:fontsize=38:x=(w-text_w)/2:y=1650[v]"
                )
            elif layout == "fit_center_white":
                # Layout Clipper Modern: Video 16:9 utuh di tengah, latar belakang PUTIH di atas & bawah dengan teks hitam tebal
                clean_banner = (banner_text or "HIGHLIGHT MOMENT").replace("'", "").replace(":", "")
                text_col = font_color or "black"
                filter_complex = (
                    f"color=c=white:s=1080x1920[vbg];"
                    f"[0:v]scale=1080:-1:flags=lanczos[vvid];"
                    f"[vbg][vvid]overlay=0:(H-h)/2[vmid];"
                    f"[vmid]drawtext=text='{clean_banner}'{font_param}:fontcolor={text_col}:fontsize={fs}:fontweight=bold:x=(w-text_w)/2:y=220,"
                    f"drawtext=text='TONTON SAMPAI HABIS!':fontcolor=red:fontsize=40:fontweight=bold:x=(w-text_w)/2:y=1640[v]"
                )
            else:
                # Layout Focus (single vertical camera tracking face):
                # Target aspect ratio is 9:16.
                crop_w = int(src_h * (9.0 / 16.0))
                crop_h = src_h
                crop_x = int(np.clip(center_x * src_w - (crop_w / 2), 0, src_w - crop_w))
                crop_y = 0

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1920:flags=lanczos[v]"
                )

                filter_complex = (
                    f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1920:flags=lanczos[v]"
                )

            cmd = [
                "ffmpeg", "-y",
                "-i", clip_path,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-r", "30",
                "-c:a", "aac",
                "-b:a", "128k",
                output_path
            ]

            try:
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                reframed_paths.append(output_path)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed reframing clip #{idx}: {e.stderr.decode('utf-8', errors='ignore')}")
                raise RuntimeError(f"FFmpeg reframing failed for clip #{idx}") from None

        return reframed_paths
