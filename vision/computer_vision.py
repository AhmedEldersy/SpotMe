import os
import sys
import json
import math
import uuid
import shutil
import tempfile
import argparse
import datetime
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["GLOG_minloglevel"] = "2"
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks_python
from mediapipe.tasks.python import vision as mp_tasks_vision
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

SUPPORTED_SPORTS = ["Football", "Basketball", "Volleyball", "Handball"]

POSE_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
POSE_LANDMARKER_MODEL_DIR = os.environ.get(
    "CV_MODEL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
)
POSE_LANDMARKER_MODEL_PATH = os.path.join(POSE_LANDMARKER_MODEL_DIR, "pose_landmarker_lite.task")


def ensure_pose_landmarker_model() -> str:
    """Downloads the pose landmarker model bundle on first use and caches it locally."""
    if os.path.isfile(POSE_LANDMARKER_MODEL_PATH) and os.path.getsize(POSE_LANDMARKER_MODEL_PATH) > 0:
        return POSE_LANDMARKER_MODEL_PATH
    os.makedirs(POSE_LANDMARKER_MODEL_DIR, exist_ok=True)
    tmp_path = POSE_LANDMARKER_MODEL_PATH + ".part"
    try:
        urllib.request.urlretrieve(POSE_LANDMARKER_MODEL_URL, tmp_path)
        os.replace(tmp_path, POSE_LANDMARKER_MODEL_PATH)
    except Exception as error:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise VideoAnalysisError(
            f"Could not download the pose landmarker model, {str(error)}. "
            f"You can also download it manually from {POSE_LANDMARKER_MODEL_URL} "
            f"and place it at {POSE_LANDMARKER_MODEL_PATH}."
        )
    return POSE_LANDMARKER_MODEL_PATH

