from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.decorators.http import require_POST
from django.db.utils import DatabaseError, OperationalError, ProgrammingError
from django.db.models import Prefetch

import json
from copy import deepcopy

from django.conf import settings

from .models import (
    Company,
    ContactSubmission,
    Education,
    ExperienceRole,
    ProfileDetail,
    Project,
    ProjectSkill,
    ProjectScreenshot,
    Skill,
    SkillCategory,
    SocialLink,
)
from .utils import (
    add_site_visit_duration,
    record_site_visit,
    send_contact_notifications,
    send_site_visit_notifications,
)


NOT_ADDED = 'Not Added'
PROJECT_FALLBACK_IMAGE = 'images/projects/project-01/PROJECT_COVER_IMAGE.jpg'
SITE_ICON_IMAGE = 'images/share-icon.svg'
SITE_SHARE_IMAGE = 'images/share-preview.jpg'
CONTACT_FIELD_LIMITS = {
    'name': 24,
    'email': 35,
    'phone_number': 30,
    'subject': 55,
    'message': 355,
}


DEFAULT_BROWSER_TAB_FRAMES = [
    'class KirtanPatel(Developer):',
    'portfolio = KirtanPatel()',
    'def build_portfolio():',
    "print('Kirtan Patel')",
    'python manage.py runserver',
]


def get_active_profile():
    try:
        return ProfileDetail.objects.filter(is_active=True).order_by('-updated_at').first()
    except (DatabaseError, OperationalError, ProgrammingError):
        return None


def get_active_social_links():
    try:
        return SocialLink.objects.filter(is_active=True).exclude(url='').order_by('display_order', 'created_at', 'name')
    except (DatabaseError, OperationalError, ProgrammingError):
        return []


def get_active_companies():
    try:
        return (
            Company.objects
            .filter(is_active=True, roles__is_active=True)
            .prefetch_related(Prefetch(
                'roles',
                queryset=ExperienceRole.objects.filter(is_active=True).order_by(
                    'display_order',
                    '-start_year',
                    '-start_month',
                    'role',
                ),
            ))
            .distinct()
            .order_by('display_order', 'name')
        )
    except (DatabaseError, OperationalError, ProgrammingError):
        return []


def get_active_skill_categories():
    try:
        return (
            SkillCategory.objects
            .filter(is_active=True, skills__is_active=True)
            .prefetch_related(Prefetch(
                'skills',
                queryset=Skill.objects.filter(is_active=True).order_by('display_order', 'name'),
            ))
            .distinct()
            .order_by('display_order', 'name')
        )
    except (DatabaseError, OperationalError, ProgrammingError):
        return []


def get_active_educations():
    try:
        return Education.objects.filter(is_active=True).order_by(
            'display_order',
            '-passing_year',
            'institution_name',
        )
    except (DatabaseError, OperationalError, ProgrammingError):
        return []


def get_active_projects():
    try:
        return (
            Project.objects
            .filter(is_active=True)
            .prefetch_related(
                Prefetch(
                    'project_skills',
                    queryset=ProjectSkill.objects.filter(is_active=True).order_by(
                        'display_order',
                        'name',
                    ),
                ),
                Prefetch(
                    'screenshots',
                    queryset=ProjectScreenshot.objects.filter(is_active=True).order_by(
                        'display_order',
                        'id',
                    ),
                ),
            )
            .order_by('display_order', 'name')
        )
    except (DatabaseError, OperationalError, ProgrammingError):
        return []


def normalize_languages(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(',') if item.strip()]

    return []


