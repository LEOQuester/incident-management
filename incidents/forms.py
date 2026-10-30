from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from incidents.models import Incident, Authority, Category
from accounts.models import User


class ReportIncidentForm(forms.ModelForm):
    is_urgent = forms.BooleanField(
        required=False,
        label="Mark as urgent",
    )

    class Meta:
        model = Incident
        fields = ("title", "case_type", "priority", "category", "location", "description")
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control incident-description",
                    "rows": 6,
            "placeholder": "What happened? Include location and time. For large videos, paste a Google Drive share link here.",
                    "maxlength": settings.INCIDENT_DESCRIPTION_MAX_LENGTH,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["case_type"].widget = forms.HiddenInput()
        self.fields["priority"].required = False
        self.fields["priority"].widget = forms.HiddenInput()
        for name in ("title", "category", "location"):
            self.fields[name].required = True
        for field in self.fields.values():
            if isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput)):
                continue
            field.widget.attrs.setdefault("class", "form-control")
        if self.instance.pk and self.instance.priority == Incident.Priority.URGENT:
            self.fields["is_urgent"].initial = True

    def clean_description(self):
        text = (self.cleaned_data.get("description") or "").strip()
        if len(text) < 10:
            raise ValidationError("Please provide at least 10 characters.")
        max_len = settings.INCIDENT_DESCRIPTION_MAX_LENGTH
        if len(text) > max_len:
            raise ValidationError(f"Description cannot exceed {max_len} characters.")
        return text

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_urgent"):
            cleaned["priority"] = Incident.Priority.URGENT
        else:
            cleaned["priority"] = cleaned.get("priority") or Incident.Priority.NORMAL
        return cleaned


def validate_incident_photos(files):
    max_count = settings.INCIDENT_MAX_PHOTOS
    max_bytes = settings.INCIDENT_PHOTO_MAX_BYTES
    allowed = settings.INCIDENT_ALLOWED_IMAGE_TYPES

    if len(files) > max_count:
        raise ValidationError(f"You can upload at most {max_count} images.")

    for uploaded in files:
        content_type = getattr(uploaded, "content_type", "") or ""
        if content_type not in allowed:
            raise ValidationError(
                f"Unsupported image type: {content_type or uploaded.name}."
            )
        if uploaded.size > max_bytes:
            limit = max_bytes // (1024 * 1024)
            raise ValidationError(
                f"Each image must be {limit} MB or smaller. "
                "Use a Google Drive link in the description for larger files."
            )


