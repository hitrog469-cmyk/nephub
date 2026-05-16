from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class BlogCategory(models.TextChoices):
    NEWS = 'news', 'News'
    TIPS = 'tips', 'Career Tips'
    SCHOLARSHIP = 'scholarship_news', 'Scholarship Updates'
    LOKSEWA = 'loksewa_update', 'Loksewa Updates'
    FOREIGN = 'foreign_news', 'Foreign Employment News'


class BlogPost(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=320, unique=True, blank=True)
    excerpt = models.TextField(max_length=400)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=BlogCategory.choices, default=BlogCategory.NEWS)
    author_name = models.CharField(max_length=100, default='NepHub Team')
    published_at = models.DateTimeField(default=timezone.now)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            self.slug = base
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog_detail', kwargs={'slug': self.slug})
