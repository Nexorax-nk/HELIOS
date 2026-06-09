"""
HELIOS Orchestrator — Multi-Agent Pipeline
Coordinates the 6-agent evaluation pipeline with:
- Async parallel execution (Agents 2, 3, 4 run concurrently after Agent 1)
- SSE event streaming for real-time dashboard updates
- Full pipeline result assembly
"""
from __future__ import annotations
import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Callable, Optional

from agents.models import (
    EvaluationRequest, PipelineResult,
    SentinelReport, ChronicleReport, MeridianReport,
    ContextReport, OracleReport, ArbiterVerdict
)
from agents import sentinel, chronicle, meridian, context, oracle, arbiter

logger = logging.getLogger(__name__)

# SSE event broadcaster — callers register a callback to receive events
StreamCallback = Callable[[str, dict], None]


async def run_pipeline(
    request: EvaluationRequest,
    stream_callback: Optional[StreamCallback] = None,
) -> PipelineResult:
    """
    Execute the full HELIOS 6-agent pipeline.

    Execution order:
      SENTINEL → (CHRONICLE ∥ MERIDIAN ∥ CONTEXT) → ORACLE → ARBITER

    Args:
        request: The evaluation request
        stream_callback: Optional callback for real-time streaming events.
                         Called as callback(event_name, data_dict)

    Returns:
        Complete PipelineResult with all agent outputs and final verdict
    """
    eval_id = request.eval_id or str(uuid.uuid4())[:8]
    request.eval_id = eval_id
    start_time = time.time()

    result = PipelineResult(eval_id=eval_id, request=request)

    def emit(event: str, data: dict):
        """Send a streaming event to the dashboard."""
        if stream_callback:
            try:
                stream_callback(event, {"eval_id": eval_id, **data})
            except Exception as e:
                logger.warning(f"Stream callback error: {e}")

    logger.info(f"[{eval_id}] HELIOS pipeline starting: {request.config_file} ({request.environment})")
    emit("pipeline_start", {
        "config_file": request.config_file,
        "environment": request.environment,
        "message": f"HELIOS evaluation started for {request.config_file}"
    })

    try:
        # ─── LAYER 1: SENTINEL ─────────────────────────────────────────────
        emit("agent_start", {"agent": "SENTINEL", "layer": 1,
                              "message": "Analyzing semantic meaning of the config change..."})
        logger.info(f"[{eval_id}] Layer 1: SENTINEL starting")

        sentinel_report = await sentinel.run(request)
        result.sentinel = sentinel_report

        emit("agent_complete", {
            "agent": "SENTINEL",
            "layer": 1,
            "result": {
                "parameter": sentinel_report.parameter,
                "config_type": sentinel_report.config_type,
                "behavior_change": sentinel_report.behavior_change,
                "semantic_severity": sentinel_report.semantic_severity,
            },
            "message": f"SENTINEL: {sentinel_report.parameter} is a {sentinel_report.config_type} change — {sentinel_report.behavior_change[:100]}..."
        })

        # ─── LAYER 2: CHRONICLE ∥ MERIDIAN ∥ CONTEXT (parallel) ───────────
        logger.info(f"[{eval_id}] Layer 2: CHRONICLE + MERIDIAN + CONTEXT (parallel)")
        emit("layer_start", {"layer": 2, "message": "Layer 2: Querying knowledge base, graph, and org signals in parallel..."})

        emit("agent_start", {"agent": "CHRONICLE", "layer": 2,
                              "message": "Querying Foundry IQ knowledge base for historical evidence..."})
        emit("agent_start", {"agent": "MERIDIAN", "layer": 2,
                              "message": "Traversing Fabric IQ graph for blast radius..."})
        emit("agent_start", {"agent": "CONTEXT", "layer": 2,
                              "message": "Reading Work IQ organizational signals..."})

        # Rate limit handling: Gemini Free tier limit is 5 requests per minute
        chronicle_report = await chronicle.run(sentinel_report)
        await asyncio.sleep(15)
        meridian_report = await meridian.run(sentinel_report)
        await asyncio.sleep(15)
        context_report = await context.run(request, sentinel_report)
        await asyncio.sleep(15)

        result.chronicle = chronicle_report
        result.meridian = meridian_report
        result.context = context_report

        emit("agent_complete", {
            "agent": "CHRONICLE",
            "layer": 2,
            "result": {
                "historical_risk_signal": chronicle_report.historical_risk_signal,
                "similar_incidents_found": chronicle_report.similar_incidents_found,
                "vendor_advisories_found": chronicle_report.vendor_advisories_found,
                "key_finding": chronicle_report.key_finding,
            },
            "message": f"CHRONICLE: {chronicle_report.historical_risk_signal} historical risk — {chronicle_report.similar_incidents_found} incidents, {chronicle_report.vendor_advisories_found} advisories"
        })

        emit("agent_complete", {
            "agent": "MERIDIAN",
            "layer": 2,
            "result": {
                "blast_radius_score": meridian_report.blast_radius_score,
                "affected_endpoints_total": meridian_report.affected_endpoints_total,
                "business_functions_at_risk": meridian_report.business_functions_at_risk,
                "revenue_at_risk_per_hour": meridian_report.revenue_at_risk_per_hour,
            },
            "message": f"MERIDIAN: {meridian_report.blast_radius_score} blast radius — {meridian_report.affected_endpoints_total:,} endpoints, ${meridian_report.revenue_at_risk_per_hour:,.0f}/hr at risk"
        })

        emit("agent_complete", {
            "agent": "CONTEXT",
            "layer": 2,
            "result": {
                "deployment_window_risk": context_report.deployment_window_risk,
                "context_risk_score": context_report.context_risk_score,
                "recovery_capability": context_report.recovery_capability,
                "primary_expert_available": context_report.primary_expert_available,
            },
            "message": f"CONTEXT: {context_report.deployment_window_risk} deployment window (score: {context_report.context_risk_score}/100), recovery: {context_report.recovery_capability}"
        })

        # ─── LAYER 3: ORACLE ───────────────────────────────────────────────
        logger.info(f"[{eval_id}] Layer 3: ORACLE (cross-domain consequence prediction)")
        emit("agent_start", {"agent": "ORACLE", "layer": 3,
                              "message": "Predicting real-world organizational consequences across all dimensions..."})

        oracle_report = await oracle.run(
            sentinel_report, chronicle_report, meridian_report, context_report
        )
        result.oracle = oracle_report

        emit("agent_complete", {
            "agent": "ORACLE",
            "layer": 3,
            "result": {
                "scenario_title": oracle_report.scenario_title,
                "estimated_revenue_impact": oracle_report.estimated_revenue_impact,
                "recovery_time_estimate": oracle_report.recovery_time_estimate,
                "confidence": oracle_report.confidence,
                "key_prediction": oracle_report.key_prediction,
            },
            "message": f"ORACLE: {oracle_report.key_prediction}"
        })

        # ─── LAYER 4: ARBITER ──────────────────────────────────────────────
        logger.info(f"[{eval_id}] Layer 4: ARBITER (final verdict)")
        emit("agent_start", {"agent": "ARBITER", "layer": 4,
                              "message": "Synthesizing all evidence — issuing final verdict..."})

        arbiter_verdict = await arbiter.run(
            request, sentinel_report, chronicle_report,
            meridian_report, context_report, oracle_report
        )
        result.arbiter = arbiter_verdict

        execution_time = time.time() - start_time
        result.execution_time_seconds = round(execution_time, 2)

        emit("agent_complete", {
            "agent": "ARBITER",
            "layer": 4,
            "result": {
                "verdict": arbiter_verdict.verdict,
                "verdict_emoji": arbiter_verdict.verdict_emoji,
                "risk_score": arbiter_verdict.risk_score,
                "confidence": arbiter_verdict.confidence,
            },
            "message": f"ARBITER: {arbiter_verdict.verdict_emoji} {arbiter_verdict.verdict} (risk={arbiter_verdict.risk_score}/100)"
        })

        emit("pipeline_complete", {
            "verdict": arbiter_verdict.verdict,
            "verdict_emoji": arbiter_verdict.verdict_emoji,
            "risk_score": arbiter_verdict.risk_score,
            "execution_time_seconds": execution_time,
            "message": f"Pipeline complete in {execution_time:.1f}s — Verdict: {arbiter_verdict.verdict_emoji} {arbiter_verdict.verdict}"
        })

        logger.info(
            f"[{eval_id}] Pipeline complete in {execution_time:.1f}s — "
            f"{arbiter_verdict.verdict_emoji} {arbiter_verdict.verdict} "
            f"(risk={arbiter_verdict.risk_score})"
        )

    except Exception as e:
        result.error = str(e)
        logger.exception(f"[{eval_id}] Pipeline error: {e}")
        emit("pipeline_error", {"error": str(e), "message": f"Pipeline error: {e}"})

    return result
