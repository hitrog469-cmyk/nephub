from django.contrib import admin
from .models import Job, SavedJob, Tag, JobAlert


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display  = ('title', 'organization', 'category', 'job_type', 'location', 'deadline', 'is_active', 'is_featured', 'views')
    list_filter   = ('category', 'job_type', 'experience_level', 'location', 'is_active', 'is_featured')
    search_fields = ('title', 'organization', 'description')
    list_editable = ('is_active', 'is_featured')
    filter_horizontal = ('tags',)
    ordering      = ('deadline',)
    date_hierarchy = 'date_posted'
    readonly_fields = ('views', 'date_posted')
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'organization', 'category', 'job_type', 'experience_level', 'location')}),
        ('Details', {'fields': ('description', 'requirements', 'salary_min', 'salary_max', 'tags')}),
        ('Listing', {'fields': ('deadline', 'apply_link', 'source', 'is_active', 'is_featured')}),
        ('Stats', {'fields': ('views', 'date_posted')}),
    )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'saved_at')
    list_filter  = ('saved_at',)


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display  = ('email', 'user', 'is_active', 'is_verified', 'created_at')
    list_filter   = ('is_active', 'is_verified')
    search_fields = ('email',)
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'verification_token')
