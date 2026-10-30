from django import template

from accounts.models import User
from incidents.models import Authority, Category, Incident

register = template.Library()

IMAGE_PREFIX = "image/"
VIDEO_TYPES = frozenset({"video/mp4", "video/webm"})


@register.filter
def is_image_file(attachment) -> bool:
    ct = getattr(attachment, "content_type", "") or ""
    return ct.startswith(IMAGE_PREFIX)


@register.filter
def is_video_file(attachment) -> bool:
    ct = getattr(attachment, "content_type", "") or ""
    return ct in VIDEO_TYPES or ct.startswith("video/")


@register.filter
def previewable_attachment(attachment) -> bool:
    return is_image_file(attachment) or is_video_file(attachment)


CHANGE_LABELS = {
    "status": "Status",
    "category_id": "Category",
    "authority_id": "Authority",
    "assignee_id": "Responsible",
    "priority": "Priority",
    "title": "Title",
    "description": "Description",
    "location": "Location",
    "case_type": "Type",
}


@register.filter
def change_field_label(field_name: str) -> str:
    return CHANGE_LABELS.get(field_name, field_name.replace("_", " ").title())


@register.filter
def change_value_display(value, field_name=""):
    if value is None or value == "":
        return "—"
    field_name = str(field_name or "")
    if field_name == "authority_id":
        authority = Authority.objects.filter(pk=value).first()
        return str(authority) if authority else "—"
    if field_name == "assignee_id":
        user = User.objects.filter(pk=value).first()
        return user.get_display_name() if user else "—"
    if field_name == "category_id":
        category = Category.objects.filter(pk=value).first()
        return str(category) if category else "—"
    if field_name == "status":
        return dict(Incident.Status.choices).get(value, str(value).replace("_", " ").title())
    if field_name == "priority":
        return dict(Incident.Priority.choices).get(value, str(value).replace("_", " ").title())
    if field_name == "case_type":
        return dict(Incident.CaseType.choices).get(value, str(value).replace("_", " ").title())
    text = str(value)
    if text.replace("_", "").isalnum() and "_" in text:
        return text.replace("_", " ").title()
    return text


@register.filter
def case_list_label(case) -> str:
    title = (getattr(case, "title", None) or getattr(case, "description", None) or "").strip()
    return title or "Untitled case"


@register.filter
def user_unit_role(user, authority) -> str:
    if not user or not authority:
        return ""
    authority_id = authority.pk if hasattr(authority, "pk") else authority
    role = user.roles.filter(authority_id=authority_id).order_by("name").first()
    return role.name if role else ""

