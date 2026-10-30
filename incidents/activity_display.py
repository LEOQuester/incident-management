"""Which case history rows belong on the detail feed (below the main post card)."""

from incidents.models import CaseUpdate


def is_submission_echo(update: CaseUpdate) -> bool:
    """Initial status=submitted log duplicates the post header and status chips."""
    if update.comment.strip() or update.internal:
        return False
    changes = update.changes or {}
    if len(changes) != 1:
        return False
    status = changes.get("status")
    if not isinstance(status, dict):
        return False
    return status.get("old") in (None, "") and status.get("new") == "submitted"


def activity_feed_updates(updates):
    return [update for update in updates if not is_submission_echo(update)]
