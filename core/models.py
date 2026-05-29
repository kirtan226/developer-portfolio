from django.db import models


class CommonModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProfileDetail(CommonModel):
    name = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=160, blank=True)
    about_description = models.TextField(blank=True)
    languages = models.JSONField(default=list, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=80, blank=True)
    profile_picture = models.FileField(upload_to='profile/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Profile Detail'
        verbose_name_plural = 'Profile Details'
        ordering = ['-is_active', '-updated_at']

    def __str__(self):
        return self.name or 'Profile Detail'


class SocialLink(CommonModel):
    class Platform(models.TextChoices):
        GITHUB = 'github', 'GitHub'
        LINKEDIN = 'linkedin', 'LinkedIn'
        TWITTER = 'twitter', 'Twitter / X'
        INSTAGRAM = 'instagram', 'Instagram'
        FACEBOOK = 'facebook', 'Facebook'
        EMAIL = 'email', 'Email'
        THREADS = 'threads', 'Threads'
        YOUTUBE = 'youtube', 'YouTube'
        WEBSITE = 'website', 'Website'
        DISCORD = 'discord', 'Discord'
        TELEGRAM = 'telegram', 'Telegram'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    name = models.CharField(max_length=30, choices=Platform.choices)
    url = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Social Link'
        verbose_name_plural = 'Social Links'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()