def normalize_roles(value):
    """Accept a list or a JSON/string with separators and return list of role strings."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        s = value.strip()
        # try parse JSON list
        if (s.startswith('[') and s.endswith(']')):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass

        # fallback: split on common separators
        return [item.strip() for item in re_split_roles(s) if item.strip()]

    return []


def re_split_roles(s):
    import re
    return re.split(r'[,;|\\n]+', s)


def format_location(profile):
    if not profile:
        return f'Location: {NOT_ADDED}'

    parts = [
        profile.city.strip(),
        profile.state.strip(),
        profile.country.strip(),
    ]
    location = ', '.join(part for part in parts if part)
    return location or f'Location: {NOT_ADDED}'


def build_browser_tab_config(profile, page_title):
    title_frames = []

    if profile and isinstance(profile.browser_tab_title_frames, list):
        title_frames = [
            str(frame).strip()
            for frame in profile.browser_tab_title_frames
            if str(frame).strip()
        ]

    if not title_frames:
        title_frames = DEFAULT_BROWSER_TAB_FRAMES.copy()

    if page_title and page_title not in title_frames:
        title_frames.append(page_title)

    animation_speed = profile.browser_tab_animation_speed_ms if profile else 1600
    if not isinstance(animation_speed, int) or animation_speed < 500:
        animation_speed = 1600

    icon_text = profile.browser_tab_icon_text.strip() if profile and profile.browser_tab_icon_text.strip() else 'KP'

    return {
        'iconText': icon_text[:4],
        'speedMs': animation_speed,
        'titleFrames': title_frames,
    }


def build_absolute_asset_url(request, asset_path):
    asset_url = static(asset_path)

    if request:
        return request.build_absolute_uri(asset_url)

    return asset_url


def build_share_icon_url(request):
    if request:
        return request.build_absolute_uri(reverse('share_icon_svg'))

    return build_absolute_asset_url(request, SITE_ICON_IMAGE)


def build_share_image_url(request):
    return build_absolute_asset_url(request, SITE_SHARE_IMAGE)


def build_share_metadata(request, page_title, description):
    cleaned_description = ' '.join(description.split()) if description else ''
    share_description = (
        cleaned_description
        if description and NOT_ADDED not in description
        else 'Portfolio website showcasing design engineering work.'
    )
    page_url = request.build_absolute_uri(request.path) if request else ''

    return {
        'title': page_title,
        'description': share_description,
        'url': page_url,
        'site_name': page_title,
        'image': build_share_image_url(request),
        'image_type': 'image/jpeg',
        'image_width': 1200,
        'image_height': 630,
        'image_alt': page_title,
        'icon': build_share_icon_url(request),
    }


def social_icon_for(name):
    normalized_name = name.strip().lower()
    icon_map = {
        'email': 'bi-envelope',
        'github': 'bi-github',
        'linkedin': 'bi-linkedin',
        'instagram': 'bi-instagram',
        'twitter': 'bi-twitter-x',
        'threads': 'bi-threads',
        'facebook': 'bi-facebook',
        'youtube': 'bi-youtube',
        'website': 'bi-globe2',
        'discord': 'bi-discord',
        'telegram': 'bi-telegram',
        'whatsapp': 'bi-whatsapp',
    }
    return icon_map.get(normalized_name, 'bi-link-45deg')


def normalize_social_url(name, url):
    cleaned_url = url.strip()
    if name.strip().lower() == 'email' and '@' in cleaned_url and not cleaned_url.startswith('mailto:'):
        return f'mailto:{cleaned_url}'
    return cleaned_url


def build_social_links():
    social_links = []

    for link in get_active_social_links():
        name = link.name.strip()
        label = link.get_name_display()
        url = normalize_social_url(name, link.url)

        if not name or not url:
            continue

        social_links.append({
            'name': label,
            'icon': social_icon_for(name),
            'link': url,
        })

    return social_links


def share_icon_svg(request):
    profile = get_active_profile()
    icon_text = (
        profile.browser_tab_icon_text.strip()
        if profile and profile.browser_tab_icon_text.strip()
        else 'KP'
    )[:4].upper()
    font_size = 156 if len(icon_text) <= 2 else 116
    escaped_icon_text = escape(icon_text)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="{escaped_icon_text}">
<defs>
  <linearGradient id="kpGradient" x1="96" y1="80" x2="416" y2="432" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#7de7ff"/>
    <stop offset="1" stop-color="#ff867d"/>
  </linearGradient>
</defs>
<rect width="512" height="512" rx="128" fill="#090b0d"/>
<circle cx="256" cy="256" r="184" fill="none" stroke="url(#kpGradient)" stroke-width="28"/>
<text x="256" y="274" text-anchor="middle" dominant-baseline="middle" fill="url(#kpGradient)" font-family="Inter, Arial, sans-serif" font-size="{font_size}" font-weight="800" letter-spacing="0">{escaped_icon_text}</text>
</svg>"""

    response = HttpResponse(svg, content_type='image/svg+xml')
    response['Cache-Control'] = 'public, max-age=3600'
    return response


