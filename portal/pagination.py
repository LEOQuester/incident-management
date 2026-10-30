"""Shared list pagination for portal and incident list views."""

from django.core.paginator import Paginator

DEFAULT_PAGE_SIZE = 15
ADMIN_PAGE_SIZE = 25
NOTIFICATION_PAGE_SIZE = 20


def paginate(request, queryset, *, per_page=DEFAULT_PAGE_SIZE):
    page = Paginator(queryset, per_page).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    query.pop("export", None)

    def page_url(num: int) -> str:
        params = query.copy()
        params["page"] = str(num)
        return "?" + params.urlencode()

    previous_url = page_url(page.previous_page_number()) if page.has_previous() else ""
    next_url = page_url(page.next_page_number()) if page.has_next() else ""
    return page, previous_url, next_url
