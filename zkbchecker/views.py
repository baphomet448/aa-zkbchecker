"""App Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render

from zkbchecker.esi_client import resolve_names
from zkbchecker.zkb_client import get_stats, get_losses, get_kills
from zkbchecker.triggers import evaluate_triggers


@login_required
@permission_required("zkbchecker.basic_access")
def index(request: WSGIRequest) -> HttpResponse:
    """
    Index view: shows the input form, and (for a single character
    submitted) the result inline on the same page.
    """
    result = None

    if request.method == "POST":
        names_raw = request.POST.get("names", "")
        names = [n.strip() for n in names_raw.splitlines() if n.strip()]

        if len(names) == 1:
            result = _check_single_character(names[0])

    context = {"result": result}

    return render(request, "zkbchecker/index.html", context)


def _check_single_character(name: str) -> dict:
    """Run the full check for a single character name and return
    a dict ready for template rendering."""
    resolved = resolve_names([name])
    if not resolved:
        return {"name": name, "found": False}

    character_id = resolved[0]["id"]
    stats = get_stats(character_id)
    losses = get_losses(character_id)
    kills = get_kills(character_id)

    triggers = evaluate_triggers(stats, losses["all_ships"], kills["victim_ships"])

    return {
        "name": stats["name"],
        "found": True,
        "corporation_id": stats["corporation_id"],
        "alliance_id": stats["alliance_id"],
        "birthday": stats["birthday"],
        "kills_total": stats["kills_total"],
        "losses_total": stats["losses_total"],
        "last_kill_date": kills["last_kill_date"],
        "last_loss_date": losses["last_loss_date"],
        "triggers": triggers,
        "suspicious_alliance": kills["suspicious_alliance"],
    }