def format_role_duration(role):
    start = f'{role.get_start_month_display()} {role.start_year}'
    end = (
        f'{role.get_end_month_display()} {role.end_year}'
        if role.end_month and role.end_year
        else 'Present'
    )
    return f'{start} - {end}'


def parse_description_points(description):
    cleaned_description = description.strip()

    if not cleaned_description:
        return [], []

    if '•' in cleaned_description:
        return [
            point.strip()
            for point in cleaned_description.split('•')
            if point.strip()
        ], []

    points = []
    paragraphs = []

    for line in cleaned_description.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        if cleaned_line.startswith(('-', '*')):
            points.append(cleaned_line.lstrip('-*').strip())
        elif points:
            points[-1] = f'{points[-1]} {cleaned_line}'
        else:
            paragraphs.append(cleaned_line)

    return points, paragraphs


def parse_project_description(description):
    cleaned_description = description.strip()

    if not cleaned_description:
        return [], []

    if '•' in cleaned_description:
        return [
            point.strip()
            for point in cleaned_description.split('•')
            if point.strip()
        ], []

    return parse_description_points(cleaned_description)


def build_companies():
    companies = []

    for company in get_active_companies():
        roles = []

        for role in company.roles.all():
            bullet_points, paragraphs = parse_description_points(role.description)
            preview_points = bullet_points[:2]
            preview_text = ' '.join(paragraphs) if not preview_points else ''

            roles.append({
                'role': role.role,
                'timeframe': format_role_duration(role),
                'description': role.description.strip(),
                'preview': preview_text,
                'preview_points': preview_points,
                'bullet_points': bullet_points,
                'paragraphs': paragraphs,
            })

        if roles:
            companies.append({
                'company': company.name,
                'logo': company.company_logo.url if company.display_logo and company.company_logo else '',
                'roles': roles,
            })

    return companies


def build_skill_categories():
    skill_categories = []

    for category in get_active_skill_categories():
        skills = []

        for skill in category.skills.all():
            if not skill.is_active:
                continue

            skills.append({
                'name': skill.name,
                'logo': skill.logo.url if skill.logo else skill.logo_url.strip() or skill.auto_logo_url,
                'has_uploaded_logo': bool(skill.logo),
                'initial': skill.name[:1].upper(),
                'display_order': skill.display_order,
            })

        if skills:
            skill_categories.append({
                'name': category.name,
                'skills': skills,
            })

    return skill_categories


def format_education_duration(education):
    if education.start_year:
        return f'{education.start_year} - {education.passing_year}'
    return str(education.passing_year)


def build_educations():
    educations = []

    for education in get_active_educations():
        degree = education.degree_name.strip() or education.get_education_type_display()
        details = []

        if education.board_or_university.strip():
            details.append(education.board_or_university.strip())

        if education.score.strip():
            details.append(education.score.strip())

        educations.append({
            'institution': education.institution_name,
            'degree': degree,
            'education_type': education.get_education_type_display(),
            'duration': format_education_duration(education),
            'details': details,
        })

    return educations


def image_item(src, alt, is_static=False):
    return {
        'src': src,
        'alt': alt,
        'is_static': is_static,
    }


