from django.contrib import admin

from .models import Company, ExperienceRole, ProfileDetail, Skill, SkillCategory, SocialLink


@admin.register(ProfileDetail)
class ProfileDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'location_display', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'role', 'city', 'state', 'country')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Profile', {
            'fields': (
                'name',
                'role',
                'about_description',
                'languages',
                'city',
                'state',
                'country',
                'profile_picture',
                'resume',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Location')
    def location_display(self, obj):
        return ', '.join(part for part in [obj.city, obj.state, obj.country] if part) or 'Not Added'


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'url')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Link', {
            'fields': ('name', 'url', 'is_active')
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
    fields = ('name', 'logo', 'display_order', 'is_active')


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


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'display_order', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'category__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Skill', {
            'fields': ('category', 'name', 'logo', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