SPRINT_THRESHOLD_MS = 5.5
HIGH_INTENSITY_THRESHOLD_MS = 4.0
MIN_SPRINT_DURATION_S = 0.6
BALL_PROXIMITY_PIXELS = 55
LANDING_WINDOW_FRAMES = 8
PROCESSING_WIDTH = 640
SPEED_SMOOTHING_WINDOW = 5
BACKGROUND_WARMUP_FRAMES = 20
MAX_PLAUSIBLE_HUMAN_SPEED_MS = 12.0
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
MAX_UPLOAD_SIZE_MB = int(os.environ.get("CV_MAX_UPLOAD_MB", "300"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
UPLOAD_TEMP_DIR = os.environ.get("CV_UPLOAD_TEMP_DIR", tempfile.gettempdir())

BALL_COLOR_PRESETS = {
    "orange": ((5, 120, 120), (18, 255, 255)),
    "yellow": ((20, 100, 100), (35, 255, 255)),
    "white": ((0, 0, 200), (180, 40, 255)),
    "green": ((36, 80, 80), (70, 255, 255)),
}


class VideoAnalysisError(Exception):
    pass


@dataclass
class TrackedPoint:
    frame_index: int
    timestamp_s: float
    x: float
    y: float


@dataclass
class PoseSnapshot:
    frame_index: int
    timestamp_s: float
    landmarks: Dict[str, Tuple[float, float, float]]


@dataclass
class VideoAnalysisConfig:
    video_path: str
    sport: str
    position: Optional[str] = None
    fps_override: Optional[float] = None
    pixels_per_meter: Optional[float] = None
    player_height_cm: Optional[float] = None
    ball_color: Optional[str] = None
    ball_hsv_lower: Optional[Tuple[int, int, int]] = None
    ball_hsv_upper: Optional[Tuple[int, int, int]] = None
    max_frames: Optional[int] = None
    output_path: Optional[str] = None


def validate_config(config: VideoAnalysisConfig):
    if config.sport not in SUPPORTED_SPORTS:
        raise VideoAnalysisError(
            f"Unsupported sport '{config.sport}'. Supported sports are {SUPPORTED_SPORTS}."
        )
    if not os.path.isfile(config.video_path):
        raise VideoAnalysisError(f"Video file not found at '{config.video_path}'.")
    if config.ball_color is not None and config.ball_color not in BALL_COLOR_PRESETS:
        raise VideoAnalysisError(
            f"Unknown ball_color preset '{config.ball_color}'. Options are {list(BALL_COLOR_PRESETS.keys())}."
        )


def moving_average(values: List[float], window: int) -> List[float]:
    if len(values) == 0:
        return []
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start:i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


class PlayerMotionTracker:
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=40, detectShadows=False
        )
        self.points: List[TrackedPoint] = []
        self.last_centroid: Optional[Tuple[float, float]] = None

    def process_frame(self, frame_index: int, timestamp_s: float, frame_bgr: np.ndarray):
        mask = self.bg_subtractor.apply(frame_bgr)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 250:
            return
        moments = cv2.moments(largest)
        if moments["m00"] == 0:
            return
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        self.points.append(TrackedPoint(frame_index, timestamp_s, cx, cy))
        self.last_centroid = (cx, cy)

    def get_points(self) -> List[TrackedPoint]:
        return self.points


class PoseTracker:

    LANDMARK_INDEX = {
        "nose": 0,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
        "left_heel": 29,
        "right_heel": 30,
        "left_foot_index": 31,
        "right_foot_index": 32,
    }

    def __init__(self):
        model_path = ensure_pose_landmarker_model()
        base_options = mp_tasks_python.BaseOptions(model_asset_path=model_path)
        options = mp_tasks_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_tasks_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = mp_tasks_vision.PoseLandmarker.create_from_options(options)
        self.snapshots: List[PoseSnapshot] = []
        self.frames_with_pose = 0
        self.frames_processed = 0
        self._last_timestamp_ms = -1

    def process_frame(self, frame_index: int, timestamp_s: float, frame_rgb: np.ndarray):
        self.frames_processed += 1
        h, w, _ = frame_rgb.shape

        timestamp_ms = int(timestamp_s * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame_rgb))
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.pose_landmarks:
            return
        self.frames_with_pose += 1
        pose_landmarks = result.pose_landmarks[0]
        landmarks = {}
        for name, idx in self.LANDMARK_INDEX.items():
            lm = pose_landmarks[idx]
            visibility = getattr(lm, "visibility", 1.0)
            landmarks[name] = (lm.x * w, lm.y * h, visibility)
        self.snapshots.append(PoseSnapshot(frame_index, timestamp_s, landmarks))

    def close(self):
        self.landmarker.close()

    def detection_rate(self) -> float:
        if self.frames_processed == 0:
            return 0.0
        return self.frames_with_pose / self.frames_processed


class BallTracker:
    def __init__(self, hsv_lower: Tuple[int, int, int], hsv_upper: Tuple[int, int, int]):
        self.hsv_lower = np.array(hsv_lower, dtype=np.uint8)
        self.hsv_upper = np.array(hsv_upper, dtype=np.uint8)
        self.points: List[TrackedPoint] = []
        self.frames_with_ball = 0
        self.frames_processed = 0

    def process_frame(self, frame_index: int, timestamp_s: float, frame_bgr: np.ndarray):
        self.frames_processed += 1
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < 15 or area > 6000:
            return
        (x, y), radius = cv2.minEnclosingCircle(largest)
        circularity_area = math.pi * radius * radius
        if circularity_area == 0 or area / circularity_area < 0.5:
            return
        self.points.append(TrackedPoint(frame_index, timestamp_s, x, y))
        self.frames_with_ball += 1

    def detection_rate(self) -> float:
        if self.frames_processed == 0:
            return 0.0
        return self.frames_with_ball / self.frames_processed


