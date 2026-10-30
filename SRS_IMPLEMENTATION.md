# SRS implementation

The main dashboard at `/` provides interactive case summaries, status/category drill-downs, a searchable and sortable case list, CSV export, resolution performance, not-started ageing, and staff authority workload. It uses the existing case visibility rules: reporters see their own cases, authority members with `update_cases` also see their assigned cases, and users with `manage_cases` or `view_reports` see all cases. Operational and management reports use the **dashboard** at `/`. The legacy `/incidents/queue/` URL redirects there with the same filters.

## Interactive dashboard

Date range, category, authority, status, priority, case type and search filters apply to every dashboard report. Summary cards narrow the case list without changing the overview; chart and authority links apply a dashboard-wide filter. Sorting and pagination retain the selected filters. CSV includes all cases matching the current filters and selected summary, not only the visible page. Invalid filters show validation errors and no results. Category/authority filter options come only from cases visible to the current user.

Attempted means reviewed or moved beyond submission (legacy routing-only records without review remain not attempted). Not started means accepted or assigned without a recorded action start. Open excludes closed/rejected, so solved cases awaiting closure remain open. Pending excludes solved/closed/rejected. Average resolution uses solved_at, falling back to closed_at, for currently solved/closed cases with a valid completion time. Missing completion data displays a dash rather than a misleading zero. Ageing shows the oldest 10 matching not-started cases; authority workload shows the 10 largest pending workloads. Summary definitions are also available on the dashboard.

## Workflow

Students and lecturers submit a title, complaint/suggestion type, urgent/normal priority, active category, location, description, declaration, and optional evidence. A case reference is generated from its immutable database ID and submission year. Administrators review, assign/reassign, reject, reopen and close cases. Authority members with `update_cases` can update their assigned cases and record completion evidence. Solving requires a resolution note; only solved cases can be closed. Internal notes are hidden from reporters. Changes and comments are recorded in case history.

AI routing no longer runs on submission, matching the SRS exclusion. Its old module and metadata are retained for compatibility. Migration 0003 returns legacy routing statuses to Submitted for manual review and preserves old routing data and photos. Historical AI role membership no longer grants case access: administrators must explicitly assign an authority.

## Roles and setup

Run `python manage.py migrate`, then **`python manage.py seed_rbac`** (updates permission URLs/menus from `rbac/features.py`, roles, catalogs). The seed command also rewrites any legacy `incidents:queue` permission URLs to the dashboard. Self-registration grants reporting access only; MC/CPM are required for student registration and optional on admin-created accounts.

Assign staff users to the appropriate role through existing user management. System administrators use **Authorities and Categories** to create authorities, enter officer contact details, and select member users. Authority membership and `update_cases` are both required for authority updates. Used authorities/categories are protected from deletion and can be deactivated instead. Management report access is read-only.

## Evidence and delivery

Images are content-validated with Pillow (5 MiB limit). MP4/WebM files have signature, video-stream, size and duration validation using ffprobe. Defaults are 25 MiB and 120 seconds; configure `INCIDENT_VIDEO_MAX_BYTES` and `INCIDENT_VIDEO_MAX_SECONDS`. Nixpacks installs ffmpeg; local Windows installations need ffprobe on PATH or `FFPROBE_PATH`. Missing validation support rejects video uploads rather than accepting unvalidated files. Uploads show submission feedback.

All old and new evidence is downloaded through authenticated, case-scoped endpoints. Do not expose MEDIA_ROOT through an external public media route or public bucket. Use a persistent private volume for production media. HTML/error responses should not be cached; attachment responses are private and no-store.

New case, assignment, status and solved notifications are recorded in-app. Email is sent after transaction commit to active recipients with email addresses, without disclosing other recipients. Configure `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL`; local default is console delivery. SMTP failures are logged while retaining in-app notifications. Password reset uses Django's expiring tokens and the same email configuration. There is no university SSO integration.

Schedule `python manage.py remind_pending_cases --days 7` daily in the hosting scheduler. Same-day repeated reminders are suppressed. This command is provided; the repository does not provision a hosted scheduler.

## Reports and operations

Staff reports filter by date range, priority, category, authority, type and status, with search, CSV export, counts, resolution rate, average resolution days, category/type totals, authority status breakdown, and not-started ageing. Authorities see their assigned queue only. The table shows the latest 200 matches and ageing the oldest 100; CSV includes all matching cases.

`python manage.py backup_cases /secure/new-backup-directory` exports application/auth data and local media. Schedule it in the hosting environment, restrict access, encrypt and copy backups off-host, and test restoration on an isolated database using `loaddata` after migrations. For a consistent production backup, pause writes or use database snapshots coordinated with media snapshots. The command never overwrites an existing directory. Hosting credentials, retention policy, storage encryption, and actual backup/scheduler provisioning remain deployment responsibilities.

Run tests with `python manage.py test --settings=config.test_settings`; this isolates the database, email delivery and file storage without requiring a collected static manifest.
