# ZKB Checker for Alliance Auth

A security-oriented plugin for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth)
that helps alliance/corp security officers identify potential spy characters
("eyes and ears") by analyzing their killboard history on
[zKillboard](https://zkillboard.com).

Given a list of character names, the plugin fetches their killboard stats and
flags characters matching known suspicious patterns, such as:

- Long-standing characters with almost no combat activity
- Characters frequently seen killing shuttles/rookie ships (new-player hunters)
- Characters flying recon, covert ops, or black ops ships
- Characters that appear alongside known hostile alliances/corporations on
  their kills

Results for a single character are shown directly on the page. For batches of
multiple characters, results are compiled into a downloadable Excel report.

> [!NOTE]
> This project is under active development. Some features described above
> may not be fully implemented yet.

______________________________________________________________________

## Requirements

- Alliance Auth v5+

## Permissions

- `zkbchecker.basic_access` — allows using the character checker
  (the main page).
- `zkbchecker.manage_config` — allows managing Suspicious Entities
  and Excluded Ships in the admin (see Configuration above).

Assign these to the appropriate Alliance Auth groups (e.g. give
`basic_access` broadly to security officers, and `manage_config`
only to a smaller, trusted group) via **Groups → your group →
Permissions** in the Alliance Auth admin.

## Configuration

The plugin's detection logic relies on two admin-managed lists, found
under **Admin → ZKBCHECKER**:

### Suspicious Entities

Alliances or corporations considered hostile/suspicious. When a
checked character's final blow on a recent kill was made by someone
from one of these entities, the result is flagged with a "Suspicious
alliance link".

To add one, paste a zKillboard alliance or corporation URL (e.g.
`https://zkillboard.com/alliance/99012042/`) — the entity type and ID
are parsed from it automatically — and give it a short label to
display in results.

Requires the `zkbchecker.manage_config` permission.

### Excluded Ships

Ship types ignored when calculating loss statistics (capsules,
mobile depots, mobile warp disruptors, etc.). Without this, a
character's "top ships lost" list would be dominated by these
disposable items instead of showing what they actually fly in
combat.

Start typing a ship name in the admin form; matching suggestions are
pulled from a local, ESI-sourced list (see `update_ship_list` below)
and selecting one fills in the ship type ID automatically.

Requires the `zkbchecker.manage_config` permission.

## Known Issue: aiopenapi3 Compatibility

If your Alliance Auth's `django-esi` version predates its fix for
`aiopenapi3` 0.11.0+ breaking changes, you may see an error like
`ValueError: invalid return value annotation for session_factory`
when using EVE SSO login (unrelated to this plugin directly, but it
can surface after installing new dependencies). If you hit this,
pin `aiopenapi3` below 0.11.0:

```bash
pip install "aiopenapi3<0.11.0"
```

This is a known upstream issue, tracked by the Alliance Auth
community; check your `django-esi` version for a permanent fix.

## Installation

Install the package into your Alliance Auth virtual environment:

```bash
pip install git+https://github.com/baphomet448/aa-zkbchecker.git
```

Add `zkbchecker` to `INSTALLED_APPS` in your `local.py`:

```python
INSTALLED_APPS += [
    'zkbchecker',
]
```

This plugin uses Celery to process batch character checks in the
background. Your Alliance Auth instance already runs Celery, but the
result backend needs to be explicitly configured so task results can
be retrieved. Add this to your `local.py` if not already set:

```python
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
```

(adjust the Redis URL if your setup differs from the default)

Run migrations and restart your Alliance Auth server:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

The excluded-ship autocomplete field needs a local, one-time snapshot
of current EVE ship types. Fetch it with:

```bash
python manage.py update_ship_list
```

Re-run this command occasionally (e.g. after a game expansion adds
new ships) to keep the autocomplete list up to date.

Then restart your `allianceserver`/`gunicorn`/`supervisor` processes as usual.

#