def compute_motion_metrics(
    points: List[TrackedPoint], pixels_per_meter: Optional[float]
) -> Dict[str, Any]:
    empty_result = {
        "speed_avg_ms": None,
        "top_speed_ms": None,
        "acceleration_ms2": None,
        "deceleration_ms2": None,
        "distance_covered_m": None,
        "sprint_count": None,
        "high_intensity_runs": None,
        "movement_efficiency": None,
        "fatigue_index": None,
        "outlier_segments_removed": 0,
    }

    if len(points) < 2 or pixels_per_meter is None:
        return empty_result

    usable_points = [p for p in points if p.frame_index >= BACKGROUND_WARMUP_FRAMES]
    if len(usable_points) < 2:
        usable_points = points

    speeds = []
    distances = []
    kept_points = [usable_points[0]]
    outliers_removed = 0
    for i in range(1, len(usable_points)):
        p0, p1 = usable_points[i - 1], usable_points[i]
        dt = p1.timestamp_s - p0.timestamp_s
        if dt <= 0:
            continue
        dx = (p1.x - p0.x) / pixels_per_meter
        dy = (p1.y - p0.y) / pixels_per_meter
        dist = math.hypot(dx, dy)
        instant_speed = dist / dt
        if instant_speed > MAX_PLAUSIBLE_HUMAN_SPEED_MS:
            outliers_removed += 1
            continue
        distances.append(dist)
        speeds.append(instant_speed)
        kept_points.append(p1)

    if not speeds:
        empty_result["outlier_segments_removed"] = outliers_removed
        return empty_result

    points = kept_points

    smoothed = moving_average(speeds, SPEED_SMOOTHING_WINDOW)
    total_distance = sum(distances)
    avg_speed = sum(smoothed) / len(smoothed)
    top_speed = max(smoothed)

    accelerations = []
    for i in range(1, len(smoothed)):
        dt = points[i + 1].timestamp_s - points[i].timestamp_s
        if dt <= 0:
            continue
        accelerations.append((smoothed[i] - smoothed[i - 1]) / dt)
    max_accel = max(accelerations) if accelerations else None
    max_decel = min(accelerations) if accelerations else None

    sprint_count = 0
    high_intensity_runs = 0
    in_sprint = False
    in_high_intensity = False
    sprint_start_t = None
    hi_start_t = None
    for i, s in enumerate(smoothed):
        t = points[i + 1].timestamp_s
        if s >= SPRINT_THRESHOLD_MS:
            if not in_sprint:
                in_sprint = True
                sprint_start_t = t
        else:
            if in_sprint and sprint_start_t is not None and (t - sprint_start_t) >= MIN_SPRINT_DURATION_S:
                sprint_count += 1
            in_sprint = False
            sprint_start_t = None

        if s >= HIGH_INTENSITY_THRESHOLD_MS:
            if not in_high_intensity:
                in_high_intensity = True
                hi_start_t = t
        else:
            if in_high_intensity and hi_start_t is not None and (t - hi_start_t) >= MIN_SPRINT_DURATION_S:
                high_intensity_runs += 1
            in_high_intensity = False
            hi_start_t = None

    if in_sprint and sprint_start_t is not None and (points[-1].timestamp_s - sprint_start_t) >= MIN_SPRINT_DURATION_S:
        sprint_count += 1
    if in_high_intensity and hi_start_t is not None and (points[-1].timestamp_s - hi_start_t) >= MIN_SPRINT_DURATION_S:
        high_intensity_runs += 1

    net_dx = (points[-1].x - points[0].x) / pixels_per_meter
    net_dy = (points[-1].y - points[0].y) / pixels_per_meter
    net_displacement = math.hypot(net_dx, net_dy)
    movement_efficiency = None
    if total_distance > 0:
        movement_efficiency = round(min(net_displacement / total_distance, 1.0), 3)

    fatigue_index = None
    if len(smoothed) >= 10:
        half = len(smoothed) // 2
        first_half_avg = sum(smoothed[:half]) / half
        second_half_avg = sum(smoothed[half:]) / (len(smoothed) - half)
        if first_half_avg > 0:
            fatigue_index = round(max(0.0, min(1.0, (first_half_avg - second_half_avg) / first_half_avg)), 3)

    return {
        "speed_avg_ms": round(avg_speed, 2),
        "top_speed_ms": round(top_speed, 2),
        "acceleration_ms2": round(max_accel, 2) if max_accel is not None else None,
        "deceleration_ms2": round(max_decel, 2) if max_decel is not None else None,
        "distance_covered_m": round(total_distance, 2),
        "sprint_count": sprint_count,
        "high_intensity_runs": high_intensity_runs,
        "movement_efficiency": movement_efficiency,
        "fatigue_index": fatigue_index,
        "outlier_segments_removed": outliers_removed,
    }


