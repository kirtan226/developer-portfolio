from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.db.utils import DatabaseError, OperationalError, ProgrammingError

from .models import ProfileDetail, SocialLink


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
            'fallback_avatar': 'images/avatar.jpg',
            'email': 'example@gmail.com',
            'location': location,
            'languages': profile_languages or [f'Languages: {NOT_ADDED}'],
        }

        social_links = build_social_links()

        about = {
            'intro': {
                'title': 'Introduction',
                'description': about_description,
            },
            'work': {
                'title': 'Experience',
                'experiences': [
                    {
                        'company': 'FLY',
                        'timeframe': '2022 - Present',
                        'role': 'Senior Design Engineer',
                        'achievements': [
                            'Redesigned the UI/UX for the FLY platform, resulting in a 20% increase in user engagement and 30% faster load times.',
                            'Spearheaded the integration of AI tools into design workflows, enabling designers to iterate 50% faster.',
                        ],
                        'images': [
                            {
                                'src': 'images/projects/project-01/cover-01.jpg',
                                'alt': 'Once UI project cover',
                            },
                        ],
                    },
                    {
                        'company': 'Creativ3',
                        'timeframe': '2018 - 2022',
                        'role': 'Lead Designer',
                        'achievements': [
                            'Developed a design system that unified the brand across multiple platforms, improving design consistency by 40%.',
                            'Led a cross-functional team to launch a new product line, contributing to a 15% increase in overall company revenue.',
                        ],
                        'images': [],
                    },
                ],
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
                'skills': [
                    {
                        'title': 'Figma',
                        'description': 'Able to prototype in Figma with Once UI with unnatural speed.',
                        'tags': ['Figma'],
                        'images': [
                            {
                                'src': 'images/projects/project-01/cover-02.jpg',
                                'alt': 'Figma project preview',
                            },
                            {
                                'src': 'images/projects/project-01/cover-03.jpg',
                                'alt': 'Design system preview',
                            },
                        ],
                    },
                    {
                        'title': 'Next.js',
                        'description': 'Building next generation apps with Next.js, Once UI, and Supabase.',
                        'tags': ['JavaScript', 'Next.js', 'Supabase'],
                        'images': [
                            {
                                'src': 'images/projects/project-01/cover-04.jpg',
                                'alt': 'Application preview',
                            },
                        ],
                    },
                ],
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
        'is_active': profile.is_active,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat(),
    })


def social_links_api(request):
    return JsonResponse({
        'social_links': build_social_links(),
    })
