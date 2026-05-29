from django.contrib import admin

from .models import ProfileDetail, SocialLink


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