def build_project_technologies(project):
    technologies = []

    for technology in project.project_skills.all():
        technologies.append({
            'name': technology.name,
            'logo': technology.logo.url if technology.logo else technology.logo_url.strip() or technology.auto_logo_url,
            'initial': technology.name[:1].upper(),
        })

    return technologies


def build_projects():
    projects = []

    for project in get_active_projects():
        cover_image = (
            image_item(project.cover_image.url, f'{project.name} cover image')
            if project.cover_image
            else image_item(PROJECT_FALLBACK_IMAGE, f'{project.name} cover image', is_static=True)
        )
        gallery_images = [
            image_item(screenshot.image.url, screenshot.caption or f'{project.name} screenshot')
            for screenshot in project.screenshots.all()
            if screenshot.image
        ]

        if not gallery_images:
            gallery_images = [cover_image]

        description_points, description_paragraphs = parse_project_description(project.description)
        technologies = build_project_technologies(project)

        projects.append({
            'name': project.name,
            'cover_image': cover_image,
            'technologies': technologies,
            'technology_preview': technologies[:3],
            'has_more_technologies': len(technologies) > 3,
            'description': project.description.strip(),
            'description_points': description_points,
            'description_paragraphs': description_paragraphs,
            'github_link': project.github_link.strip(),
            'site_link': project.site_link.strip(),
            'gallery_images': gallery_images,
            'has_multiple_images': len(gallery_images) > 1,
        })

    return projects


def validate_contact_form_data(contact_form):
    errors = {}
    required_messages = {
        'name': 'Please fill name.',
        'email': 'Please fill email.',
        'subject': 'Please fill subject.',
        'message': 'Please fill message.',
    }
    length_messages = {
        'name': 'Name should be 24 characters or less.',
        'email': 'Email should be 35 characters or less.',
        'phone_number': 'Phone number should be 30 characters or less.',
        'subject': 'Subject should be 55 characters or less.',
        'message': 'Message should be 355 characters or less.',
    }

    for field, required_message in required_messages.items():
        value = contact_form.get(field, '')

        if not value:
            errors[field] = required_message
            continue

        if len(value) > CONTACT_FIELD_LIMITS[field]:
            errors[field] = length_messages[field]

    phone_number = contact_form.get('phone_number', '')
    if phone_number and len(phone_number) > CONTACT_FIELD_LIMITS['phone_number']:
        errors['phone_number'] = length_messages['phone_number']

    if contact_form.get('email') and 'email' not in errors:
        try:
            validate_email(contact_form['email'])
        except ValidationError:
            errors['email'] = 'Please enter a valid email.'

    return errors


