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

Run migrations and restart your Alliance Auth server:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Then restart your `allianceserver`/`gunicorn`/`supervisor` processes as usual.

#