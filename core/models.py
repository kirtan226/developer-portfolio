from django.db import models
from django.utils.text import slugify


MONTH_CHOICES = [
    (1, 'January'),
    (2, 'February'),
    (3, 'March'),
    (4, 'April'),
    (5, 'May'),
    (6, 'June'),
    (7, 'July'),
    (8, 'August'),
    (9, 'September'),
    (10, 'October'),
    (11, 'November'),
    (12, 'December'),
]


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
    resume = models.FileField(upload_to='resume/', blank=True, null=True)
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


class Company(CommonModel):
    name = models.CharField(max_length=160)
    company_logo = models.FileField(upload_to='companies/', blank=True, null=True)
    display_logo = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ExperienceRole(CommonModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='roles',
    )
    role = models.CharField(max_length=160)
    start_month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    start_year = models.PositiveSmallIntegerField()
    end_month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES, blank=True, null=True)
    end_year = models.PositiveSmallIntegerField(blank=True, null=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Experience Role'
        verbose_name_plural = 'Experience Roles'
        ordering = ['display_order', '-start_year', '-start_month', 'role']

    def __str__(self):
        return f'{self.role} at {self.company.name}'


class SkillCategory(CommonModel):
    name = models.CharField(max_length=120)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Skill Category'
        verbose_name_plural = 'Skill Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Skill(CommonModel):
    SIMPLE_ICON_ALIASES = {
        'drf': 'djangorest',
        'django rest framework': 'djangorest',
        'fast api': 'fastapi',
        'fastapi': 'fastapi',
        'js': 'javascript',
        'node js': 'nodedotjs',
        'node.js': 'nodedotjs',
        'next js': 'nextdotjs',
        'next.js': 'nextdotjs',
        'postgres': 'postgresql',
        'postgre sql': 'postgresql',
        'tailwind': 'tailwindcss',
        'tailwind css': 'tailwindcss',
    }

    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.CASCADE,
        related_name='skills',
    )
    name = models.CharField(max_length=120)
    logo = models.FileField(upload_to='skills/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    @property
    def auto_logo_url(self):
        normalized_name = self.name.strip().lower()
        icon_slug = self.SIMPLE_ICON_ALIASES.get(normalized_name)

        if not icon_slug:
            icon_slug = slugify(normalized_name).replace('-', '')

        return f'https://cdn.simpleicons.org/{icon_slug}'
