import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _alertable_roles():
    from rbac.models import Role

    return list(
        Role.objects.filter(is_end_user_role=False)
        .order_by("name")
        .values("id", "name", "description")
    )


def suggest_roles_for_incident(description: str) -> tuple[list[str], dict | None]:
    """
    Return role names to alert using Gemini. Falls back to [] on error.
    """
    roles = _alertable_roles()
    if not roles:
        return [], {"reason": "no_alertable_roles"}

    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set; skipping AI routing.")
        return [], {"reason": "missing_api_key"}

    role_catalog = [
        {
            "name": r["name"],
            "description": r["description"] or "",
        }
        for r in roles
    ]
    allowed_names = {r["name"] for r in role_catalog}

    prompt = f"""You route university incident reports to the correct staff teams at FMSC, USJ.

Given the incident description and the list of STAFF roles (never include end-user/Member roles),
respond with JSON only, matching this schema:
{{"role_names": ["Exact Role Name", ...]}}

Rules:
- Pick only roles from the provided catalog (use exact name strings).
- Choose the minimum set of roles that should act on this incident.
- If unclear, prefer operational/security/support roles over academic ones.
- Do not invent role names.

Staff role catalog:
{json.dumps(role_catalog, ensure_ascii=False)}

Incident description:
{description}
"""

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        )
        raw = (response.text or "").strip()
        payload = json.loads(raw)
        names = payload.get("role_names") or payload.get("roles") or []
        if not isinstance(names, list):
            names = []
        cleaned = []
        for name in names:
            if not isinstance(name, str):
                continue
            name = name.strip()
            if name in allowed_names and name not in cleaned:
                cleaned.append(name)
        return cleaned, {"raw": payload, "model": model_name}
    except Exception as exc:
        logger.exception("Gemini routing failed: %s", exc)
        return [], {"error": str(exc)}


def route_incident(incident) -> int:
    """Run AI routing and create in-app notifications. Returns notification count."""
    from accounts.models import User
    from rbac.models import Role

    from incidents.models import Notification

    names, meta = suggest_roles_for_incident(incident.description)
    incident.ai_role_selection = meta

    if not names:
        incident.status = incident.Status.ROUTING_FAILED
        incident.save(update_fields=["ai_role_selection", "status", "updated_at"])
        return 0

    roles = Role.objects.filter(name__in=names, is_end_user_role=False)
    incident.alerted_roles.set(roles)
    incident.status = incident.Status.ROUTED
    incident.save(update_fields=["ai_role_selection", "status", "updated_at"])

    snippet = incident.description[:120]
    if len(incident.description) > 120:
        snippet += "…"

    count = 0
    for role in roles:
        recipients = User.objects.filter(is_active=True, roles=role).distinct()
        for user in recipients:
            Notification.objects.create(
                user=user,
                incident=incident,
                message=(
                    f"New incident (#{incident.pk}) routed to {role.name}: {snippet}"
                ),
            )
            count += 1
    return count
