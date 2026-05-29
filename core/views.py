from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.db.utils import DatabaseError, OperationalError, ProgrammingError
from django.db.models import Prefetch

from .models import Company, ExperienceRole, ProfileDetail, Skill, SkillCategory, SocialLink


NOT_ADDED = 'Not Added'


def get_active_profile():
    try:
        return ProfileDetail.objects.filter(is_active=True).order_by('-updated_at').first()
    except (DatabaseError, OperationalError, ProgrammingError):
        return None


def get_active_social_links():
    try:
        return SocialLink.objects.filter(is_active=True).exclude(url='').order_by('name')
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


def normalize_languages(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(',') if item.strip()]

    return []


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


def format_role_duration(role):
    start = f'{role.get_start_month_display()} {role.start_year}'
    end = (
        f'{role.get_end_month_display()} {role.end_year}'
        if role.end_month and role.end_year
        else 'Present'
    )
    return f'{start} - {end}'


def parse_description_points(description):
    points = []
    paragraphs = []

    for line in description.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        if cleaned_line.startswith('-'):
            points.append(cleaned_line.lstrip('-').strip())
        elif points:
            points[-1] = f'{points[-1]} {cleaned_line}'
        else:
            paragraphs.append(cleaned_line)

    return points, paragraphs


def build_companies():
    companies = []

    for company in get_active_companies():
        roles = []

        for role in company.roles.all():
            bullet_points, paragraphs = parse_description_points(role.description)
            preview_text = ' '.join(bullet_points or paragraphs)

            roles.append({
                'role': role.role,
                'timeframe': format_role_duration(role),
                'description': role.description.strip(),
                'preview': preview_text,
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
                'logo': skill.logo.url if skill.logo else skill.auto_logo_url,
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


class HomeView(View):
    template_name = 'core/home.html'

    def get(self, request, *args, **kwargs):
        profile = get_active_profile()
        profile_languages = normalize_languages(profile.languages) if profile else []
        name = profile.name.strip() if profile and profile.name.strip() else f'Name: {NOT_ADDED}'
        role = profile.role.strip() if profile and profile.role.strip() else f'Role: {NOT_ADDED}'
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
            'avatar': profile.profile_picture.url if profile and profile.profile_picture else '',
            'resume': profile.resume.url if profile and profile.resume else '',
            'fallback_avatar': 'images/avatar.jpg',
            'email': 'example@gmail.com',
            'location': location,
            'languages': profile_languages or [f'Languages: {NOT_ADDED}'],
        }

        social_links = build_social_links()
        skill_categories = build_skill_categories()
        companies = build_companies()
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
            'studies': {
                'title': 'Studies',
                'institutions': [
                    {
                        'name': 'University of Jakarta',
                        'description': 'Studied software engineering.',
                    },
                    {
                        'name': 'Build the Future',
                        'description': 'Studied online marketing and personal branding.',
                    },
                ],
            },
            'technical': {
                'title': 'Skills',
                'categories': skill_categories or fallback_skill_categories,
            },
        }

        context = {
            'person': person,
            'social_links': social_links,
            'about': about,
            'projects': [
                {
                    'title': 'Once UI Design System',
                    'description': 'A customizable design system built for fast, consistent product interfaces.',
                    'image': 'images/projects/project-01/cover-01.jpg',
                    'tags': ['Design System', 'UI Engineering'],
                },
                {
                    'title': 'Figma to Code Pipeline',
                    'description': 'A workflow that automates design handovers and speeds up production builds.',
                    'image': 'images/projects/project-01/cover-02.jpg',
                    'tags': ['Automation', 'Frontend'],
                },
            ],
            'current_year': timezone.now().year,
            'page_title': f"{person['name']} Portfolio",
        }
        return render(request, self.template_name, context)


def profile_detail_api(request):
    profile = get_active_profile()

    if not profile:
        return JsonResponse({
            'name': f'Name: {NOT_ADDED}',
            'role': f'Role: {NOT_ADDED}',
            'about_description': f'About: {NOT_ADDED}',
            'languages': [f'Languages: {NOT_ADDED}'],
            'location': f'Location: {NOT_ADDED}',
            'city': '',
            'state': '',
            'country': '',
            'profile_picture': None,
            'resume': None,
            'is_active': False,
        })

    return JsonResponse({
        'name': profile.name or f'Name: {NOT_ADDED}',
        'role': profile.role or f'Role: {NOT_ADDED}',
        'about_description': profile.about_description or f'About: {NOT_ADDED}',
        'languages': normalize_languages(profile.languages) or [f'Languages: {NOT_ADDED}'],
        'location': format_location(profile),
        'city': profile.city,
        'state': profile.state,
        'country': profile.country,
        'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
        'resume': profile.resume.url if profile.resume else None,
        'is_active': profile.is_active,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat(),
    })


def social_links_api(request):
    return JsonResponse({
        'social_links': build_social_links(),
    })
