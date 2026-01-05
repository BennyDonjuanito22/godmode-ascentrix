"""FastAPI application that fronts the shared TaskManager."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr

from api import accounting
from api.approvals import router as approvals_router
from api.blitz_api import router as blitz_router
from api.email_api import router as email_router
from api.funnels import load_b1_funnel_config, render_b1_landing
from api.funnels_api import router as funnels_router
from api.hud_api import (
    hud_agents,
    hud_autopilot_status,
    hud_channel_summary,
    hud_home,
    hud_logs,
    hud_master_checklist,
    hud_autopilot_metrics,
    hud_autopilot_trend,
    hud_business_chat,
    hud_append_business_chat,
    hud_business_queue,
    hud_portfolio_states,
    hud_work_queue,
    hud_settings,
    hud_streams,
    hud_llm_usage,
)
from api.human_help_api import router as human_router
from api.leads import add_lead, list_leads
from api.ledger import LedgerEntry, append_entry, iter_entries, summarize
from api.landing_pages_api import router as landing_pages_router
from api.mode_api import router as mode_router
from api.notifications_api import router as notifications_router
from api.offers_api import router as offers_router
from api.metrics_api import router as metrics_router
from api.vector_memory import build_index, search_index
from api.task_runtime import TaskManager
from api.password_api import router as vault_router
from godmode.accounts import registry as account_registry
from godmode.business import landing_pages
from godmode.phone_bridge.server import router as phone_bridge_router
from godmode.config import get_settings
from godmode.core.logging import configure_logging, get_logger
from godmode.status import build_status

settings = get_settings()
configure_logging(service_name="api", level=settings.log_level, environment=settings.environment)
LOGGER = get_logger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
TASK_HISTORY_DIR = settings.data_dir / "task_history"
TASK_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_PATH = TASK_HISTORY_DIR / "api_app_history.jsonl"


def _process_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder worker logic until real jobs are wired up."""
    time.sleep(2)
    return {"status": "processed", "payload": task_data}


MANAGER = TaskManager(history_path=HISTORY_PATH, processor=_process_task, name="api-app-worker")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    LOGGER.info("API starting; history=%s", HISTORY_PATH)
    MANAGER.start()
    try:
        yield
    finally:
        LOGGER.info("API shutting down")
        MANAGER.shutdown()


app = FastAPI(title="God Mode API", debug=settings.debug, lifespan=_lifespan)
app.include_router(phone_bridge_router)
app.include_router(approvals_router)
app.include_router(mode_router)
app.include_router(blitz_router)
app.include_router(vault_router)
app.include_router(email_router)
app.include_router(human_router)
app.include_router(notifications_router)
app.include_router(metrics_router)
app.include_router(offers_router)
app.include_router(funnels_router)
app.include_router(landing_pages_router)
app.state.settings = settings


@app.post("/task")
def enqueue_task(task: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    job_id = MANAGER.enqueue(task)
    return {"job_id": job_id, "status": "queued"}


@app.get("/result/{job_id}")
def get_result(job_id: int) -> Dict[str, Any]:
    record = MANAGER.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="job_id not found")
    return {
        "job_id": job_id,
        "status": record["status"],
        "result": record.get("result"),
        "error": record.get("error"),
    }


@app.get("/tasks")
def list_tasks() -> Dict[str, Any]:
    return {"results": MANAGER.snapshot()}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "uptime": MANAGER.uptime}


@app.get("/")
def root() -> Dict[str, Any]:
    return {"service": "godmode-api", "status": "running"}


@app.get("/funnels/b1")
def funnel_b1_config() -> Dict[str, Any]:
    """
    Return the current configuration for the B1 (Affiliate/Digital product) funnel.
    """
    config = load_b1_funnel_config()
    return {"funnel": config.to_dict()}


@app.get("/funnels/b1/landing", response_class=HTMLResponse)
def funnel_b1_landing() -> HTMLResponse:
    """
    Render a simple landing page that can be shared or embedded.
    """
    config = load_b1_funnel_config()
    html = render_b1_landing(config)
    return HTMLResponse(content=html)


class LeadCapturePayload(BaseModel):
    email: EmailStr
    source: str | None = "landing"
    tag: str | None = None


class BusinessChatPayload(BaseModel):
    role: str
    text: str