class HomeView(View):
    template_name = 'core/home.html'
    context_cache_key = 'core.home_context.v1'

    def build_context(self, request=None, contact_status=None, contact_form=None, contact_errors=None):
        profile = get_active_profile()
        profile_languages = normalize_languages(profile.languages) if profile else []
        name = profile.name.strip() if profile and profile.name.strip() else f'Name: {NOT_ADDED}'
        # Normalize roles list (new JSONField or list). If not present, fallback to NOT_ADDED.
        roles_list = normalize_roles(profile.roles) if profile else []
        if not roles_list:
            roles_list = [f'Role: {NOT_ADDED}']

        # Single role string for legacy template compatibility
        role = roles_list[0]

        # role display duration in ms (how long after fully typed to pause before erasing)
        role_display_duration = profile.role_display_duration_ms if profile and getattr(profile, 'role_display_duration_ms', None) is not None else 1400
        try:
            role_display_duration = int(role_display_duration)
            if role_display_duration < 0:
                role_display_duration = 1400
        except Exception:
            role_display_duration = 1400
        location = format_location(profile)
        about_description = (
            profile.about_description.strip()
            if profile and profile.about_description.strip()
            else f'About: {NOT_ADDED}'
        )

        person = {
            'name': name,
            'first_name': name.split()[0] if name and NOT_ADDED not in name else NOT_ADDED,
            'role': role,
            # Include roles array and JSON for frontend use
            'roles': roles_list,
            'roles_json': json.dumps(roles_list),
            'role_display_duration_ms': role_display_duration,
            'footer_text': (
                profile.footer_text.strip()
                if profile and profile.footer_text.strip()
                else f'© {timezone.now().year} / {name} all rights reserved'
            ),
            'avatar': profile.profile_picture.url if profile and profile.profile_picture else '',
            'resume': profile.resume.url if profile and profile.resume else '',
            'fallback_avatar': 'images/avatar.jpg',
            'email': profile.email.strip() if profile and profile.email.strip() else '',
            'phone_number': profile.phone_number.strip() if profile and profile.phone_number.strip() else '',
            'location': location,
            'languages': profile_languages or [f'Languages: {NOT_ADDED}'],
        }

        social_links = build_social_links()
        skill_categories = build_skill_categories()
        companies = build_companies()
        educations = build_educations()
        projects = build_projects()
        fallback_companies = [
            {
                'company': 'FLY',
                'logo': '',
                'roles': [
                    {
                        'timeframe': 'January 2022 - Present',
                        'role': 'Senior Design Engineer',
                        'description': 'Redesigned the UI/UX for the FLY platform and integrated AI tools into design workflows.',
                        'preview': 'Redesigned the UI/UX for the FLY platform and integrated AI tools into design workflows.',
                        'bullet_points': ['Redesigned the UI/UX for the FLY platform.', 'Integrated AI tools into design workflows.'],
                        'paragraphs': [],
                    },
                    {
                        'timeframe': 'June 2021 - December 2021',
                        'role': 'Design Intern',
                        'description': 'Supported design delivery and assisted with interface documentation.',
                        'preview': 'Supported design delivery and assisted with interface documentation.',
                        'bullet_points': ['Supported design delivery.', 'Assisted with interface documentation.'],
                        'paragraphs': [],
                    },
                ],
            },
        ]
        fallback_skill_categories = [
            {
                'name': 'Frontend',
                'skills': [
                    {
                        'name': 'JavaScript',
                        'logo': 'https://cdn.simpleicons.org/javascript',
                        'has_uploaded_logo': False,
                        'initial': 'J',
                    },
                    {
                        'name': 'Bootstrap',
                        'logo': 'https://cdn.simpleicons.org/bootstrap',
                        'has_uploaded_logo': False,
                        'initial': 'B',
                    },
                ],
            },
            {
                'name': 'Backend',
                'skills': [
                    {
                        'name': 'Python',
                        'logo': 'https://cdn.simpleicons.org/python',
                        'has_uploaded_logo': False,
                        'initial': 'P',
                    },
                    {
                        'name': 'Django',
                        'logo': 'https://cdn.simpleicons.org/django',
                        'has_uploaded_logo': False,
                        'initial': 'D',
                    },
                ],
            },
        ]

        about = {
            'intro': {
                'title': 'Introduction',
                'description': about_description,
            },
            'work': {
                'title': 'Experience',
                'companies': companies or fallback_companies,
            },
            'education': {
                'title': 'Education',
                'items': educations or [
                    {
                        'institution': 'University of Jakarta',
                        'degree': 'Software Engineering',
                        'education_type': 'Bachelor',
                        'duration': '2020 - 2024',
                        'details': ['University of Jakarta', '8.4 CGPA'],
                    },
                    {
                        'institution': 'Build the Future',
                        'degree': 'Online Marketing',
                        'education_type': 'Diploma',
                        'duration': '2019',
                        'details': ['Personal branding', '85%'],
                    },
                ],
            },
            'technical': {
                'title': 'Skills',
                'categories': skill_categories or fallback_skill_categories,
            },
        }

        page_title = f"{person['name']} Portfolio"

        context = {
            'person': person,
            'social_links': social_links,
            'about': about,
            'projects': projects or [
                {
                    'name': 'Once UI Design System',
                    'description': 'A customizable design system built for fast, consistent product interfaces.',
                    'cover_image': image_item(PROJECT_FALLBACK_IMAGE, 'Once UI Design System cover image', is_static=True),
                    'technologies': [
                        {
                            'name': 'Django',
                            'logo': 'https://cdn.simpleicons.org/django',
                            'initial': 'D',
                        },
                        {
                            'name': 'Bootstrap',
                            'logo': 'https://cdn.simpleicons.org/bootstrap',
                            'initial': 'B',
                        },
                    ],
                    'github_link': '',
                    'site_link': '',
                    'gallery_images': [
                        image_item(PROJECT_FALLBACK_IMAGE, 'Once UI Design System cover image', is_static=True),
                    ],
                    'has_multiple_images': False,
                },
                {
                    'name': 'Figma to Code Pipeline',
                    'description': 'A workflow that automates design handovers and speeds up production builds.',
                    'cover_image': image_item(PROJECT_FALLBACK_IMAGE, 'Figma to Code Pipeline cover image', is_static=True),
                    'technologies': [
                        {
                            'name': 'Python',
                            'logo': 'https://cdn.simpleicons.org/python',
                            'initial': 'P',
                        },
                        {
                            'name': 'JavaScript',
                            'logo': 'https://cdn.simpleicons.org/javascript',
                            'initial': 'J',
                        },
                    ],
                    'github_link': '',
                    'site_link': '',
                    'gallery_images': [
                        image_item(PROJECT_FALLBACK_IMAGE, 'Figma to Code Pipeline cover image', is_static=True),
                    ],
                    'has_multiple_images': False,
                },
            ],
            'current_year': timezone.now().year,
            'page_title': page_title,
            'share_metadata': build_share_metadata(request, page_title, about_description),
            'browser_tab_config': build_browser_tab_config(profile, page_title),
            'contact_status': contact_status,
            'contact_form': contact_form or {},
            'contact_errors': contact_errors or {},
        }
        return context

    def get(self, request, *args, **kwargs):
        context = cache.get(self.context_cache_key)

        if context is None:
            context = self.build_context()
            cache.set(
                self.context_cache_key,
                context,
                timeout=settings.HOME_CONTEXT_CACHE_SECONDS,
            )

        context = deepcopy(context)
        context['share_metadata'] = build_share_metadata(
            request,
            context['page_title'],
            context['about']['intro']['description'],
        )
        context['track_site_visit_duration'] = settings.TRACK_SITE_VISIT_DURATION
        context['site_visit_alert_delay_ms'] = settings.SITE_VISIT_ALERT_DELAY_SECONDS * 1000
        return render(request, self.template_name, context)


