"""App Views"""

import json
import uuid

from zkbchecker import check_control

from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone

from celery.result import AsyncResult

from pathlib import Path

from zkbchecker.tasks import check_characters_task
from zkbchecker.excel_export import build_workbook

from zkbchecker.forms import ExcludedShipForm, SuspiciousEntityForm
from zkbchecker.models import ExcludedShip, SuspiciousEntity

from django.contrib import messages
from django.urls import reverse

@login_required
@permission_required("zkbchecker.basic_access")
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view: shows the input form and an empty results area.
    Results are loaded asynchronously via JavaScript after the check
    completes in the background (see start_check / check_status).
    """
    return render(request, "zkbchecker/index.html", {})


@login_required
@permission_required("zkbchecker.basic_access")
@require_POST
def start_check(request: WSGIRequest) -> JsonResponse:
    """Start a background check for the submitted character names and
    return the Celery task ID so the client can poll for the result."""
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    names = payload.get("names", [])
    names = [n.strip() for n in names if isinstance(n, str) and n.strip()]

    if not names:
        return JsonResponse({"error": "No character names provided"}, status=400)

    # Our own task id, registered *before* the task starts, so the task
    # never sees a missing heartbeat on its very first check.
    task_id = str(uuid.uuid4())
    check_control.register(request.user.pk, task_id)
    check_characters_task.apply_async(args=[names, request.user.pk], task_id=task_id)

    return JsonResponse({"task_id": task_id})


@login_required
@permission_required("zkbchecker.basic_access")
def check_status(request: WSGIRequest, task_id: str) -> JsonResponse:
    """Return the state of a background check plus the result rows the
    client hasn't seen yet. The client passes `?since=N`, the number of
    rows it already has, and gets rows[N:] back with `next` to use as
    `since` in the following request. Every poll doubles as a heartbeat
    that tells the task somebody is still watching."""
    try:
        since = max(int(request.GET.get("since", 0)), 0)
    except ValueError:
        since = 0

    async_result = AsyncResult(task_id)
    state = async_result.state

    if state in ("PENDING", "PROGRESS"):
        check_control.touch(task_id)

    response = {"state": state, "rows": [], "next": since}

    if state in ("PROGRESS", "CANCELLED"):
        info = async_result.info or {}
        results = info.get("results", [])
        response["current"] = info.get("current", 0)
        response["total"] = info.get("total", 0)
        response["rows"] = results[since:]
        response["next"] = max(since, len(results))
    elif state == "SUCCESS":
        results = async_result.result or []
        response["current"] = len(results)
        response["total"] = len(results)
        response["rows"] = results[since:]
        response["next"] = max(since, len(results))
    elif state == "FAILURE":
        response["error"] = str(async_result.info)

    return JsonResponse(response)

@login_required
@permission_required("zkbchecker.basic_access")
@require_POST
def export_excel(request: WSGIRequest) -> HttpResponse:
    """Build and return an Excel file from the results submitted by
    the client (the same results already shown in the DataTable)."""
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    results = payload.get("results", [])
    if not results:
        return JsonResponse({"error": "No results provided"}, status=400)

    buffer = build_workbook(results)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    filename = f"zkb_check_{timezone.now().strftime('%Y-%m-%d_%H-%M')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@login_required
@permission_required("zkbchecker.manage_config")
def ship_list(request: WSGIRequest) -> JsonResponse:
    """Serve the locally cached list of ship types for the
    ExcludedShip admin autocomplete field."""
    path = Path(__file__).resolve().parent / "ship_list.json"
    if not path.exists():
        return JsonResponse({"ships": []})

    with open(path, "r", encoding="utf-8") as f:
        ships = json.load(f)

    return JsonResponse({"ships": ships})

def _settings_redirect(tab: str) -> HttpResponse:
    """Redirect back to the settings page, keeping the active tab."""
    return redirect(f"{reverse('zkbchecker:settings')}?tab={tab}")


def _flash_form_errors(request: WSGIRequest, form) -> None:
    """Show form validation errors as messages at the top of the page."""
    for errors in form.errors.values():
        for error in errors:
            messages.error(request, error)


@login_required
@permission_required("zkbchecker.manage_config")
def config_settings(request: WSGIRequest) -> HttpResponse:
    """Plugin settings page: manage suspicious entities and excluded
    ships. Both add-forms post to this same view, told apart by the
    hidden 'form_type' field."""
    active_tab = "ships" if request.GET.get("tab") == "ships" else "entities"
    entity_form = SuspiciousEntityForm()
    ship_form = ExcludedShipForm()

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "entity":
            active_tab = "entities"
            entity_form = SuspiciousEntityForm(request.POST)
            if entity_form.is_valid():
                entity = entity_form.save()
                messages.success(request, f"Added suspicious entity: {entity.label}")
                return _settings_redirect("entities")
            _flash_form_errors(request, entity_form)

        elif form_type == "ship":
            active_tab = "ships"
            ship_form = ExcludedShipForm(request.POST)
            if ship_form.is_valid():
                ship = ship_form.save()
                messages.success(request, f"Added excluded item: {ship.name}")
                return _settings_redirect("ships")
            _flash_form_errors(request, ship_form)

    context = {
        "active_tab": active_tab,
        "entities": SuspiciousEntity.objects.all(),
        "ships": ExcludedShip.objects.all(),
        "entity_form": entity_form,
        "ship_form": ship_form,
    }
    return render(request, "zkbchecker/settings.html", context)


@login_required
@permission_required("zkbchecker.manage_config")
@require_POST
def delete_suspicious_entity(request: WSGIRequest, pk: int) -> HttpResponse:
    entity = get_object_or_404(SuspiciousEntity, pk=pk)
    label = entity.label
    entity.delete()
    messages.success(request, f"Removed suspicious entity: {label}")
    return _settings_redirect("entities")


@login_required
@permission_required("zkbchecker.manage_config")
@require_POST
def delete_excluded_ship(request: WSGIRequest, pk: int) -> HttpResponse:
    ship = get_object_or_404(ExcludedShip, pk=pk)
    name = ship.name
    ship.delete()
    messages.success(request, f"Removed excluded item: {name}")
    return _settings_redirect("ships")

@login_required
@permission_required("zkbchecker.basic_access")
@require_POST
def cancel_check(request: WSGIRequest) -> HttpResponse:
    """Called by the browser (sendBeacon) when the page is being left
    or reloaded: cancel the user's running check."""
    check_control.cancel_active(request.user.pk)
    return HttpResponse(status=204)