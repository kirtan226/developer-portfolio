from django.contrib import admin

from .models import (
    Company,
    ContactSubmission,
    DynamicTemplate,
    Education,
    ExperienceRole,
    NotificationSetting,
    ProfileDetail,
    Project,
    ProjectSkill,
    ProjectScreenshot,
    Skill,
    SkillCategory,
    SocialLink,
    UserSiteVisit,
)


@admin.register(ProfileDetail)
class ProfileDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'email', 'phone_number', 'location_display', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'role', 'email', 'phone_number', 'city', 'state', 'country')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Profile', {
            'fields': (
                'name',
                'role',
                'email',
                'phone_number',
                'about_description',
                'footer_text',
                'languages',
                'city',
                'state',
                'country',
                'profile_picture',
                'resume',
                'is_active',
            )
        }),
        ('Browser Tab Animation', {
            'fields': (
                'browser_tab_icon_text',
                'browser_tab_animation_speed_ms',
                'browser_tab_title_frames',
            ),
            'description': 'Controls the animated browser tab title and KP icon. Add title frames as a JSON list of strings.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/profile-image-crop.css',)
        }
        js = ('admin/js/profile-image-crop.js',)

    @admin.display(description='Location')
    def location_display(self, obj):
        return ', '.join(part for part in [obj.city, obj.state, obj.country] if part) or 'Not Added'


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'display_order', 'is_active', 'updated_at')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'url')
    ordering = ('display_order', 'created_at', 'name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Link', {
            'fields': ('name', 'url', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'phone_number',
        'subject',
        'owner_email_sent',
        'confirmation_email_sent',
        'telegram_notification_sent',
        'is_read',
        'created_at',
    )
    list_filter = (
        'owner_email_sent',
        'confirmation_email_sent',
        'telegram_notification_sent',
        'is_read',
        'created_at',
    )
    search_fields = ('name', 'email', 'phone_number', 'subject', 'message')
    readonly_fields = (
        'name',
        'email',
        'phone_number',
        'subject',
        'message',
        'owner_email_sent',
        'confirmation_email_sent',
        'telegram_notification_sent',
        'email_error',
        'telegram_error',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('Contact Details', {
            'fields': ('name', 'email', 'phone_number', 'subject', 'message', 'is_read')
        }),
        ('Email Status', {
            'fields': ('owner_email_sent', 'confirmation_email_sent', 'email_error')
        }),
        ('Telegram Status', {
            'fields': ('telegram_notification_sent', 'telegram_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = (
        'notification_type',
        'email_notification',
        'telegram_notification',
        'is_active',
        'updated_at',
    )
    list_filter = ('email_notification', 'telegram_notification', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Notification', {
            'fields': (
                'notification_type',
                'email_notification',
                'telegram_notification',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(UserSiteVisit)
class UserSiteVisitAdmin(admin.ModelAdmin):
    list_display = (
        'ip_address',
        'browser_name',
        'city',
        'state',
        'country',
        'operating_system',
        'device_type',
        'visit_count',
        'duration_display',
        'is_active',
        'first_visited_at',
        'last_visited_at',
    )
    list_editable = ('is_active',)
    list_filter = (
        'is_active',
        'browser_name',
        'country',
        'state',
        'city',
        'operating_system',
        'device_type',
        'created_at',
        'first_visited_at',
        'last_visited_at',
    )
    search_fields = (
        'ip_address',
        'browser_name',
        'browser_version',
        'operating_system',
        'country',
        'state',
        'city',
        'user_agent',
        'referrer_url',
    )
    readonly_fields = (
        'ip_address',
        'browser_name',
        'browser_version',
        'operating_system',
        'device_type',
        'user_agent',
        'referrer_url',
        'country',
        'state',
        'city',
        'visit_count',
        'total_duration_seconds',
        'first_visited_at',
        'last_visited_at',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('Visitor', {
            'fields': (
                'ip_address',
                'browser_name',
                'browser_version',
                'operating_system',
                'device_type',
                'user_agent',
                'referrer_url',
                'country',
                'state',
                'city',
                'is_active',
            )
        }),
        ('Visit Stats', {
            'fields': ('visit_count', 'total_duration_seconds', 'first_visited_at', 'last_visited_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Duration')
    def duration_display(self, obj):
        minutes, seconds = divmod(obj.total_duration_seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f'{hours}h {minutes}m {seconds}s'

        if minutes:
            return f'{minutes}m {seconds}s'

        return f'{seconds}s'


@admin.register(DynamicTemplate)
class DynamicTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'slug', 'rich_enrichment')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Template', {
            'fields': ('name', 'slug', 'rich_enrichment', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


class ExperienceRoleInline(admin.StackedInline):
    model = ExperienceRole
    extra = 1
    fields = (
        'role',
        'start_month',
        'start_year',
        'end_month',
        'end_year',
        'description',
        'display_order',
        'is_active',
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_logo', 'display_order', 'is_active', 'updated_at')
    list_filter = ('display_logo', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'roles__role', 'roles__description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (ExperienceRoleInline,)
    fieldsets = (
        ('Company', {
            'fields': (
                'name',
                'company_logo',
                'display_logo',
                'display_order',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/logo-image-crop.css',)
        }
        js = ('admin/js/logo-image-crop.js',)


@admin.register(ExperienceRole)
class ExperienceRoleAdmin(admin.ModelAdmin):
    list_display = ('role', 'company', 'duration_display', 'display_order', 'is_active', 'updated_at')
    list_filter = ('company', 'is_active', 'start_year', 'end_year', 'created_at', 'updated_at')
    search_fields = ('role', 'company__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Role', {
            'fields': (
                'company',
                'role',
                'start_month',
                'start_year',
                'end_month',
                'end_year',
                'description',
                'display_order',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Duration')
    def duration_display(self, obj):
        start = f'{obj.get_start_month_display()} {obj.start_year}'
        end = (
            f'{obj.get_end_month_display()} {obj.end_year}'
            if obj.end_month and obj.end_year
            else 'Present'
        )
        return f'{start} - {end}'


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ('name', 'logo', 'logo_url', 'display_order', 'is_active')

    class Media:
        css = {
            'all': ('admin/css/logo-image-crop.css',)
        }
        js = ('admin/js/logo-image-crop.js',)


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = (SkillInline,)
    fieldsets = (
        ('Category', {
            'fields': ('name', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/logo-image-crop.css',)
        }
        js = ('admin/js/logo-image-crop.js',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'display_order', 'has_custom_logo_url', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'category__name', 'logo_url')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Skill', {
            'fields': ('category', 'name', 'logo', 'logo_url', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/logo-image-crop.css',)
        }
        js = ('admin/js/logo-image-crop.js',)

    @admin.display(boolean=True, description='Logo URL')
    def has_custom_logo_url(self, obj):
        return bool(obj.logo_url)


class ProjectScreenshotInline(admin.TabularInline):
    model = ProjectScreenshot
    extra = 1
    fields = ('image', 'caption', 'display_order', 'is_active')

    class Media:
        css = {
            'all': ('admin/css/project-image-crop.css',)
        }
        js = ('admin/js/project-image-crop.js',)


class ProjectSkillInline(admin.TabularInline):
    model = ProjectSkill
    extra = 1
    fields = ('name', 'logo', 'logo_url', 'display_order', 'is_active')

    class Media:
        css = {
            'all': ('admin/css/logo-image-crop.css',)
        }
        js = ('admin/js/logo-image-crop.js',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'github_link', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'github_link', 'project_skills__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (ProjectSkillInline, ProjectScreenshotInline)
    fieldsets = (
        ('Project', {
            'fields': (
                'name',
                'cover_image',
                'description',
                'github_link',
                'display_order',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/project-image-crop.css',)
        }
        js = ('admin/js/project-image-crop.js',)


@admin.register(ProjectSkill)
class ProjectSkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'display_order', 'has_custom_logo_url', 'is_active', 'updated_at')
    list_filter = ('project', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'project__name', 'logo_url')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Project Skill', {
            'fields': ('project', 'name', 'logo', 'logo_url', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/logo-image-crop.css',)
        }
        js = ('admin/js/logo-image-crop.js',)

    @admin.display(boolean=True, description='Logo URL')
    def has_custom_logo_url(self, obj):
        return bool(obj.logo_url)


@admin.register(ProjectScreenshot)
class ProjectScreenshotAdmin(admin.ModelAdmin):
    list_display = ('project', 'caption', 'display_order', 'is_active', 'updated_at')
    list_filter = ('project', 'is_active', 'created_at', 'updated_at')
    search_fields = ('project__name', 'caption')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Screenshot', {
            'fields': ('project', 'image', 'caption', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/project-image-crop.css',)
        }
        js = ('admin/js/project-image-crop.js',)


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = (
        'institution_name',
        'degree_display',
        'education_type',
        'duration_display',
        'score',
        'display_order',
        'is_active',
        'updated_at',
    )
    list_filter = ('education_type', 'is_active', 'passing_year', 'created_at', 'updated_at')
    search_fields = ('institution_name', 'degree_name', 'board_or_university', 'score')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Education', {
            'fields': (
                'education_type',
                'institution_name',
                'degree_name',
                'board_or_university',
                'score',
                'start_year',
                'passing_year',
                'display_order',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Degree')
    def degree_display(self, obj):
        return obj.degree_name or obj.get_education_type_display()

    @admin.display(description='Duration')
    def duration_display(self, obj):
        if obj.start_year:
            return f'{obj.start_year} - {obj.passing_year}'
        return obj.passing_year
