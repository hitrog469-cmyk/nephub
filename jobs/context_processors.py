from django.db.models import Count
from django.utils import timezone


def site_stats(request):
    from jobs.models import Job
    today = timezone.now().date()
    counts_qs = (
        Job.objects.filter(is_active=True)
        .values('category')
        .annotate(c=Count('id'))
    )
    cat_counts = {row['category']: row['c'] for row in counts_qs}
    total_active = sum(cat_counts.values())
    urgent_count = Job.objects.filter(
        is_active=True,
        deadline__gte=today,
        deadline__lte=today + __import__('datetime').timedelta(days=3)
    ).count()
    return {
        'cat_counts': cat_counts,
        'total_active': total_active,
        'urgent_count': urgent_count,
    }
