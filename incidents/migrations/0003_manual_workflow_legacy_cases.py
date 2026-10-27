from django.db import migrations


def migrate_legacy_cases(apps, schema_editor):
    Incident = apps.get_model("incidents", "Incident")
    CaseUpdate = apps.get_model("incidents", "CaseUpdate")
    alias = schema_editor.connection.alias
    for case in Incident.objects.using(alias).all().iterator():
        changes = {}
        if not case.title:
            case.title = case.description[:100] or f"Legacy incident {case.pk}"
        if case.status in {"routed", "routing_failed"}:
            changes["status"] = {"old": case.status, "new": "submitted"}
            case.status = "submitted"
        case.save(using=alias, update_fields=["title", "status"])
        CaseUpdate.objects.using(alias).create(incident_id=case.pk, internal=True,
            comment="Existing case retained for manual review. Original AI routing metadata is preserved.", changes=changes)


class Migration(migrations.Migration):
    dependencies = [("incidents", "0002_category_incident_case_type_incident_closed_at_and_more")]
    operations = [migrations.RunPython(migrate_legacy_cases, migrations.RunPython.noop)]
