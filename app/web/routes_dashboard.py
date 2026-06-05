"""HTML dashboard routes (Jinja2 + HTMX)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import SuggestionStatus
from app.services import suggestions as svc
from app.web.deps import templates

router = APIRouter()


def _parse_hashtags(raw: str) -> list[str]:
    tokens = raw.replace(",", " ").split()
    return [t.lstrip("#") for t in tokens if t.strip()]


@router.get("/", response_class=HTMLResponse)
def queue(request: Request, status: str = "suggested", db: Session = Depends(get_db)):
    try:
        status_enum = SuggestionStatus(status)
    except ValueError:
        status_enum = SuggestionStatus.SUGGESTED
    items = svc.list_suggestions(db, status_enum)
    return templates.TemplateResponse(
        request,
        "queue.html",
        {
            "suggestions": items,
            "current_status": status_enum.value,
            "statuses": [s.value for s in SuggestionStatus],
            "counts": svc.status_counts(db),
        },
    )


@router.get("/suggestions/{suggestion_id}", response_class=HTMLResponse)
def detail(suggestion_id: int, request: Request, db: Session = Depends(get_db)):
    suggestion = svc.get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return templates.TemplateResponse(request, "detail.html", {"s": suggestion})


def _card(request: Request, suggestion) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "_suggestion_card.html", {"s": suggestion}
    )


@router.post("/suggestions/{suggestion_id}/edit", response_class=HTMLResponse)
def edit_caption(
    suggestion_id: int,
    request: Request,
    caption: str = Form(...),
    hashtags: str = Form(""),
    db: Session = Depends(get_db),
):
    suggestion = svc.get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404)
    svc.update_caption(db, suggestion, caption, _parse_hashtags(hashtags))
    return _card(request, suggestion)


@router.post("/suggestions/{suggestion_id}/image", response_class=HTMLResponse)
def swap_image(
    suggestion_id: int,
    request: Request,
    image_id: int = Form(...),
    db: Session = Depends(get_db),
):
    suggestion = svc.get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404)
    svc.select_image(db, suggestion, image_id)
    return templates.TemplateResponse(
        request, "_image_picker.html", {"s": suggestion}
    )


@router.post("/suggestions/{suggestion_id}/approve", response_class=HTMLResponse)
def approve(suggestion_id: int, request: Request, db: Session = Depends(get_db)):
    suggestion = svc.get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404)
    svc.approve(db, suggestion)
    return _card(request, suggestion)


@router.post("/suggestions/{suggestion_id}/reject", response_class=HTMLResponse)
def reject(suggestion_id: int, request: Request, db: Session = Depends(get_db)):
    suggestion = svc.get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404)
    svc.reject(db, suggestion)
    return _card(request, suggestion)


@router.post("/suggestions/{suggestion_id}/publish", response_class=HTMLResponse)
def publish(suggestion_id: int, request: Request, db: Session = Depends(get_db)):
    suggestion = svc.get_suggestion(db, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404)
    svc.publish(db, suggestion)
    return _card(request, suggestion)
