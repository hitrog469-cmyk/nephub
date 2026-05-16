from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# ── Category Metadata ──────────────────────────────────────────────
CAT_META = {
    'government':  {'label': 'Government',         'icon': 'building-2',     'color': '#1e40af', 'light': '#eff6ff'},
    'loksewa':     {'label': 'Loksewa',             'icon': 'clipboard-list', 'color': '#15803d', 'light': '#f0fdf4'},
    'private':     {'label': 'Private',             'icon': 'briefcase',      'color': '#c2410c', 'light': '#fff7ed'},
    'scholarship': {'label': 'Scholarship',         'icon': 'book-open',      'color': '#a21caf', 'light': '#fdf4ff'},
    'foreign':     {'label': 'Foreign Employment',  'icon': 'plane',          'color': '#be123c', 'light': '#fff1f2'},
    'internship':  {'label': 'Internships',         'icon': 'graduation-cap', 'color': '#0369a1', 'light': '#f0f9ff'},
    'opportunity': {'label': 'Opportunities',       'icon': 'star',           'color': '#b45309', 'light': '#fffbeb'},
}

BS_MONTHS = [
    'Baisakh', 'Jestha', 'Ashadh', 'Shrawan', 'Bhadra', 'Ashwin',
    'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra',
]

BS_MONTHS_NP = [
    'बैशाख', 'जेठ', 'असार', 'साउन', 'भदौ', 'असोज',
    'कार्तिक', 'मंसिर', 'पुष', 'माघ', 'फागुन', 'चैत',
]


# ── Lucide Icon Tag ────────────────────────────────────────────────
@register.simple_tag
def icon(name, css='', size=16):
    return mark_safe(
        f'<i data-lucide="{name}" '
        f'style="width:{size}px;height:{size}px;display:inline-block;vertical-align:middle;flex-shrink:0;" '
        f'class="lc-icon {css}"></i>'
    )


# ── Category Filters ───────────────────────────────────────────────
@register.filter
def cat_icon(category):
    return CAT_META.get(category, {}).get('icon', 'briefcase')


@register.filter
def cat_label(category):
    return CAT_META.get(category, {}).get('label', category.title())


@register.filter
def cat_color(category):
    return CAT_META.get(category, {}).get('color', '#374151')


@register.filter
def cat_light(category):
    return CAT_META.get(category, {}).get('light', '#f9fafb')


@register.filter
def cat_count(cat_counts_dict, category):
    if not cat_counts_dict:
        return 0
    return cat_counts_dict.get(category, 0)


# ── Nepali (BS) Date Filters ───────────────────────────────────────
@register.filter
def to_bs(value):
    """Return BS date string: e.g. '6 Baisakh 2082'"""
    if not value:
        return ''
    try:
        from nepali_datetime import date as NepaliDate
        import datetime
        if isinstance(value, datetime.datetime):
            value = value.date()
        nd = NepaliDate.from_datetime_date(value)
        return f"{nd.day} {BS_MONTHS[nd.month - 1]} {nd.year}"
    except Exception:
        return ''


@register.filter
def to_bs_full(value):
    """Return combined BS + AD: e.g. '6 Baisakh 2082 BS (Apr 19, 2025)'"""
    if not value:
        return ''
    try:
        import datetime
        from nepali_datetime import date as NepaliDate
        if isinstance(value, datetime.datetime):
            value = value.date()
        nd = NepaliDate.from_datetime_date(value)
        bs_str  = f"{nd.day} {BS_MONTHS[nd.month - 1]} {nd.year} BS"
        ad_str  = value.strftime('%b %d, %Y')
        return f"{bs_str} ({ad_str})"
    except Exception:
        try:
            return value.strftime('%b %d, %Y')
        except Exception:
            return str(value)


@register.filter
def to_bs_np(value):
    """Return Nepali Unicode BS date"""
    if not value:
        return ''
    try:
        from nepali_datetime import date as NepaliDate
        import datetime
        if isinstance(value, datetime.datetime):
            value = value.date()
        nd = NepaliDate.from_datetime_date(value)
        return f"{nd.day} {BS_MONTHS_NP[nd.month - 1]} {nd.year}"
    except Exception:
        return ''


# ── Utility Filters ────────────────────────────────────────────────
@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def split(value, arg):
    return value.split(arg)


@register.filter
def in_list(value, lst):
    return value in lst


@register.filter
def commify(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value