def estimate_pixels_per_meter(
    snapshots: List[PoseSnapshot], player_height_cm: Optional[float]
) -> Optional[float]:
    if not snapshots or player_height_cm is None or player_height_cm <= 0:
        return None
    spans = []
    for snap in snapshots:
        lm = snap.landmarks
        if "nose" not in lm or "left_ankle" not in lm or "right_ankle" not in lm:
            continue
        nose_y = lm["nose"][1]
        ankle_y = max(lm["left_ankle"][1], lm["right_ankle"][1])
        span = ankle_y - nose_y
        if span > 0:
            spans.append(span)
    if not spans:
        return None
    median_span_px = sorted(spans)[len(spans) // 2]
    body_fraction = 0.87
    height_m = player_height_cm / 100.0
    estimated_full_body_px = median_span_px / body_fraction
    return estimated_full_body_px / height_m


def compute_jump_and_stability_metrics(
    snapshots: List[PoseSnapshot], pixels_per_meter: Optional[float]
) -> Dict[str, Any]:
    if len(snapshots) < 5:
        return {
            "jump_height_cm": None,
            "landing_stability": None,
            "balance": None,
        }

    hip_y_series = []
    for snap in snapshots:
        lm = snap.landmarks
        if "left_hip" in lm and "right_hip" in lm:
            hip_y = (lm["left_hip"][1] + lm["right_hip"][1]) / 2.0
            hip_y_series.append(hip_y)

    jump_height_cm = None
    if pixels_per_meter is not None and len(hip_y_series) >= 5:
        baseline = sorted(hip_y_series)[int(len(hip_y_series) * 0.9):]
        baseline_y = sum(baseline) / len(baseline) if baseline else max(hip_y_series)
        peak_y = min(hip_y_series)
        jump_px = max(0.0, baseline_y - peak_y)
        jump_height_cm = round((jump_px / pixels_per_meter) * 100.0, 1)
        if jump_height_cm < 3.0:
            jump_height_cm = None

    landing_stability = None
    if len(hip_y_series) >= 5:
        peak_index = hip_y_series.index(min(hip_y_series))
        window_end = min(len(snapshots), peak_index + LANDING_WINDOW_FRAMES)
        landing_snaps = snapshots[peak_index:window_end]
        ankle_xs = []
        for snap in landing_snaps:
            lm = snap.landmarks
            if "left_ankle" in lm and "right_ankle" in lm:
                ankle_xs.append((lm["left_ankle"][0] + lm["right_ankle"][0]) / 2.0)
        if len(ankle_xs) >= 3:
            std_dev = float(np.std(ankle_xs))
            normalized = min(std_dev / 40.0, 1.0)
            landing_stability = round(1.0 - normalized, 3)

    balance = None
    lean_angles = []
    for snap in snapshots:
        lm = snap.landmarks
        if "left_shoulder" in lm and "right_shoulder" in lm and "left_hip" in lm and "right_hip" in lm:
            shoulder_mid = (
                (lm["left_shoulder"][0] + lm["right_shoulder"][0]) / 2.0,
                (lm["left_shoulder"][1] + lm["right_shoulder"][1]) / 2.0,
            )
            hip_mid = (
                (lm["left_hip"][0] + lm["right_hip"][0]) / 2.0,
                (lm["left_hip"][1] + lm["right_hip"][1]) / 2.0,
            )
            dx = shoulder_mid[0] - hip_mid[0]
            dy = shoulder_mid[1] - hip_mid[1]
            angle = math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))
            lean_angles.append(angle)
    if len(lean_angles) >= 5:
        std_angle = float(np.std(lean_angles))
        balance = round(max(0.0, 1.0 - min(std_angle / 20.0, 1.0)), 3)

    return {
        "jump_height_cm": jump_height_cm,
        "landing_stability": landing_stability,
        "balance": balance,
    }


