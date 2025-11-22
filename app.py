"""
Diagnosaurus.ai - Main Flask Application
Multi-agent medical symptom analysis system
"""
import asyncio
import uuid
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from loguru import logger
import sys

from config import settings
from models.schemas import (
    SymptomAnalysisRequest,
    AnalysisResponse,
    SessionStatus,
    AgentStatus,
    Location,
)
from services.redis_service import RedisService
from services.skyflow_service import skyflow_service
from services.parallel_service import get_research_service
from services.geoip_service import geoip_service
from services.document_service import document_service
from agents.research_agent import CoarseSearchAgent, DeepResearchAgent
from agents.forum_coordinator import AdversarialForum
from agents.condition_analyzer import condition_analyzer

# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.log_level)
logger.add(settings.log_file, rotation="500 MB", level=settings.log_level)

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload
CORS(app)

# Initialize services
redis_service = RedisService()
research_service = get_research_service()  # Selects Parallel.ai or fallback based on config

# Store active analysis sessions
active_sessions = {}


@app.route("/")
def index():
    """Serve main UI"""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    redis_healthy = redis_service.health_check()

    return jsonify({
        "status": "healthy" if redis_healthy else "degraded",
        "redis": redis_healthy,
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/api/analyze", methods=["POST"])
def analyze_symptoms():
    """
    Main symptom analysis endpoint
    Initiates multi-agent analysis pipeline
    """
    try:
        data = request.get_json()

        # Validate request
        analysis_request = SymptomAnalysisRequest(**data)

        # Generate session ID
        session_id = f"session_{uuid.uuid4().hex[:16]}"

        # Get user location
        if not analysis_request.location:
            location_data = geoip_service.get_location_from_request(request)
            analysis_request.location = Location(
                latitude=location_data.get("latitude", 0.0),
                longitude=location_data.get("longitude", 0.0),
                city=location_data.get("city"),
                country=location_data.get("country"),
                ip_address=request.remote_addr,
            )

        # Initialize session
        session_data = {
            "session_id": session_id,
            "request": analysis_request.model_dump(),
            "status": "initializing",
            "created_at": datetime.utcnow().isoformat(),
        }
        redis_service.set_session_data(session_id, session_data)

        # Start analysis in background thread
        def run_async_pipeline():
            asyncio.run(run_analysis_pipeline(session_id, analysis_request))

        thread = threading.Thread(target=run_async_pipeline, daemon=True)
        thread.start()

        logger.info(f"Started analysis session: {session_id}")

        return jsonify({
            "session_id": session_id,
            "status": "processing",
            "message": "Analysis started. Poll /api/status/{session_id} for updates.",
        }), 202

    except Exception as e:
        logger.error(f"Analysis request failed: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/status/<session_id>", methods=["GET"])
def get_analysis_status(session_id: str):
    """Poll analysis status"""
    try:
        session_data = redis_service.get_session_data(session_id)

        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        # Get current status
        status = session_data.get("status", "unknown")
        result = session_data.get("result")
        error = session_data.get("error")
        progress = session_data.get("progress", 0)

        response = {
            "session_id": session_id,
            "status": status,
            "progress": progress,
            "result": result,
            "error": error,
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"error": str(e)}), 500


async def run_analysis_pipeline(session_id: str, request: SymptomAnalysisRequest):
    """
    Main analysis pipeline
    Orchestrates all agents and services
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"[{session_id}] Starting analysis pipeline")

        # Update status
        update_session_status(session_id, "sanitizing", 10)

        # Step 1: Extract text from uploaded documents
        document_text = ""
        if request.documents:
            logger.info(f"[{session_id}] Extracting text from {len(request.documents)} documents")
            document_text = document_service.extract_text_from_documents(request.documents)

        # Step 2: Merge symptoms + document text
        combined_text = request.symptoms
        if document_text:
            combined_text += f"\n\n--- Medical Documents ---\n{document_text}"
            logger.info(f"[{session_id}] Combined text length: {len(combined_text)} chars")

        # Step 3: Sanitize PII/PHI in combined text
        sanitized_text = skyflow_service.sanitize_text(combined_text)
        logger.info(f"[{session_id}] Text sanitized (Skyflow: {skyflow_service.client is not None})")

        # Step 4: Coarse search - identify potential conditions
        update_session_status(session_id, "researching", 20)

        coarse_agent = CoarseSearchAgent(parallel_service=research_service)
        coarse_result = await coarse_agent.execute({
            "symptoms": sanitized_text,
            "patient_context": {
                "age": request.patient_age,
                "sex": request.patient_sex,
            },
        })

        potential_conditions = coarse_result["conditions"]
        logger.info(f"[{session_id}] Identified {len(potential_conditions)} potential conditions")

        # Step 5: Deep research on each condition (batched)
        update_session_status(session_id, "deep_research", 40)

        research_results = await run_deep_research_batch(
            session_id,
            potential_conditions,
            sanitized_text,
            request,
        )

        # Step 6: Adversarial forum debate
        update_session_status(session_id, "debating", 70)

        forum = AdversarialForum()
        forum_result = await forum.execute({
            "research_results": research_results,
            "symptoms": sanitized_text,
            "patient_context": {
                "age": request.patient_age,
                "sex": request.patient_sex,
            },
        })

        # Step 7: Final condition analysis and scoring
        update_session_status(session_id, "analyzing", 85)

        final_conditions = condition_analyzer.analyze(
            research_results,
            forum_result["adjusted_confidences"],
            sanitized_text,
        )

        # Step 8: Find nearby clinics
        update_session_status(session_id, "finding_clinics", 90)

        clinics = await research_service.find_clinics(
            location={
                "lat": request.location.latitude,
                "lon": request.location.longitude,
            },
            min_rating=settings.min_clinic_rating,
        )

        # Step 9: Build final response
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        analysis_response = AnalysisResponse(
            session_id=session_id,
            conditions=final_conditions,
            clinics=clinics,
            agent_research=research_results,
            forum_debate=forum_result["debate_result"],
            processing_time_ms=processing_time,
            warning_message=_generate_warning_message(sanitized_text, final_conditions),
        )

        # Store result
        update_session_status(
            session_id,
            "completed",
            100,
            result=analysis_response.dict(),
        )

        logger.info(f"[{session_id}] Analysis complete in {processing_time}ms")

    except Exception as e:
        logger.error(f"[{session_id}] Analysis pipeline failed: {e}")
        update_session_status(session_id, "failed", 0, error=str(e))


async def run_deep_research_batch(
    session_id: str,
    conditions: list,
    symptoms: str,
    request: SymptomAnalysisRequest,
):
    """Run deep research agents in batches"""
    results = []
    batch_size = settings.agents_batch

    for i in range(0, len(conditions), batch_size):
        batch = conditions[i:i + batch_size]
        logger.info(f"[{session_id}] Processing batch {i//batch_size + 1}: {batch}")

        # Run batch in parallel
        tasks = []
        for condition in batch:
            agent = DeepResearchAgent(parallel_service=research_service)
            task = agent.execute({
                "condition": condition,
                "symptoms": symptoms,
                "patient_context": {
                    "age": request.patient_age,
                    "sex": request.patient_sex,
                },
            })
            tasks.append(task)

        batch_results = await asyncio.gather(*tasks)

        for result in batch_results:
            results.append(result["research_result"])

        # Update progress
        progress = 40 + int((i / len(conditions)) * 30)
        update_session_status(session_id, "deep_research", progress)

    return results


def update_session_status(
    session_id: str,
    status: str,
    progress: int,
    result=None,
    error=None,
):
    """Update session status in Redis"""
    session_data = redis_service.get_session_data(session_id) or {}
    session_data.update({
        "status": status,
        "progress": progress,
        "updated_at": datetime.utcnow().isoformat(),
    })

    if result:
        session_data["result"] = result
    if error:
        session_data["error"] = error

    redis_service.set_session_data(session_id, session_data)
    logger.debug(f"[{session_id}] Status: {status} ({progress}%)")


def _generate_warning_message(symptoms: str, conditions: list) -> str:
    """Generate warning message if symptoms are too general"""
    if len(symptoms) < 50:
        return "Your symptom description is quite brief. More detailed information may improve accuracy."

    if not conditions:
        return "Unable to identify specific conditions. Please provide more detailed symptoms or consult a healthcare provider."

    avg_confidence = sum(c.confidence for c in conditions) / len(conditions)
    if avg_confidence < 0.5:
        return "Results have lower confidence due to general symptoms. These are possibilities, not diagnoses. Please consult a healthcare provider."

    return None


if __name__ == "__main__":
    logger.info(f"Starting Diagnosaurus.ai on port {settings.port}")
    logger.info(f"Debug mode: {settings.flask_debug}")
    logger.info(f"Agent batch size: {settings.agents_batch} (TODO: increase to 5 before demo)")

    app.run(
        host="0.0.0.0",
        port=settings.port,
        debug=settings.flask_debug,
    )