class CaseUpdateForm(forms.ModelForm):
    COMMENT_TYPE_NORMAL = "normal"
    COMMENT_TYPE_INTERNAL = "internal"
    COMMENT_TYPE_RESOLUTION = "resolution"
    COMMENT_TYPE_CHOICES = (
        (COMMENT_TYPE_NORMAL, "Normal"),
        (COMMENT_TYPE_INTERNAL, "Internal"),
        (COMMENT_TYPE_RESOLUTION, "Resolution"),
    )

    comment = forms.CharField(
        widget=forms.Textarea,
        required=False,
        max_length=5000,
        label="Comment",
    )
    comment_type = forms.ChoiceField(
        choices=COMMENT_TYPE_CHOICES,
        initial=COMMENT_TYPE_NORMAL,
        required=False,
        label="Type",
    )

    class Meta:
        model = Incident
        fields = (
            "category",
            "priority",
            "authority",
            "assignee",
            "status",
        )

    def __init__(self, *args, manager=False, can_transfer=False, can_update=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.can_transfer = can_transfer
        self.can_update = can_update
        self.fields["authority"].queryset = Authority.objects.filter(is_active=True)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["assignee"].required = False
        self.fields["assignee"].label = "Responsible person"
        self.fields["assignee"].empty_label = "None selected"
        self.fields["authority"].required = False

        allowed = {
            "under_review",
            "not_started",
            "assigned",
            "in_progress",
            "waiting",
            "solved",
            "closed",
            "rejected",
            "reopened",
        }
        if not manager:
            if can_update:
                allowed = {"in_progress", "waiting", "solved"}
            else:
                allowed = set()
            for field in ("category", "priority"):
                self.fields.pop(field, None)
            if not can_update:
                self.fields.pop("status", None)
            if not can_transfer:
                for field in ("authority", "assignee"):
                    self.fields.pop(field, None)
        if manager or can_transfer:
            auth_id = self.instance.authority_id
            staff = User.objects.filter(is_active=True, roles__authority__isnull=False)
            if auth_id:
                staff = staff.filter(roles__authority_id=auth_id)
            self.fields["assignee"].queryset = staff.distinct().order_by("username")
            if can_transfer and not manager:
                self.fields["authority"].label = "Transfer to authority"
                self.fields["authority"].help_text = (
                    "Choose another authority. Optionally pick a responsible person below."
                )
        if "status" in self.fields:
            self.fields["status"].choices = [
                (k, v) for k, v in Incident.Status.choices if k in allowed
            ]
            self.fields["status"].required = False
        compact = "form-control form-control-compact"
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
                continue
            field.widget.attrs.setdefault("class", compact)
        if "comment" in self.fields:
            self.fields["comment"].widget.attrs.update(
                {"rows": 2, "placeholder": "Progress note, resolution summary, or staff-only note"}
            )
        if "comment_type" in self.fields:
            self.fields["comment_type"].widget.attrs.setdefault(
                "class", "form-control form-control-compact case-update-comment-type"
            )
            can_resolve = "status" in self.fields and "solved" in {
                choice[0] for choice in self.fields["status"].choices
            }
            if not can_resolve:
                self.fields["comment_type"].choices = [
                    choice
                    for choice in self.COMMENT_TYPE_CHOICES
                    if choice[0] != self.COMMENT_TYPE_RESOLUTION
                ]

    def clean_comment_type(self):
        value = self.cleaned_data.get("comment_type")
        if not value:
            return self.COMMENT_TYPE_NORMAL
        return value

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if status:
            return status
        if "status" in self.fields:
            return self.instance.status
        return self.instance.status

    def clean(self):
        cleaned = super().clean()
        comment_type = cleaned.get("comment_type") or self.COMMENT_TYPE_NORMAL
        comment = (cleaned.get("comment") or "").strip()
        cleaned["internal"] = comment_type == self.COMMENT_TYPE_INTERNAL

        if comment_type == self.COMMENT_TYPE_RESOLUTION:
            if not comment:
                self.add_error(
                    "comment",
                    "Describe what was done to resolve this case.",
                )
            else:
                cleaned["resolution_note"] = comment
                if "status" in self.fields:
                    cleaned["status"] = "solved"

        new_status = cleaned.get("status", self.instance.status)
        old_status = self.instance.status
        has_resolution_note = bool(
            (cleaned.get("resolution_note") or self.instance.resolution_note or "").strip()
        )
        if (
            new_status == "solved"
            and not has_resolution_note
            and comment_type != self.COMMENT_TYPE_RESOLUTION
            and new_status != old_status
        ):
            self.add_error(
                "comment_type",
                "Choose Resolution and enter what was done, or mark solved via Resolution.",
            )
        authority = (
            cleaned.get("authority")
            if self.manager or self.can_transfer
            else self.instance.authority
        )
        if not authority and self.instance.authority_id:
            authority = self.instance.authority
        if self.manager or self.can_transfer:
            cleaned["authority"] = authority
        assignee = cleaned.get("assignee")
        if authority and assignee and not assignee.roles.filter(authority=authority).exists():
            self.add_error(
                "assignee",
                "This person must have a role for the selected authority.",
            )
        if new_status in {"assigned", "in_progress", "waiting", "solved"} and not authority:
            self.add_error(None, "Assign an authority before starting or solving a case.")
        if new_status == "closed" and self.instance.status != "solved":
            self.add_error("status", "Only solved cases can be closed.")
        if new_status == "reopened" and self.instance.status not in {"solved", "closed", "rejected"}:
            self.add_error("status", "Only solved, closed, or rejected cases can be reopened.")
        if self.instance.status in {"closed", "rejected", "solved"} and new_status not in {
            "reopened",
            "closed",
        }:
            self.add_error("status", "Reopen this case before making further progress.")
        if new_status in {"rejected", "reopened"} and not comment:
            self.add_error("comment", "Explain why the case is rejected or reopened.")
        if not self.manager and self.can_transfer and not self.can_update:
            if (
                cleaned.get("authority") == self.instance.authority
                and cleaned.get("assignee") == self.instance.assignee
                and not (cleaned.get("comment") or "").strip()
            ):
                self.add_error(None, "Choose a new authority, assignee, or add a comment.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        comment_type = self.cleaned_data.get("comment_type") or self.COMMENT_TYPE_NORMAL
        if comment_type == self.COMMENT_TYPE_RESOLUTION:
            instance.resolution_note = (self.cleaned_data.get("comment") or "").strip()
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class AuthorityForm(forms.ModelForm):
    class Meta:
        model = Authority
        fields = ("name", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


def validate_evidence(files):
    """Validate file contents as well as extension; never trust browser MIME headers."""
    from pathlib import Path
    from PIL import Image, UnidentifiedImageError
    if len(files) > 5:
        raise ValidationError("Upload at most five evidence files at a time.")
    for uploaded in files:
        suffix = Path(uploaded.name).suffix.lower()
        head = uploaded.read(32)
        uploaded.seek(0)
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            if uploaded.size > 5 * 1024 * 1024:
                raise ValidationError("Images must not exceed 5 MiB.")
            try:
                image = Image.open(uploaded)
                image.verify()
                uploaded.content_type = Image.MIME.get(image.format, "image/jpeg")
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
                raise ValidationError("Upload a valid image.") from exc
            finally:
                uploaded.seek(0)
        elif suffix in {".mp4", ".webm"}:
            if uploaded.size > settings.INCIDENT_VIDEO_MAX_BYTES:
                limit = settings.INCIDENT_VIDEO_MAX_BYTES // (1024 * 1024)
                raise ValidationError(
                    f"Each video must be {limit} MB or smaller. "
                    "Upload larger videos to Google Drive and paste the share link in the description."
                )
            if suffix == ".mp4" and (len(head) < 12 or head[4:8] != b"ftyp"):
                raise ValidationError("Upload a valid MP4 video.")
            if suffix == ".webm" and not head.startswith(b"\x1a\x45\xdf\xa3"):
                raise ValidationError("Upload a valid WebM video.")
            validate_video(uploaded, suffix)
            uploaded.content_type = "video/mp4" if suffix == ".mp4" else "video/webm"
        else:
            raise ValidationError("Allowed evidence: JPEG, PNG, WebP, GIF, MP4, and WebM.")


def validate_video(uploaded, suffix):
    import json
    import math
    import subprocess
    import tempfile
    from pathlib import Path
    # Probe a private temporary file, without invoking a shell or allowing network protocols.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / f"evidence{suffix}"
        try:
            with path.open("wb") as target:
                for chunk in uploaded.chunks():
                    target.write(chunk)
            result = subprocess.run([
                settings.FFPROBE_PATH, "-v", "error", "-protocol_whitelist", "file",
                "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(path),
            ], capture_output=True, text=True, timeout=15, check=True)
            metadata = json.loads(result.stdout)
            duration = float(metadata["format"]["duration"])
            if not any(stream.get("codec_type") == "video" for stream in metadata.get("streams", [])):
                raise ValueError("Missing video stream")
            if not math.isfinite(duration) or duration <= 0 or duration > settings.INCIDENT_VIDEO_MAX_SECONDS:
                raise ValidationError(f"Video duration must be between 0 and {settings.INCIDENT_VIDEO_MAX_SECONDS} seconds.")
        except FileNotFoundError as exc:
            raise ValidationError("Video validation is unavailable. Contact the administrator or upload images instead.") from exc
        except (subprocess.SubprocessError, ValueError, KeyError, OSError) as exc:
            raise ValidationError("The video could not be validated. Upload a valid MP4 or WebM file.") from exc
        finally:
            uploaded.seek(0)