@app.post("/funnels/b1/lead")
def funnel_b1_capture(payload: LeadCapturePayload) -> Dict[str, Any]:
    metadata = {"tag": payload.tag} if payload.tag else None
    entry = add_lead(email=payload.email, source=payload.source or "landing", metadata=metadata)
    return {"ok": True, "lead": entry.to_dict()}


@app.get("/funnels/b1/lead")
def funnel_b1_leads(limit: int = 50) -> Dict[str, Any]:
    leads = list_leads()
    return {"leads": [lead.to_dict() for lead in leads[-limit:]]}


@app.get("/finance/ledger")
def ledger_list(limit: int = 50) -> Dict[str, Any]:
    entries = list(iter_entries(limit=limit))
    return {"entries": [entry.__dict__ for entry in entries]}


@app.post("/finance/ledger")
def ledger_append(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["amount", "currency", "source", "funnel", "notes"]
    for key in required:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {key}")
    entry = LedgerEntry(
        timestamp=time.time(),
        amount=float(payload["amount"]),
        currency=str(payload["currency"]),
        source=str(payload["source"]),
        funnel=str(payload["funnel"]),
        notes=str(payload["notes"]),
        purpose=str(payload.get("purpose", "")),
        business_id=payload.get("business_id"),
        offer_id=payload.get("offer_id"),
    )
    append_entry(entry)
    return {"ok": True}


@app.get("/finance/summary")
def ledger_summary() -> Dict[str, Any]:
    entries = iter_entries()
    data = summarize(entries)
    return data


class BusinessPayload(BaseModel):
    name: str
    slug: str
    kind: str | None = "digital"
    status: str | None = None
    cta_url: str | None = None
    instant_payout: bool | None = None
    tags: List[str] | None = None
    metadata: Dict[str, Any] | None = None


@app.get("/accounting/businesses")
def accounting_businesses() -> Dict[str, Any]:
    businesses: List[Dict[str, Any]] = []
    for record in accounting.list_businesses():
        snapshot = accounting.business_snapshot(record)
        business_id = snapshot.get("id") or record.id
        email_accounts = account_registry.get_accounts_for_business(business_id, account_type="email")
        snapshot["email_account"] = email_accounts[0].to_dict() if email_accounts else None
        snapshot["landing_pages"] = [page.to_dict() for page in landing_pages.list_pages_for_business(business_id)]
        businesses.append(snapshot)
    return {"businesses": businesses}


@app.post("/accounting/businesses")
def accounting_upsert_business(payload: BusinessPayload) -> Dict[str, Any]:
    record = accounting.upsert_business(
        name=payload.name,
        slug=payload.slug,
        kind=payload.kind or "digital",
        status=payload.status or "planning",
        cta_url=payload.cta_url,
        instant_payout=bool(payload.instant_payout),
        tags=payload.tags or [],
        metadata=payload.metadata or {},
    )
    return {"business": accounting.business_snapshot(record)}


@app.get("/crm/customers")
def crm_customers() -> Dict[str, Any]:
    customers = [record.to_dict() for record in accounting.list_customers()]
    return {"customers": customers}


@app.get("/accounting/customers/summary")
def accounting_customer_summary(business_id: str | None = None) -> Dict[str, Any]:
    profiles = [profile.to_dict() for profile in accounting.list_customer_profiles(business_id=business_id)]
    return {"customers": profiles, "count": len(profiles)}


@app.post("/accounting/customers/rebuild")
def accounting_customer_rebuild() -> Dict[str, Any]:
    profiles = accounting.rebuild_customer_profiles()
    return {"ok": True, "count": len(profiles)}


class EventPayload(BaseModel):
    business_slug: str
    event_type: str
    amount: float | None = None
    currency: str | None = None
    offer_id: str | None = None
    cart_id: str | None = None
    anonymous_id: str | None = None
    customer_email: EmailStr | None = None
    customer_name: str | None = None
    opportunity_id: str | None = None
    consent: bool | None = None
    variant: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    referrer: str | None = None
    device: str | None = None
    metadata: Dict[str, Any] | None = None


@app.post("/events/track")
def events_track(payload: EventPayload) -> Dict[str, Any]:
    business = accounting.get_business_by_slug(payload.business_slug)
    if not business:
        business = accounting.upsert_business(name=payload.business_slug.title(), slug=payload.business_slug)
    customer_id: Optional[str] = None
    if payload.customer_email:
        customer = accounting.upsert_customer(payload.customer_email, full_name=payload.customer_name)
        customer_id = customer.id
    event_metadata = payload.metadata or {}
    if payload.customer_email:
        event_metadata = dict(event_metadata)
        event_metadata.setdefault("email", payload.customer_email)
    event = accounting.track_event(
        business_id=business.id,
        event_type=payload.event_type,
        offer_id=payload.offer_id,
        customer_id=customer_id,
        anonymous_id=payload.anonymous_id,
        amount=payload.amount,
        currency=payload.currency,
        cart_id=payload.cart_id,
        metadata=event_metadata,
        opportunity_id=payload.opportunity_id,
        consent=payload.consent,
        variant=payload.variant,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_content=payload.utm_content,
        utm_term=payload.utm_term,
        referrer=payload.referrer,
        device=payload.device,
    )
    if payload.event_type == "purchase" and payload.amount:
        accounting.add_transaction(
            business_id=business.id,
            amount=payload.amount,
            currency=payload.currency or "USD",
            status="paid",
            customer_id=customer_id,
            metadata=payload.metadata or {},
            opportunity_id=payload.opportunity_id,
        )
    signals = accounting.buyer_signals(business_id=business.id)
    return {"event": event.to_dict(), "signals": signals}


@app.get("/events/recent")
def events_recent(limit: int = 25) -> Dict[str, Any]:
    events = accounting.list_events()
    events.sort(key=lambda record: record.occurred_at, reverse=True)
    return {"events": [event.to_dict() for event in events[:limit]]}


@app.post("/memory/ingest")
def memory_ingest() -> Dict[str, Any]:
    stats = build_index()
    return {"ok": True, **stats}


@app.get("/memory/search")
def memory_search(query: str, limit: int = 5) -> Dict[str, Any]:
    results = search_index(query=query, limit=limit)
    return {"results": results}


@app.get("/hud/home")
def hud_home_endpoint() -> Dict[str, Any]:
    return hud_home()


@app.get("/hud/streams")
def hud_streams_endpoint() -> Dict[str, Any]:
    return hud_streams()


@app.get("/hud/agents")
def hud_agents_endpoint() -> Dict[str, Any]:
    return hud_agents()


@app.get("/hud/logs")
def hud_logs_endpoint() -> Dict[str, Any]:
    return hud_logs()


@app.get("/hud/settings")
def hud_settings_endpoint() -> Dict[str, Any]:
    return hud_settings()


@app.get("/hud/llm")
def hud_llm_endpoint() -> Dict[str, Any]:
    return hud_llm_usage()


@app.get("/hud/autopilot/status")
def hud_autopilot_status_endpoint() -> Dict[str, Any]:
    return hud_autopilot_status()


@app.get("/hud/channel_summary")
def hud_channel_summary_endpoint() -> Dict[str, Any]:
    return hud_channel_summary()


@app.get("/hud/master_checklist")
def hud_master_checklist_endpoint() -> Dict[str, Any]:
    return hud_master_checklist()


@app.get("/hud/work_queue")
def hud_work_queue_endpoint() -> Dict[str, Any]:
    return hud_work_queue()


@app.get("/hud/portfolio")
def hud_portfolio_endpoint() -> Dict[str, Any]:
    return hud_portfolio_states()


@app.get("/hud/businesses/{business_id}/queue")
def hud_business_queue_endpoint(business_id: str, limit: int = 12) -> Dict[str, Any]:
    return hud_business_queue(business_id, limit=limit)


@app.get("/hud/businesses/{business_id}/chat")
def hud_business_chat_endpoint(business_id: str, limit: int = 200) -> Dict[str, Any]:
    return hud_business_chat(business_id, limit=limit)


@app.post("/hud/businesses/{business_id}/chat")
def hud_business_chat_post_endpoint(business_id: str, payload: BusinessChatPayload) -> Dict[str, Any]:
    return hud_append_business_chat(business_id, role=payload.role, text=payload.text)


@app.get("/hud/autopilot/metrics")
def hud_autopilot_metrics_endpoint() -> Dict[str, Any]:
    return hud_autopilot_metrics()


@app.get("/hud/autopilot/trend")
def hud_autopilot_trend_endpoint(days: int = 7) -> Dict[str, Any]:
    return hud_autopilot_trend(days=days)


@app.get("/status")
def status_dashboard() -> Dict[str, Any]:
    return build_status()


@app.get("/docs/system_blueprint_checklist.pdf")
def system_blueprint_pdf() -> FileResponse:
    path = settings.repo_root / "docs" / "system_blueprint_checklist.pdf"
    return FileResponse(path)