def compute_ball_metrics(
    ball_points: List[TrackedPoint], player_points: List[TrackedPoint]
) -> Dict[str, Any]:
    if not ball_points or not player_points:
        return {"ball_touches": None}

    player_by_frame = {p.frame_index: p for p in player_points}
    touches = 0
    was_close = False
    for bp in ball_points:
        candidates = [p for p in player_points if abs(p.frame_index - bp.frame_index) <= 2]
        if not candidates:
            continue
        nearest = min(candidates, key=lambda p: abs(p.frame_index - bp.frame_index))
        dist = math.hypot(bp.x - nearest.x, bp.y - nearest.y)
        is_close = dist <= BALL_PROXIMITY_PIXELS
        if is_close and not was_close:
            touches += 1
        was_close = is_close

    return {"ball_touches": touches}


def resolve_ball_hsv_range(config: VideoAnalysisConfig) -> Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
    if config.ball_hsv_lower is not None and config.ball_hsv_upper is not None:
        return config.ball_hsv_lower, config.ball_hsv_upper
    if config.ball_color is not None:
        return BALL_COLOR_PRESETS[config.ball_color]
    return None


def analyze_video(config: VideoAnalysisConfig) -> Dict[str, Any]:
    validate_config(config)

    capture = cv2.VideoCapture(config.video_path)
    if not capture.isOpened():
        capture.release()
        raise VideoAnalysisError(f"Could not open video file '{config.video_path}'.")

    pose_tracker = None

    try:
        source_fps = capture.get(cv2.CAP_PROP_FPS)
        fps = config.fps_override or (source_fps if source_fps and source_fps > 1 else 25.0)
        source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count_meta = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        scale = 1.0
        if source_width > PROCESSING_WIDTH and source_width > 0:
            scale = PROCESSING_WIDTH / source_width

        player_tracker = PlayerMotionTracker()
        pose_tracker = PoseTracker()

        ball_hsv_range = resolve_ball_hsv_range(config)
        ball_tracker = BallTracker(*ball_hsv_range) if ball_hsv_range else None

        frame_index = 0
        processed_frames = 0

        while True:
            ret, frame = capture.read()
            if not ret:
                break
            if config.max_frames is not None and processed_frames >= config.max_frames:
                break

            timestamp_s = frame_index / fps

            if scale != 1.0:
                frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)

            player_tracker.process_frame(frame_index, timestamp_s, frame)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb.flags.writeable = False
            pose_tracker.process_frame(frame_index, timestamp_s, frame_rgb)

            if ball_tracker is not None:
                ball_tracker.process_frame(frame_index, timestamp_s, frame)

            frame_index += 1
            processed_frames += 1

            if processed_frames % 60 == 0:
                print(
                    f"[analyze_video] processed {processed_frames} frames "
                    f"({round(processed_frames / fps, 1)}s of video)"
                )
    finally:
        capture.release()
        if pose_tracker is not None:
            pose_tracker.close()

    if processed_frames == 0:
        raise VideoAnalysisError("No frames could be read from the video file.")

    pixels_per_meter = config.pixels_per_meter
    calibration_source = "manual" if pixels_per_meter else None
    if pixels_per_meter is None:
        pixels_per_meter = estimate_pixels_per_meter(pose_tracker.snapshots, config.player_height_cm)
        if pixels_per_meter is not None:
            calibration_source = "estimated_from_player_height"

    motion_metrics = compute_motion_metrics(player_tracker.get_points(), pixels_per_meter)
    pose_metrics = compute_jump_and_stability_metrics(pose_tracker.snapshots, pixels_per_meter)

    ball_metrics = {"ball_touches": None}
    ball_detection_rate = 0.0
    if ball_tracker is not None:
        ball_metrics = compute_ball_metrics(ball_tracker.points, player_tracker.get_points())
        ball_detection_rate = ball_tracker.detection_rate()

    pose_detection_rate = pose_tracker.detection_rate()
    player_detection_rate = len(player_tracker.get_points()) / processed_frames

    metrics = {
        "distance_covered_m": motion_metrics["distance_covered_m"],
        "speed_avg_ms": motion_metrics["speed_avg_ms"],
        "top_speed_ms": motion_metrics["top_speed_ms"],
        "acceleration_ms2": motion_metrics["acceleration_ms2"],
        "deceleration_ms2": motion_metrics["deceleration_ms2"],
        "sprint_count": motion_metrics["sprint_count"],
        "high_intensity_runs": motion_metrics["high_intensity_runs"],
        "movement_efficiency": motion_metrics["movement_efficiency"],
        "fatigue_index": motion_metrics["fatigue_index"],
        "jump_height_cm": pose_metrics["jump_height_cm"],
        "landing_stability": pose_metrics["landing_stability"],
        "balance": pose_metrics["balance"],
        "ball_touches": ball_metrics["ball_touches"],
        "video_duration_s": round(processed_frames / fps, 2),
        "frames_analyzed": processed_frames,
    }

    notes = []
    notes.append(f"Source resolution {source_width}x{source_height}, processed at scale {round(scale, 2)}.")
    notes.append(f"Reported frame rate used for timing calculations, {round(fps, 2)} fps.")
    if frame_count_meta and abs(frame_count_meta - processed_frames) > max(5, int(frame_count_meta * 0.05)):
        notes.append("Frame count metadata did not match frames actually decoded, results are based on decoded frames only.")

    outliers_removed = motion_metrics.get("outlier_segments_removed", 0)
    if outliers_removed:
        notes.append(f"{outliers_removed} tracking segment(s) exceeded plausible human sprint speed and were treated as tracking glitches and excluded from speed and distance calculations.")

    if pixels_per_meter is None:
        notes.append("No pixel to meter calibration was available, speed, distance, acceleration, sprint count, and jump height could not be computed and are reported as null rather than estimated.")
    elif calibration_source == "estimated_from_player_height":
        notes.append("Distance based metrics were calibrated from the provided player height and pose landmarks, treat as an approximation rather than a precise measurement.")
    else:
        notes.append("Distance based metrics used a manually supplied pixels per meter calibration value.")

    if player_detection_rate < 0.5:
        notes.append(f"Player motion was detected in only {round(player_detection_rate * 100, 1)} percent of frames, motion based metrics have reduced reliability, check for a static camera, stable lighting, and a single subject in frame.")

    if pose_detection_rate < 0.5:
        notes.append(f"Full body pose was detected in only {round(pose_detection_rate * 100, 1)} percent of frames, jump height, landing stability, and balance metrics have reduced reliability.")

    if ball_tracker is None:
        notes.append("No ball color range was configured, ball touches could not be measured and is reported as null.")
    elif ball_detection_rate < 0.2:
        notes.append(f"Ball was detected in only {round(ball_detection_rate * 100, 1)} percent of frames, ball touches figure has low reliability, verify the ball color preset matches the actual ball and lighting conditions.")

    confidence_components = [player_detection_rate, pose_detection_rate]
    if ball_tracker is not None:
        confidence_components.append(ball_detection_rate)
    confidence_score = round(sum(confidence_components) / len(confidence_components), 3)

    file_mtime = os.path.getmtime(config.video_path)
    capture_date = datetime.datetime.fromtimestamp(file_mtime, tz=datetime.timezone.utc).isoformat()

    result = {
        "metrics": metrics,
        "confidence_score": confidence_score,
        "video_quality_notes": " ".join(notes),
        "capture_date": capture_date,
    }

    return result