@require_POST
def contact_submit_api(request):
    contact_form = {
        'name': request.POST.get('name', '').strip(),
        'email': request.POST.get('email', '').strip(),
        'phone_number': request.POST.get('phone_number', '').strip(),
        'subject': request.POST.get('subject', '').strip(),
        'message': request.POST.get('message', '').strip(),
    }
    errors = validate_contact_form_data(contact_form)

    if errors:
        return JsonResponse({
            'ok': False,
            'message': 'Please fix the highlighted fields.',
            'errors': errors,
        }, status=400)

    contact_submission = ContactSubmission.objects.create(**contact_form)
    profile = get_active_profile()

    try:
        notification_result = send_contact_notifications(contact_submission, profile)
        contact_submission.owner_email_sent = notification_result['owner_email_sent']
        contact_submission.confirmation_email_sent = notification_result['confirmation_email_sent']
        contact_submission.telegram_notification_sent = notification_result['telegram_notification_sent']
        contact_submission.email_error = notification_result['email_error']
        contact_submission.telegram_error = notification_result['telegram_error']

        contact_submission.save(update_fields=[
            'owner_email_sent',
            'confirmation_email_sent',
            'telegram_notification_sent',
            'email_error',
            'telegram_error',
            'updated_at',
        ])
        status_message = 'Your message has been sent.'

        if notification_result['email_error'] or notification_result['telegram_error']:
            status_message = 'Your message was saved, but one or more owner alerts failed.'

        return JsonResponse({
            'ok': True,
            'message': status_message,
        })
    except Exception as exc:
        error_message = str(exc)
        contact_submission.email_error = error_message
        contact_submission.save(update_fields=['email_error', 'updated_at'])
        return JsonResponse({
            'ok': False,
            'message': f'Your message was saved, but email delivery failed: {error_message}',
            'errors': {},
        }, status=500)


