"""App Views"""

import json

from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.utils import timezone

from celery.result import AsyncResult

from zkbchecker.tasks import check_characters_task

from zkbchecker.excel_export import build_workbook


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

    async_result = check_characters_task.delay(names)

    return JsonResponse({"task_id": async_result.id})


@login_required
@permission_required("zkbchecker.basic_access")
def check_status(request: WSGIRequest, task_id: str) -> JsonResponse:
    """Return the current status of a background check task, and its
    result once it has finished."""
    async_result = AsyncResult(task_id)

    response = {"state": async_result.state}

    if async_result.state == "PROGRESS":
        response["meta"] = async_result.info
    elif async_result.state == "SUCCESS":
        response["result"] = async_result.result
    elif async_result.state == "FAILURE":
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