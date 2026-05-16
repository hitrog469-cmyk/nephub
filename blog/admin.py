from django.contrib import admin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author_name', 'published_at', 'is_featured', 'views')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('category', 'is_featured')
    search_fields = ('title', 'excerpt', 'content')
    list_editable = ('is_featured',)
    date_hierarchy = 'published_at'
    readonly_fields = ('views',)
