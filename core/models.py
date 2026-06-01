from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField


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
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    about_description = models.TextField(blank=True)
    footer_text = models.CharField(max_length=160, blank=True)
    languages = models.JSONField(default=list, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=80, blank=True)
    profile_picture = models.FileField(upload_to='profile/', blank=True, null=True)
    resume = models.FileField(upload_to='resume/', blank=True, null=True)
    browser_tab_icon_text = models.CharField(
        max_length=4,
        blank=True,
        default='KP',
        help_text='Short text for the animated browser tab icon, for example KP.',
    )
    browser_tab_animation_speed_ms = models.PositiveIntegerField(
        default=1600,
        help_text='Browser tab animation speed in milliseconds. Higher means slower.',
    )
    browser_tab_title_frames = models.JSONField(
        default=list,
        blank=True,
        help_text='List of browser tab title frames, for example ["def build_portfolio():", "print(\'Kirtan Patel\')"].',
    )
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
    display_order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers display first in profile actions and footer logos.',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Social Link'
        verbose_name_plural = 'Social Links'
        ordering = ['display_order', 'created_at', 'name']

    def __str__(self):
        return self.get_name_display()


class ContactSubmission(CommonModel):
    name = models.CharField(max_length=24)
    email = models.EmailField(max_length=35)
    phone_number = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=55)
    message = models.TextField()
    owner_email_sent = models.BooleanField(default=False)
    confirmation_email_sent = models.BooleanField(default=False)
    telegram_notification_sent = models.BooleanField(default=False)
    email_error = models.TextField(blank=True)
    telegram_error = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.subject or "Contact message"}'


class NotificationSetting(CommonModel):
    class NotificationType(models.TextChoices):
        SITE = 'site', 'Site Notification'
        CONTACT_US = 'contact_us', 'Contact Us Notification'
        SITE_VISIT = 'site_visit', 'Site Visit Notification'

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        unique=True,
    )
    email_notification = models.BooleanField(default=False)
    telegram_notification = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Notification Setting'
        verbose_name_plural = 'Notification Settings'
        ordering = ['notification_type']

    def __str__(self):
        return self.get_notification_type_display()


class UserSiteVisit(CommonModel):
    ip_address = models.GenericIPAddressField()
    browser_name = models.CharField(max_length=80)
    browser_version = models.CharField(max_length=80, blank=True)
    operating_system = models.CharField(max_length=120, blank=True)
    device_type = models.CharField(max_length=40, blank=True)
    user_agent = models.TextField(blank=True)
    referrer_url = models.URLField(max_length=500, blank=True)
    country = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    visit_count = models.PositiveIntegerField(default=1)
    total_duration_seconds = models.PositiveIntegerField(default=0)
    first_visited_at = models.DateTimeField(default=timezone.now)
    last_visited_at = models.DateTimeField()

    class Meta:
        verbose_name = 'User Site Visit'
        verbose_name_plural = 'User Site Visits'
        ordering = ['-last_visited_at']
        constraints = [
            models.UniqueConstraint(
                fields=['ip_address', 'browser_name'],
                name='unique_visit_ip_browser',
            ),
        ]

    def __str__(self):
        return f'{self.ip_address} - {self.browser_name}'


class DynamicTemplate(CommonModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    rich_enrichment = RichTextUploadingField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Dynamic Template'
        verbose_name_plural = 'Dynamic Templates'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    logo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Optional direct logo URL. Used when no logo file is uploaded.',
    )
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


class Project(CommonModel):
    name = models.CharField(max_length=160)
    cover_image = models.FileField(upload_to='projects/covers/', blank=True, null=True)
    description = models.TextField(blank=True)
    github_link = models.CharField(max_length=300, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ProjectSkill(CommonModel):
    SIMPLE_ICON_ALIASES = Skill.SIMPLE_ICON_ALIASES

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_skills',
    )
    name = models.CharField(max_length=120)
    logo = models.FileField(upload_to='project-skills/', blank=True, null=True)
    logo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Optional direct logo URL. Used when no logo file is uploaded.',
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Project Skill'
        verbose_name_plural = 'Project Skills'
        ordering = ['display_order', 'name']

    def __str__(self):
        return f'{self.name} - {self.project.name}'

    @property
    def auto_logo_url(self):
        normalized_name = self.name.strip().lower()
        icon_slug = self.SIMPLE_ICON_ALIASES.get(normalized_name)

        if not icon_slug:
            icon_slug = slugify(normalized_name).replace('-', '')

        return f'https://cdn.simpleicons.org/{icon_slug}'


class ProjectScreenshot(CommonModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='screenshots',
    )
    image = models.FileField(upload_to='projects/screenshots/')
    caption = models.CharField(max_length=160, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Project Screenshot'
        verbose_name_plural = 'Project Screenshots'
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.caption or f'{self.project.name} screenshot'


class Education(CommonModel):

    class EducationType(models.TextChoices):
        HSC = "hsc", "HSC (12th)"
        SSC = "ssc", "SSC (10th)"
        DIPLOMA = "diploma", "Diploma"
        BACHELOR = "bachelor", "Bachelor's Degree"
        MASTER = "master", "Master's Degree"

    education_type = models.CharField(
        max_length=20,
        choices=EducationType.choices
    )

    institution_name = models.CharField(max_length=255)

    degree_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="B.E. Computer Engineering, HSC Science, SSC etc."
    )

    board_or_university = models.CharField(
        max_length=255,
        blank=True
    )

    score = models.CharField(
        max_length=50,
        blank=True,
        help_text="8.4 CGPA, 85%, A Grade"
    )

    start_year = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    passing_year = models.PositiveIntegerField()
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Education'
        verbose_name_plural = 'Education'
        ordering = ['display_order', '-passing_year', 'institution_name']

    def __str__(self):
        degree = self.degree_name or self.get_education_type_display()
        return f'{degree} - {self.institution_name}'
