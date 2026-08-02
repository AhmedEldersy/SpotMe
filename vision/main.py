import os
import json
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from groq import Groq
from groq import APIError, APIConnectionError, APIStatusError, RateLimitError
from dotenv import load_dotenv


from computer_vision import (
    VideoAnalysisConfig,
    VideoAnalysisError,
    analyze_video,
    SUPPORTED_SPORTS as CV_SUPPORTED_SPORTS,
    BALL_COLOR_PRESETS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    UPLOAD_TEMP_DIR,
)
import knowledge_base as kb

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Every finished video analysis gets saved as a PDF report here, named after
# the player, in addition to being returned in the API response. Override
# with the CV_OUTPUT_DIR env var if you want it somewhere else (e.g. a
# shared network drive).
OUTPUT_DIR = os.environ.get(
    "CV_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Human-readable labels + units for each raw metrics key, used when
# rendering the PDF table.
METRIC_LABELS = {
    "distance_covered_m": ("Distance Covered", "m"),
    "speed_avg_ms": ("Average Speed", "m/s"),
    "top_speed_ms": ("Top Speed", "m/s"),
    "acceleration_ms2": ("Acceleration", "m/s2"),
    "deceleration_ms2": ("Deceleration", "m/s2"),
    "sprint_count": ("Sprint Count", ""),
    "high_intensity_runs": ("High Intensity Runs", ""),
    "movement_efficiency": ("Movement Efficiency", ""),
    "fatigue_index": ("Fatigue Index", ""),
    "jump_height_cm": ("Jump Height", "cm"),
    "landing_stability": ("Landing Stability", ""),
    "balance": ("Balance", ""),
    "ball_touches": ("Ball Touches", ""),
    "video_duration_s": ("Video Duration", "s"),
    "frames_analyzed": ("Frames Analyzed", ""),
}


def _safe_filename_part(text: str) -> str:
    """Strips characters that aren't safe in a filename, keeps spaces as
    underscores. Falls back to 'player' if nothing usable is left (e.g. the
    name was empty or entirely special characters)."""
    cleaned = "".join(c if (c.isalnum() or c in (" ", "-", "_")) else "" for c in text).strip()
    cleaned = cleaned.replace(" ", "_")
    return cleaned or "player"


def save_result_to_output_pdf(result: Dict[str, Any], player_name: str, sport: str) -> str:
    """Renders an analysis result as a PDF report named after the player and
    writes it into OUTPUT_DIR. Returns the path that was written to."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    safe_name = _safe_filename_part(player_name)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Performance Analysis Report - {player_name}", styles["Title"]))
    story.append(Paragraph(f"Sport: {sport}", styles["Normal"]))
    story.append(Paragraph(f"Capture date: {result.get('capture_date', 'N/A')}", styles["Normal"]))
    story.append(Spacer(1, 0.6 * cm))

    metrics = result.get("metrics", {}) or {}
    table_data = [["Metric", "Value", "Unit"]]
    for key, (label, unit) in METRIC_LABELS.items():
        if key not in metrics:
            continue
        value = metrics[key]
        display_value = "N/A" if value is None else (
            f"{value:.2f}" if isinstance(value, float) else str(value)
        )
        table_data.append([label, display_value, unit])

    metrics_table = Table(table_data, colWidths=[7 * cm, 4 * cm, 3 * cm])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.6 * cm))

    confidence = result.get("confidence_score")
    if confidence is not None:
        story.append(Paragraph(f"Confidence score: {confidence:.2f}", styles["Heading3"]))
        story.append(Spacer(1, 0.3 * cm))

    notes = result.get("video_quality_notes")
    if notes:
        story.append(Paragraph("Video Quality Notes", styles["Heading3"]))
        story.append(Paragraph(notes, styles["Normal"]))

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    doc.build(story)
    return output_path

router = APIRouter()

SUPPORTED_SPORTS = ["Football", "Basketball", "Volleyball", "Handball"]
assert SUPPORTED_SPORTS == CV_SUPPORTED_SPORTS, "main.py and computer_vision.py sport lists drifted apart."


METRIC_TO_SKILL = {
    "top_speed_ms": ["top_speed"],
    "speed_avg_ms": ["acceleration"],
    "acceleration_ms2": ["acceleration"],
    "sprint_count": ["acceleration", "top_speed"],
    "high_intensity_runs": ["fatigue_resistance"],
    "distance_covered_m": ["fatigue_resistance"],
    "fatigue_index": ["fatigue_resistance", "recovery"],
    "movement_efficiency": ["decision_making"],
    "jump_height_cm": ["jump_height"],
    "landing_stability": ["landing_stability"],
    "balance": ["balance"],
    "ball_touches": ["ball_control"],
}
WEAK_BANDS = {"Very Poor", "Poor", "Below Average"}

SYSTEM_PROMPT = """
ROLE

You are a Senior Sports Scientist, Professional Performance Analyst, Strength & Conditioning Coach, Tactical Analyst, AI Engineer, and Elite Academy Coach.

Your job is NOT to simply generate training exercises.

Your job is to analyze the athlete completely, identify the real weaknesses, discover the root causes, generate a personalized development plan, continuously adapt it according to new performance data, and explain every recommendation scientifically.

The system must support FOUR SPORTS ONLY: Football, Basketball, Volleyball, Handball. No other sports.

KNOWLEDGE BASE GROUNDING

The user message includes a "knowledge_base" object built from an internal, curated sports-science reference (benchmark_reference, exercise_shortlist, coaching_principles, disclaimer, instructions_for_model). You MUST:
- Use knowledge_base.benchmark_reference.metric_bands to classify every numeric metric into knowledge_base.benchmark_reference.classification_scale (Very Poor..Elite). Do not invent your own thresholds.
- If knowledge_base.benchmark_reference.is_exact_match is false, explicitly state that the benchmark comparison uses the closest available age group / competition level as an approximation.
- Build training_plan_daily / weekly / monthly primarily from knowledge_base.exercise_shortlist. You may add a closely related exercise not in the shortlist only if none of the shortlisted ones fit the identified weakness, and you must explain why in that exercise's "Why Selected".
- Ground WHY sections, recovery guidance, and injury-prevention reasoning in knowledge_base.coaching_principles where relevant, and note the knowledge_base.disclaimer's caveat about reference data being a baseline, not a certified norm.

OBJECTIVE

Build an AI Performance Development System instead of a normal Training Planner. The AI must behave like a complete performance department inside a professional sports club. It must continuously improve the athlete using video analysis results, performance metrics, personal profile, goals, injuries and progress history. The AI must NEVER generate random workouts. Every recommendation must have a logical explanation.

AI WORKFLOW

Step 1, Validate Data. Check missing values, outliers, low confidence metrics, poor video quality. If confidence is low, mention it. Never hide uncertainty.

Step 2, Build Performance Profile. Create a complete evaluation covering Technical, Physical, Tactical, Mental, Athletic, Recovery, Consistency, Movement, Decision Making, Discipline.

Step 3, Root Cause Analysis. Do not only detect weaknesses, explain why they exist using specific technical and tactical reasoning.

Step 4, Benchmark Comparison. Compare only with athletes having the same sport, same position, same gender, same age group, same competition level. Never compare teenagers with professionals. Classify every metric as Very Poor, Poor, Below Average, Average, Good, Excellent, Elite, using knowledge_base.benchmark_reference as described above.

Step 5, Priority Ranking. Identify Critical Weaknesses, Medium Weaknesses, Minor Weaknesses, Hidden Strengths, Greatest Advantage, Highest Improvement Opportunity.

Step 6, Training Plan Generation. Generate Daily Plan, Weekly Plan, Monthly Plan. Select exercises based on weaknesses, never random drills, primarily from knowledge_base.exercise_shortlist. Every exercise must include Exercise Name, Purpose, Why Selected, Target Skill, Sport, Position, Difficulty, Duration, Sets, Repetitions, Rest Time, Required Equipment, Expected Improvement, Safety Notes.

Step 7, Adaptive Training. If a new video is uploaded, compare with previous performance and evolve the plan automatically, removing drills for improved metrics and increasing focus on metrics that are still weak or have declined.

Step 8, Recovery Planning. Estimate Fatigue, Recovery, Training Load, Rest Days, Recovery Exercises, Mobility, Stretching, Sleep Recommendation, Hydration.

Step 9, Injury Prevention. Estimate injury risk. Identify Overtraining, Muscle Imbalance, Movement Asymmetry, Poor Landing, High Fatigue, High Sprint Load. Generate preventive recommendations. Never diagnose injuries.

Step 10, Player Development Roadmap. Generate 1 Week Goal, 1 Month Goal, 3 Month Goal, 6 Month Goal, 12 Month Goal. Each goal must be measurable.

Step 11, Progress Prediction. Estimate future development based only on available performance trends. Provide Expected Improvement, Expected AI Score Range, Confidence Level, Key Factors Affecting Projection. Do not present predictions as guarantees.

Step 12, Explainability. Every recommendation must include a WHY section grounded in the metrics provided and, where applicable, in knowledge_base.coaching_principles.

Step 13, Coach Summary. Generate a professional report with Current Level, Top Strengths, Top Weaknesses, Immediate Priorities, Long-Term Priorities, Overall Readiness, Training Focus, Recovery Status, Risk Factors.

IMPORTANT RULES

Never invent data. Never fake measurements. Never pretend certainty. Always mention confidence. Always explain reasoning. Always adapt training. Never compare across different sports. Never compare different age groups. Never recommend unsafe training. Never diagnose medical conditions. Use evidence based sports science principles and the provided knowledge_base as the primary reference.

OUTPUT FORMAT

Return a single JSON object only, no prose before or after, no markdown code fences, with exactly these top level keys: player_profile, performance_summary, benchmark_comparison, strengths, weaknesses, root_cause_analysis, training_plan_daily, training_plan_weekly, training_plan_monthly, recovery_plan, injury_prevention, development_roadmap, progress_prediction, coach_summary, athlete_summary.

TONE

Professional, scientific, objective, explainable, evidence based, suitable for use by elite academies and professional sports clubs. Never behave like a chatbot.
"""


class PlayerProfile(BaseModel):
    name: str
    age: int
    gender: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    dominant_hand_or_foot: Optional[str] = None
    sport: str
    position: str
    experience_years: Optional[float] = None
    competition_level: str
    current_club: Optional[str] = None
    playing_time_minutes_per_week: Optional[float] = None
    weekly_training_days: Optional[int] = None
    available_equipment: Optional[List[str]] = None
    previous_injuries: Optional[List[str]] = None
    medical_restrictions: Optional[List[str]] = None


class VideoAnalysisResults(BaseModel):
    metrics: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: Optional[float] = None
    video_quality_notes: Optional[str] = None
    capture_date: Optional[str] = None


class PlayerGoals(BaseModel):
    goals: List[str] = Field(default_factory=list)


class HistoricalData(BaseModel):
    previous_ai_scores: Optional[List[float]] = None
    previous_reports: Optional[List[Dict[str, Any]]] = None
    previous_training_plans: Optional[List[Dict[str, Any]]] = None
    weekly_progress: Optional[List[Dict[str, Any]]] = None
    monthly_progress: Optional[List[Dict[str, Any]]] = None
    training_completion_rate: Optional[float] = None
    performance_trend: Optional[str] = None


class AnalysisRequest(BaseModel):
    player_profile: PlayerProfile
    video_analysis: VideoAnalysisResults
    previous_video_analysis: Optional[VideoAnalysisResults] = None
    goals: PlayerGoals
    historical_data: Optional[HistoricalData] = None


def validate_sport(sport: str):
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported sport '{sport}'. Supported sports are {SUPPORTED_SPORTS}."
        )


def get_groq_client() -> Groq:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY environment variable is not configured."
        )
    return Groq(api_key=GROQ_API_KEY)


def _weak_skill_hints(metrics: Dict[str, Any], bands: Dict[str, Any]) -> List[str]:
    """Look at the raw CV metrics against the resolved benchmark bands and
    return a list of knowledge_base target_skill tags for whatever came back
    Below Average or worse, so the exercise shortlist is actually relevant."""
    hints: List[str] = []
    for metric_name, value in (metrics or {}).items():
        spec = bands.get(metric_name)
        if not spec or value is None:
            continue
        band = kb.classify_metric(value, spec)
        if band in WEAK_BANDS:
            hints.extend(METRIC_TO_SKILL.get(metric_name, []))
    return list(dict.fromkeys(hints))  # de-dupe, keep order


def build_knowledge_base_payload(request: AnalysisRequest) -> Dict[str, Any]:
    """Resolve benchmark bands for this athlete, figure out which skills look
    weak from the raw metrics, and shortlist matching exercises. Pure Python,
    no LLM call — this is what keeps the model's benchmarking and exercise
    picks grounded instead of invented."""
    profile = request.player_profile
    age_group = kb._age_to_group(profile.age)
    bands, resolved_age, resolved_level, exact = kb.get_benchmark_bands(
        profile.sport, age_group, profile.competition_level
    )
    hints = _weak_skill_hints(request.video_analysis.metrics, bands)
    return kb.build_knowledge_context(
        sport=profile.sport,
        age=profile.age,
        competition_level=profile.competition_level,
        weak_skill_hints=hints,
    )


def build_user_payload(request: AnalysisRequest) -> str:
    knowledge_base_payload = build_knowledge_base_payload(request)
    payload = {
        "player_profile": request.player_profile.model_dump(),
        "video_analysis": request.video_analysis.model_dump(),
        "previous_video_analysis": request.previous_video_analysis.model_dump() if request.previous_video_analysis else None,
        "goals": request.goals.model_dump(),
        "historical_data": request.historical_data.model_dump() if request.historical_data else None,
        "knowledge_base": knowledge_base_payload,
    }
    return json.dumps(payload, indent=2)


def call_model(user_payload: str) -> Dict[str, Any]:
    client = get_groq_client()
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.3,
            max_tokens=8000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analyze the following athlete data and return the required JSON object only.\n\n"
                        + user_payload
                    ),
                },
            ],
        )
    except RateLimitError as error:
        raise HTTPException(status_code=429, detail=f"Groq rate limit exceeded: {str(error)}")
    except APIConnectionError as error:
        raise HTTPException(status_code=503, detail=f"Could not connect to Groq: {str(error)}")
    except APIStatusError as error:
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(error)}")
    except APIError as error:
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(error)}")

    if not completion.choices:
        raise HTTPException(status_code=502, detail="Groq returned no choices in the response.")

    raw_text = completion.choices[0].message.content
    if raw_text is None:
        raise HTTPException(status_code=502, detail="Groq returned an empty response.")

    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="Model did not return valid JSON."
        )

    return parsed


def run_full_pipeline(request: AnalysisRequest) -> Dict[str, Any]:
    """Shared tail end for every endpoint: sport validation already done by
    the caller, this just builds the grounded payload and calls the model."""
    user_payload = build_user_payload(request)
    return call_model(user_payload)



def _parse_json_field(raw: Optional[str], field_name: str) -> Optional[Dict[str, Any]]:
    if raw is None or raw.strip() == "":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{field_name}' is not valid JSON: {str(error)}"
        )


async def _save_upload_to_temp(video: UploadFile) -> str:
    if not video.filename:
        raise HTTPException(status_code=400, detail="Uploaded video has no filename.")

    extension = os.path.splitext(video.filename)[1].lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{extension}'. Allowed extensions are {sorted(ALLOWED_VIDEO_EXTENSIONS)}."
        )

    import uuid
    os.makedirs(UPLOAD_TEMP_DIR, exist_ok=True)
    temp_path = os.path.join(UPLOAD_TEMP_DIR, f"cv_upload_{uuid.uuid4().hex}{extension}")

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

    return temp_path


async def _analyze_uploaded_video(
    video: UploadFile,
    sport: str,
    player_name: str,
    position: Optional[str],
    fps: Optional[float],
    pixels_per_meter: Optional[float],
    player_height_cm: Optional[float],
    ball_color: Optional[str],
    max_frames: Optional[int],
) -> Dict[str, Any]:
    """Save an uploaded video, run the real computer-vision analysis from
    computer_vision.py, and return a dict shaped like VideoAnalysisResults.
    This is the step that actually happens 'when a video is uploaded'."""
    validate_sport(sport)
    if ball_color is not None and ball_color not in BALL_COLOR_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown ball_color preset '{ball_color}'. Options are {list(BALL_COLOR_PRESETS.keys())}."
        )

    temp_path = await _save_upload_to_temp(video)
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
        cv_result = await run_in_threadpool(analyze_video, config)
        saved_path = save_result_to_output_pdf(cv_result, player_name, sport)
        print(f"[output] analysis report saved to {saved_path}")
    except VideoAnalysisError as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return cv_result  


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "supported_sports": SUPPORTED_SPORTS,
        "model": GROQ_MODEL,
        "knowledge_base_version": kb.KB_VERSION,
        "ball_color_presets": list(BALL_COLOR_PRESETS.keys()),
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "allowed_video_extensions": sorted(ALLOWED_VIDEO_EXTENSIONS),
    }


@router.post("/analyze")
def analyze_player(request: AnalysisRequest):
    """Analyze an athlete when video metrics have ALREADY been computed
    elsewhere and are being sent directly as JSON."""
    validate_sport(request.player_profile.sport)
    return run_full_pipeline(request)


@router.post("/adaptive-analyze")
def adaptive_analyze(request: AnalysisRequest):
    """Same as /analyze but requires previous_video_analysis so the model
    explicitly compares against the prior session and evolves the plan."""
    validate_sport(request.player_profile.sport)
    if request.previous_video_analysis is None:
        raise HTTPException(
            status_code=400,
            detail="previous_video_analysis is required for adaptive analysis."
        )
    return run_full_pipeline(request)


@router.post("/upload-and-analyze")
async def upload_and_analyze(
    video: UploadFile = File(..., description="The athlete's video file to analyze."),
    player_profile: str = Form(..., description="PlayerProfile as a JSON string."),
    goals: str = Form(..., description="PlayerGoals as a JSON string, e.g. {\"goals\": [\"...\"]}"),
    historical_data: Optional[str] = Form(None, description="HistoricalData as a JSON string, optional."),
    position: Optional[str] = Form(None, description="Overrides player_profile.position for CV calibration if set."),
    fps: Optional[float] = Form(None),
    pixels_per_meter: Optional[float] = Form(None),
    player_height_cm: Optional[float] = Form(None),
    ball_color: Optional[str] = Form(None),
    max_frames: Optional[int] = Form(None),
):
    """
    THE end-to-end endpoint: upload a raw video + athlete info, and get back
    the full AI performance report in one call.

    Flow: validate -> save video -> computer_vision.analyze_video() extracts
    real metrics from the footage -> those metrics + the knowledge base are
    sent to the LLM -> the structured JSON report is returned.
    """
    profile_dict = _parse_json_field(player_profile, "player_profile") or {}
    goals_dict = _parse_json_field(goals, "goals") or {"goals": []}
    historical_dict = _parse_json_field(historical_data, "historical_data")

    try:
        profile = PlayerProfile(**profile_dict)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Invalid player_profile: {str(error)}")

    validate_sport(profile.sport)

    cv_result = await _analyze_uploaded_video(
        video=video,
        sport=profile.sport,
        player_name=profile.name,
        position=position or profile.position,
        fps=fps,
        pixels_per_meter=pixels_per_meter,
        player_height_cm=player_height_cm or profile.height_cm,
        ball_color=ball_color,
        max_frames=max_frames,
    )

    request = AnalysisRequest(
        player_profile=profile,
        video_analysis=VideoAnalysisResults(**cv_result),
        goals=PlayerGoals(**goals_dict),
        historical_data=HistoricalData(**historical_dict) if historical_dict else None,
    )

    ai_report = run_full_pipeline(request)

    return {
        "video_analysis_raw": cv_result,
        "ai_report": ai_report,
    }


@router.post("/upload-and-adaptive-analyze")
async def upload_and_adaptive_analyze(
    video: UploadFile = File(..., description="The athlete's NEW video file to analyze."),
    player_profile: str = Form(..., description="PlayerProfile as a JSON string."),
    goals: str = Form(..., description="PlayerGoals as a JSON string."),
    historical_data: Optional[str] = Form(None, description="HistoricalData as a JSON string, optional."),
    previous_video_analysis: Optional[str] = Form(
        None, description="Previous VideoAnalysisResults as a JSON string (use this OR previous_video, not both)."
    ),
    previous_video: Optional[UploadFile] = File(
        None, description="Previous video file to re-analyze for comparison (use this OR previous_video_analysis)."
    ),
    position: Optional[str] = Form(None),
    fps: Optional[float] = Form(None),
    pixels_per_meter: Optional[float] = Form(None),
    player_height_cm: Optional[float] = Form(None),
    ball_color: Optional[str] = Form(None),
    max_frames: Optional[int] = Form(None),
):
    """
    Same end-to-end flow as /upload-and-analyze, but for a follow-up session:
    requires either a previous video (re-analyzed here) or an already-computed
    previous_video_analysis JSON, so the model can show real progress/decline
    and adapt the plan (Step 7, Adaptive Training).
    """
    profile_dict = _parse_json_field(player_profile, "player_profile") or {}
    goals_dict = _parse_json_field(goals, "goals") or {"goals": []}
    historical_dict = _parse_json_field(historical_data, "historical_data")
    previous_dict = _parse_json_field(previous_video_analysis, "previous_video_analysis")

    if previous_dict is None and previous_video is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either previous_video (a file) or previous_video_analysis (a JSON string)."
        )

    try:
        profile = PlayerProfile(**profile_dict)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Invalid player_profile: {str(error)}")

    validate_sport(profile.sport)

    cv_result = await _analyze_uploaded_video(
        video=video,
        sport=profile.sport,
        player_name=profile.name,
        position=position or profile.position,
        fps=fps,
        pixels_per_meter=pixels_per_meter,
        player_height_cm=player_height_cm or profile.height_cm,
        ball_color=ball_color,
        max_frames=max_frames,
    )

    if previous_dict is None:
        previous_dict = await _analyze_uploaded_video(
            video=previous_video,
            sport=profile.sport,
            player_name=profile.name,
            position=position or profile.position,
            fps=fps,
            pixels_per_meter=pixels_per_meter,
            player_height_cm=player_height_cm or profile.height_cm,
            ball_color=ball_color,
            max_frames=max_frames,
        )

    request = AnalysisRequest(
        player_profile=profile,
        video_analysis=VideoAnalysisResults(**cv_result),
        previous_video_analysis=VideoAnalysisResults(**previous_dict),
        goals=PlayerGoals(**goals_dict),
        historical_data=HistoricalData(**historical_dict) if historical_dict else None,
    )

    ai_report = run_full_pipeline(request)

    return {
        "video_analysis_raw": cv_result,
        "previous_video_analysis_raw": previous_dict,
        "ai_report": ai_report,
    }
