# Changelog

## [0.2.0] - 2026-10-12

### Added

- **Settings tab** next to the **Checker** tab for users with the
  `zkbchecker.manage_config` permission: manage Suspicious Entities and
  Excluded Ships inside Alliance Auth (add above the table, search,
  sort, delete). The Django admin stays available as a fallback.
- Results now **appear in the table while the check is running**; a
  progress bar and spinners show that work is in progress. Export Excel
  becomes available when the check finishes.
- A running check is **stopped automatically** when the user reloads or
  leaves the page, so the Celery worker is not kept busy for nobody.
  One active check per user: starting a new one cancels the previous.
- **English and Russian localization** (interface, messages, Excel
  headers, table controls).
- Deployables (mobile depots, tractor units, warp disruptors, etc.) are
  now searchable in the excluded-ship autocomplete.

### Changed

- Excluded ships and suspicious entities are read from the database once
  per batch instead of once per character.
- Characters whose zKillboard check failed are shown as "Check failed"
  in the table instead of breaking it.
- Dates in the results table are shortened to the day; the Excel export
  keeps the full timestamps.

### Fixed

- Timeouts on large batches: zKillboard requests are paced, retried on
  timeouts and use a longer timeout.
- Characters without any killboard activity now show their name.

## [0.1.0] - 2026-09-28

- Initial release: character checks via zKillboard and ESI, suspicion
  triggers, batch checks with Celery, Excel export, configurable
  suspicious entities and excluded ships.