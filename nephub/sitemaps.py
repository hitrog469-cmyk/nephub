from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from jobs.models import Job, Category
from blog.models import BlogPost


class NepHubSitemap(Sitemap):
    protocol = 'https'


class StaticSitemap(NepHubSitemap):
    priority = 0.6
    changefreq = 'weekly'

    def items(self):
        return ['home', 'search', 'about', 'advertise', 'blog_list']

    def location(self, item):
        return reverse(item)


class CategorySitemap(NepHubSitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return [c[0] for c in Category.choices]

    def location(self, slug):
        return reverse('category_page', args=[slug])


class JobSitemap(NepHubSitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        from django.db.models import Q
        today = timezone.now().date()
        return Job.objects.filter(is_active=True).filter(
            Q(deadline__gte=today) | Q(deadline__isnull=True)
        ).order_by('-date_posted')[:1000]

    def location(self, obj):
        return reverse('job_detail', args=[obj.pk])

    def lastmod(self, obj):
        return obj.date_posted


class BlogSitemap(NepHubSitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return BlogPost.objects.order_by('-published_at')[:500]

    def lastmod(self, obj):
        return obj.published_at


SITEMAPS = {
    'static':     StaticSitemap,
    'categories': CategorySitemap,
    'jobs':       JobSitemap,
    'blog':       BlogSitemap,
}
