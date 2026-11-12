"""Additional endpoints for the agency upgrade; all endpoints require Django session auth."""
import json
import logging
import os
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from . import ai as agency_ai
from .models import Department, ExternalNews, User
from .permissions import active_users
from .views import api, body, err, j

log = logging.getLogger("core")


def _filename(name, ext):
    clean = "".join(ch for ch in str(name or "document") if ch.isalnum() or ch in "-_ ").strip()[:80] or "document"
    return f"{clean}.{ext}"


@api()
@require_GET
def public_departments(request):
    return j({"departments": [{"id": d.key, "name": d.name} for d in Department.objects.all()]})


@api()
@require_GET
def mention_users(request):
    q = (request.GET.get("q") or "").strip().lstrip("@")[:100].replace("_", " ")
    qs = active_users().select_related("department").order_by("name")
    if q:
        qs = qs.filter(name__icontains=q)
    rows = qs[:500]
    return j({"users": [{"id": u.pk, "name": u.name, "role": u.role, "dept": u.department.key if u.department_id else ""} for u in rows]})


@api(post=True)
def ai_ask(request):
    if not settings.ANTHROPIC_API_KEY:
        return err("ai_not_configured", 503)
    data = body(request)
    question = (data.get("question") or "").strip()
    try:
        days = int(data.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    days = max(1, min(days, 3650))
    if not question or len(question) > 4000:
        return err("invalid_question")
    try:
        result = agency_ai.answer(request.user, question, days)
    except Exception as exc:  # return an honest error; never fall back to fake local output
        log.exception("AI request failed")
        return err("ai_unavailable", 502, detail=str(exc)[:400])
    return j(result)


@api()
@require_GET
def external_news_list(request):
    country = (request.GET.get("country") or "all").lower()
    category = (request.GET.get("category") or "all").lower()
    q = (request.GET.get("q") or "").strip()[:160]
    qs = ExternalNews.objects.all()
    if country in {"afghanistan", "world", "pakistan", "iran", "usa"}:
        qs = qs.filter(country=country)
    if category in {"urgent", "political", "security", "economy", "technology", "society", "education", "health", "sports", "other"}:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(summary__icontains=q)
    try:
        limit = max(1, min(int(request.GET.get("limit", 100)), 250))
    except ValueError:
        limit = 100
    rows = [{"id": n.pk, "title": n.title, "summary": n.summary, "url": n.url, "source": n.source,
             "country": n.country, "category": n.category,
             "published_at": n.published_at.isoformat() if n.published_at else "",
             "ts": int((n.published_at or n.fetched_at).timestamp() * 1000)} for n in qs[:limit]]
    return j({"items": rows, "count": len(rows)})


@api(post=True)
def office_export_xlsx(request):
    from .office import xlsx_bytes
    data = body(request)
    try:
        raw = xlsx_bytes(data)
    except Exception as exc:  # noqa: BLE001
        log.exception("XLSX export failed")
        return err("xlsx_export_failed", 400, detail=str(exc)[:300])
    name = _filename(data.get("filename"), "xlsx")
    response = HttpResponse(raw, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename*=UTF-8''" + quote(name)
    return response


@api(post=True)
def office_export_docx(request):
    from .office import docx_bytes
    data = body(request)
    try:
        raw = docx_bytes(data.get("html", ""), rtl=bool(data.get("rtl", True)), title=data.get("filename", ""))
    except Exception as exc:  # noqa: BLE001
        log.exception("DOCX export failed")
        return err("docx_export_failed", 400, detail=str(exc)[:300])
    name = _filename(data.get("filename"), "docx")
    response = HttpResponse(raw, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    response["Content-Disposition"] = "attachment; filename*=UTF-8''" + quote(name)
    return response


@api(post=True)
def office_import(request):
    f = request.FILES.get("file")
    if not f:
        return err("file_required")
    if f.size > 25 * 1024 * 1024:
        return err("file_too_big", 413)
    from .office import xlsx_import, docx_import
    name = os.path.basename(f.name).lower()
    try:
        if name.endswith(".xlsx"):
            result = {"kind": "xlsx", "data": xlsx_import(f)}
        elif name.endswith(".docx"):
            result = {"kind": "docx", "html": docx_import(f)}
        else:
            return err("unsupported_file", 415)
    except Exception as exc:  # noqa: BLE001
        log.exception("Office import failed")
        return err("office_import_failed", 400, detail=str(exc)[:300])
    return j(result)