@require_POST
def site_visit_notify_api(request):
    try:
        site_visit, is_new_visit = record_site_visit(request)
        result = {
            'email_sent': False,
            'telegram_sent': False,
        }

        if site_visit.is_active:
            result = send_site_visit_notifications(site_visit, get_active_profile(), is_new_visit)
    except (DatabaseError, OperationalError, ProgrammingError):
        return JsonResponse({'ok': False}, status=503)

    return JsonResponse({
        'ok': True,
        'site_visit_id': site_visit.id,
        'email_sent': result['email_sent'],
        'telegram_sent': result['telegram_sent'],
    })


@require_POST
def site_visit_duration_api(request):
    if not settings.TRACK_SITE_VISIT_DURATION:
        return JsonResponse({
            'ok': False,
            'tracking_enabled': False,
        })

    site_visit_id = request.POST.get('site_visit_id')
    duration_seconds = request.POST.get('duration_seconds')
    updated = add_site_visit_duration(site_visit_id, duration_seconds)

    return JsonResponse({
        'ok': updated,
    })


def profile_detail_api(request):
    profile = get_active_profile()

    if not profile:
        return JsonResponse({
            'name': f'Name: {NOT_ADDED}',
            'role': f'Role: {NOT_ADDED}',
            'email': '',
            'phone_number': '',
            'about_description': f'About: {NOT_ADDED}',
            'languages': [f'Languages: {NOT_ADDED}'],
            'location': f'Location: {NOT_ADDED}',
            'city': '',
            'state': '',
            'country': '',
            'profile_picture': None,
            'resume': None,
            'browser_tab_icon_text': 'KP',
            'browser_tab_animation_speed_ms': 1600,
            'browser_tab_title_frames': DEFAULT_BROWSER_TAB_FRAMES,
            'is_active': False,
        })

    return JsonResponse({
        'name': profile.name or f'Name: {NOT_ADDED}',
        'role': profile.role or f'Role: {NOT_ADDED}',
        'email': profile.email,
        'phone_number': profile.phone_number,
        'about_description': profile.about_description or f'About: {NOT_ADDED}',
        'languages': normalize_languages(profile.languages) or [f'Languages: {NOT_ADDED}'],
        'location': format_location(profile),
        'city': profile.city,
        'state': profile.state,
        'country': profile.country,
        'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
        'resume': profile.resume.url if profile.resume else None,
        'browser_tab_icon_text': profile.browser_tab_icon_text,
        'browser_tab_animation_speed_ms': profile.browser_tab_animation_speed_ms,
        'browser_tab_title_frames': profile.browser_tab_title_frames,
        'is_active': profile.is_active,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat(),
    })


def social_links_api(request):
    return JsonResponse({
        'social_links': build_social_links(),
    })


def page_not_found(request, exception=None):
    profile = get_active_profile()
    name = profile.name.strip() if profile and profile.name.strip() else 'Portfolio'
    page_title = 'Page Not Found'

    context = {
        'person': {
            'name': name,
            'footer_text': (
                profile.footer_text.strip()
                if profile and profile.footer_text.strip()
                else f'© {timezone.now().year} / {name} all rights reserved'
            ),
        },
        'social_links': build_social_links(),
        'current_year': timezone.now().year,
        'page_title': page_title,
        'hide_site_header': True,
        'hide_site_footer': True,
        'share_metadata': build_share_metadata(request, page_title, 'Page not found.'),
        'browser_tab_config': build_browser_tab_config(profile, page_title),
    }
    return render(request, '404.html', context, status=404)