def parse_hsv_arg(value: Optional[str]) -> Optional[Tuple[int, int, int]]:
    if value is None:
        return None
    parts = value.split(",")
    if len(parts) != 3:
        raise VideoAnalysisError(f"HSV value '{value}' must have exactly three comma separated numbers.")
    return tuple(int(p.strip()) for p in parts)



cv_app = APIRouter()


@cv_app.get("/health")
def cv_health_check():
    return {
        "status": "ok",
        "supported_sports": SUPPORTED_SPORTS,
        "ball_color_presets": list(BALL_COLOR_PRESETS.keys()),
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "allowed_extensions": sorted(ALLOWED_VIDEO_EXTENSIONS),
    }


@cv_app.post("/analyze-video")
async def analyze_video_upload(
    video: UploadFile = File(...),
    sport: str = Form(...),
    position: Optional[str] = Form(None),
    fps: Optional[float] = Form(None),
    pixels_per_meter: Optional[float] = Form(None),
    player_height_cm: Optional[float] = Form(None),
    ball_color: Optional[str] = Form(None),
    max_frames: Optional[int] = Form(None),
):
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported sport '{sport}'. Supported sports are {SUPPORTED_SPORTS}."
        )

    if ball_color is not None and ball_color not in BALL_COLOR_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown ball_color preset '{ball_color}'. Options are {list(BALL_COLOR_PRESETS.keys())}."
        )

    if not video.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    extension = os.path.splitext(video.filename)[1].lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{extension}'. Allowed extensions are {sorted(ALLOWED_VIDEO_EXTENSIONS)}."
        )

    os.makedirs(UPLOAD_TEMP_DIR, exist_ok=True)
    temp_filename = f"cv_upload_{uuid.uuid4().hex}{extension}"
    temp_path = os.path.join(UPLOAD_TEMP_DIR, temp_filename)

    bytes_written = 0
    try:
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded file exceeds the maximum allowed size of {MAX_UPLOAD_SIZE_MB} MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    except Exception as error:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file, {str(error)}.")
    finally:
        await video.close()

    if bytes_written == 0:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        config = VideoAnalysisConfig(
            video_path=temp_path,
            sport=sport,
            position=position,
            fps_override=fps,
            pixels_per_meter=pixels_per_meter,
            player_height_cm=player_height_cm,
            ball_color=ball_color,
            max_frames=max_frames,
        )
        result = analyze_video(config)
    except VideoAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract sports performance metrics from a video using computer vision."
    )
    parser.add_argument("--video", required=True, help="Path to the input video file.")
    parser.add_argument("--sport", required=True, choices=SUPPORTED_SPORTS, help="Sport being analyzed.")
    parser.add_argument("--position", required=False, default=None, help="Player position, optional.")
    parser.add_argument("--fps", required=False, type=float, default=None, help="Override the detected frame rate.")
    parser.add_argument("--pixels-per-meter", required=False, type=float, default=None, help="Manual pixel to meter calibration value.")
    parser.add_argument("--player-height-cm", required=False, type=float, default=None, help="Player height in centimeters, used to estimate calibration if pixels per meter is not provided.")
    parser.add_argument("--ball-color", required=False, choices=list(BALL_COLOR_PRESETS.keys()), default=None, help="Preset HSV color range for ball tracking.")
    parser.add_argument("--ball-hsv-lower", required=False, default=None, help="Custom ball HSV lower bound as H,S,V")
    parser.add_argument("--ball-hsv-upper", required=False, default=None, help="Custom ball HSV upper bound as H,S,V")
    parser.add_argument("--max-frames", required=False, type=int, default=None, help="Cap the number of frames processed.")
    parser.add_argument("--output", required=False, default=None, help="Path to write the resulting JSON file.")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    config = VideoAnalysisConfig(
        video_path=args.video,
        sport=args.sport,
        position=args.position,
        fps_override=args.fps,
        pixels_per_meter=args.pixels_per_meter,
        player_height_cm=args.player_height_cm,
        ball_color=args.ball_color,
        ball_hsv_lower=parse_hsv_arg(args.ball_hsv_lower),
        ball_hsv_upper=parse_hsv_arg(args.ball_hsv_upper),
        max_frames=args.max_frames,
        output_path=args.output,
    )

    try:
        result = analyze_video(config)
    except VideoAnalysisError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(1)

    output_json = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"Analysis written to {args.output}")
    else:
        print(output_json)

if __name__ == "__main__":
    main()