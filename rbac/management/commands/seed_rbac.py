from django.core.management.base import BaseCommand

from rbac.features import APP_FEATURES, sync_permissions_to_database
from rbac.models import Permission, Role
from rbac.seed_catalog import DEFAULT_CATEGORIES, SEED_AUTHORITIES
from rbac.seed_ops import (
    delete_retired_roles,
    ensure_bootstrap_superuser,
    purge_non_seed_authorities,
    sync_authorities_and_unit_roles,
    sync_global_roles,
)

LEGACY_PERMISSION_CODENAMES = ("manage_catalogs", "update_cases")

UNIT_CASE_PERMISSIONS = (
    "view_allocated_cases",
    "update_allocated_cases",
    "transfer_case",
)


def migrate_legacy_permissions() -> None:
    """Move roles off retired codenames before deleting unused Permission rows."""
    unit_perms = list(Permission.objects.filter(codename__in=UNIT_CASE_PERMISSIONS))
    legacy_update = Permission.objects.filter(codename="update_cases").first()
    if legacy_update and unit_perms:
        for role in Role.objects.filter(permissions=legacy_update).distinct():
            role.permissions.add(*unit_perms)
            role.permissions.remove(legacy_update)

    split_catalog = list(
        Permission.objects.filter(codename__in=("manage_authorities", "manage_categories"))
    )
    legacy_catalog = Permission.objects.filter(codename="manage_catalogs").first()
    if legacy_catalog and split_catalog:
        for role in Role.objects.filter(permissions=legacy_catalog).distinct():
            role.permissions.add(*split_catalog)
            role.permissions.remove(legacy_catalog)

    Permission.objects.filter(codename__in=LEGACY_PERMISSION_CODENAMES).delete()


def migrate_legacy_menu_urls() -> int:
    """Point old Cases & reports menu rows at the dashboard (queue page merged)."""
    updated = Permission.objects.filter(url_name="incidents:queue").update(
        url_name="portal:dashboard",
    )
    Permission.objects.filter(
        codename__in=(
            "manage_cases",
            "view_reports",
            "view_allocated_cases",
            "update_allocated_cases",
            "transfer_case",
        )
    ).update(show_in_menu=False)
    return updated


class Command(BaseCommand):
    help = (
        "Sync permissions, FMSC authorities and roles, categories, and bootstrap admin. "
        "Run after deploy or RBAC changes."
    )

    def handle(self, *args, **options):
        sync_permissions_to_database()
        migrate_legacy_permissions()
        legacy_urls = migrate_legacy_menu_urls()
        count = Permission.objects.count()
        valid_codenames = {feature.codename for feature in APP_FEATURES}

        sync_global_roles()
        retired_deleted = delete_retired_roles()
        sync_authorities_and_unit_roles()
        authorities_removed = purge_non_seed_authorities()

        from incidents.models import Category

        for name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(name=name, defaults={"is_active": True})

        removed = (
            Permission.objects.filter(is_builtin=True)
            .exclude(codename__in=valid_codenames)
            .delete()[0]
        )

        from rbac.superuser_access import sync_superuser_portal_roles

        superusers_linked = sync_superuser_portal_roles()
        admin_created, admin_username = ensure_bootstrap_superuser()

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {count} permissions, {len(SEED_AUTHORITIES)} authorities, "
                f"global roles (Student, Lecturer, System Administrator), "
                f"{len(DEFAULT_CATEGORIES)} categories."
                + (f" Updated {legacy_urls} permission row(s) from legacy queue URL." if legacy_urls else "")
                + (f" Removed {removed} obsolete built-in permission row(s)." if removed else "")
                + (f" Removed {retired_deleted} retired role row(s)." if retired_deleted else "")
                + (
                    f" Deleted {authorities_removed} non-seed authority row(s)."
                    if authorities_removed
                    else ""
                )
                + (
                    f" Linked System Administrator role to {superusers_linked} superuser(s)."
                    if superusers_linked
                    else ""
                )
                + (
                    f" Bootstrap admin '{admin_username}' created."
                    if admin_created
                    else f" Bootstrap admin '{admin_username}' updated."
                )
            )
        )
        self.stdout.write(
            "Authorities: Developers, IT Department, Maintenance and cleaning, Security. "
            "End users: Student & Lecturer (own cases + profile). Dashboard: /"
        )
