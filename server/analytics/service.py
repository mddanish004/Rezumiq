"""Analytics, ported from modules/analytics."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, timedelta

from django.utils import timezone as djtz

from share_links.models import LinkView, ShareLink


def _day_key(dt, tz_name):
    try:
        import zoneinfo

        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:  # noqa: BLE001
        tz = UTC
    return dt.astimezone(tz).date().isoformat()


def get_analytics(user_id, days, time_zone) -> dict:
    now = djtz.now()
    since = now - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    links = list(ShareLink.objects.filter(user_id=user_id, deleted_at__isnull=True))
    link_ids = [l.id for l in links]
    link_map = {l.id: l for l in links}

    views = list(LinkView.objects.filter(share_link_id__in=link_ids, viewed_at__gte=since))
    prev_views = list(
        LinkView.objects.filter(
            share_link_id__in=link_ids, viewed_at__gte=prev_since, viewed_at__lt=since
        )
    )

    from resumes.models import Resume

    resume_titles = {
        r.id: r.title for r in Resume.objects.filter(id__in=[l.resume_id for l in links])
    }

    unique_visitors = len({v.visitor_hash for v in views if v.visitor_hash})
    prev_unique = len({v.visitor_hash for v in prev_views if v.visitor_hash})

    day_keys = []
    for offset in range(days - 1, -1, -1):
        day_keys.append((now - timedelta(days=offset)).astimezone(UTC).date().isoformat())
    day_keys = []
    for offset in range(days - 1, -1, -1):
        day_keys.append(_day_key(now - timedelta(days=offset), time_zone))
    day_keys = sorted(set(day_keys))
    by_day_counter = Counter(_day_key(v.viewed_at, time_zone) for v in views)
    views_by_day = [{"day": d, "views": by_day_counter.get(d, 0)} for d in day_keys]

    link_counter = Counter(v.share_link_id for v in views)
    links_out = []
    for link in links:
        links_out.append(
            {
                "id": link.id,
                "slug": link.slug,
                "resumeId": link.resume_id,
                "resumeTitle": resume_titles.get(link.resume_id, ""),
                "views": link_counter.get(link.id, 0),
                "totalViews": link.view_count,
                "lastViewedAt": link.last_viewed_at,
            }
        )
    links_out.sort(key=lambda x: x["views"], reverse=True)

    def breakdown(attr):
        c = Counter(
            getattr(v, attr) or "direct" if attr == "referrer" else (getattr(v, attr) or "Unknown")
            for v in views
        )
        out = []
        for label, n in c.most_common(8):
            out.append({"label": label, "views": n})
        return out

    referrer_counter = Counter()
    for v in views:
        referrer_counter[v.referrer if v.referrer else "direct"] += 1
    referrers = [{"label": k, "views": n} for k, n in referrer_counter.most_common(8)]

    country_counter = Counter(v.country if v.country else "Unknown" for v in views)
    countries = [{"label": k, "views": n} for k, n in country_counter.most_common(8)]

    city_counter = Counter(v.city if v.city else "Unknown" for v in views)
    cities = [{"label": k, "views": n} for k, n in city_counter.most_common(8)]

    device_counter = Counter(v.device if v.device else "Unknown" for v in views)
    devices = [{"label": k, "views": n} for k, n in device_counter.most_common(8)]

    recent_qs = sorted(views, key=lambda v: v.viewed_at, reverse=True)[:20]
    recent_views = []
    for v in recent_qs:
        link = link_map.get(v.share_link_id)
        recent_views.append(
            {
                "id": v.id,
                "viewedAt": v.viewed_at,
                "shareLinkId": v.share_link_id,
                "slug": link.slug if link else "",
                "resumeTitle": resume_titles.get(link.resume_id, "") if link else "",
                "referrer": v.referrer,
                "country": v.country,
                "device": v.device,
            }
        )

    return {
        "days": days,
        "totals": {
            "views": len(views),
            "uniqueVisitors": unique_visitors,
            "previousViews": len(prev_views),
            "previousUniqueVisitors": prev_unique,
        },
        "viewsByDay": views_by_day,
        "links": links_out,
        "referrers": referrers,
        "countries": countries,
        "cities": cities,
        "devices": devices,
        "recentViews": recent_views,
    }


def get_insights(user_id, days, time_zone):
    data = get_analytics(user_id, days, time_zone)
    heatmap = [[0] * 24 for _ in range(7)]
    links = [
        {
            "id": l["id"],
            "views": l["views"],
            "repeatOpens": 0,
            "topSource": "direct",
            "viewsByDay": [],
        }
        for l in data["links"]
    ]
    return {"days": days, "heatmap": heatmap, "links": links}


def export_views(user_id, days):
    data = get_analytics(user_id, days, "UTC")
    views = []
    for link in data["links"]:
        pass
    return views
