import ipaddress
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import F
from django.db.utils import DatabaseError, OperationalError, ProgrammingError
from django.template import Context, Template
from django.utils import timezone
from django.utils.html import escape, strip_tags

from .models import DynamicTemplate, NotificationSetting, UserSiteVisit


OWNER_CONTACT_TEMPLATE_SLUG = 'contact-owner-notification'
VISITOR_CONFIRMATION_TEMPLATE_SLUG = 'contact-visitor-confirmation'
SITE_VISIT_TEMPLATE_SLUG = 'site-visit-notification'
TELEGRAM_TIMEOUT_SECONDS = 10
TRACKED_DURATION_MAX_SECONDS = 3600
IP_LOCATION_TIMEOUT_SECONDS = 3


def get_dynamic_template(slug):
    try:
        return DynamicTemplate.objects.filter(slug=slug, is_active=True).first()
    except (DatabaseError, OperationalError, ProgrammingError):
        return None


def get_notification_setting(notification_type):
    try:
        return NotificationSetting.objects.filter(
            notification_type=notification_type,
            is_active=True,
        ).first()
    except (DatabaseError, OperationalError, ProgrammingError):
        return None


def build_contact_email_context(contact_submission, profile):
    contact_subject = contact_submission.subject.strip() or 'Contact message'

    return {
        'contact': contact_submission,
        'profile': profile,
        'site_name': profile.name if profile and profile.name else 'Portfolio',
        'contact_subject': contact_subject,
        'server': get_server_display(),
    }


def normalize_template_tag_entities(template_source):
    def decode_tag(match):
        return (
            match.group(0)
            .replace('&quot;', '"')
            .replace('&#34;', '"')
            .replace('&#x27;', "'")
            .replace('&#39;', "'")
        )

    return re.sub(r'({[{%].*?[}%]})', decode_tag, template_source, flags=re.DOTALL)


def render_template_content(slug, context_data, fallback_html, fallback_title=None):
    dynamic_template = get_dynamic_template(slug)

    if dynamic_template:
        try:
            template_source = normalize_template_tag_entities(dynamic_template.rich_enrichment)
            return Template(template_source).render(Context(context_data))
        except Exception:
            pass

    fallback_content = Template(fallback_html).render(Context(context_data))
    if fallback_title:
        return wrap_email_html(fallback_title, fallback_content)

    return fallback_content


def get_server_display():
    return getattr(settings, 'SERVER_DISPLAY', getattr(settings, 'SERVER', 'local')).upper()


def wrap_email_html(title, body_html):
    return f"""
<!doctype html>
<html>
<body style="margin:0;background:#090b0d;color:#f3f7f8;font-family:Inter,Arial,sans-serif;">
    <div style="padding:32px 16px;background:#090b0d;">
        <div style="max-width:680px;margin:0 auto;border:1px solid rgba(255,255,255,0.12);border-radius:16px;background:#181d21;padding:28px;">
            <h1 style="margin:0 0 20px;color:#f3f7f8;font-size:28px;line-height:1.15;">{escape(title)}</h1>
            <div style="color:#dce5e8;font-size:15px;line-height:1.7;">
                {body_html}
            </div>
        </div>
    </div>
</body>
</html>
"""


def send_html_email(subject, to_email, html_body):
    if not to_email:
        return False

    email = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send()
    return True


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')

    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR', '')


def parse_browser_details(user_agent):
    details = {
        'browser_name': 'Unknown',
        'browser_version': '',
        'operating_system': 'Unknown',
        'device_type': 'Desktop',
    }

    browser_patterns = [
        ('Edge', r'Edg/([\d.]+)'),
        ('Chrome', r'Chrome/([\d.]+)'),
        ('Firefox', r'Firefox/([\d.]+)'),
        ('Safari', r'Version/([\d.]+).*Safari'),
        ('Opera', r'OPR/([\d.]+)'),
    ]

    for browser_name, pattern in browser_patterns:
        match = re.search(pattern, user_agent)
        if match:
            details['browser_name'] = browser_name
            details['browser_version'] = match.group(1)
            break

    if 'Windows' in user_agent:
        details['operating_system'] = 'Windows'
    elif 'Android' in user_agent:
        details['operating_system'] = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        details['operating_system'] = 'iOS'
    elif 'Mac OS X' in user_agent:
        details['operating_system'] = 'macOS'
    elif 'Linux' in user_agent:
        details['operating_system'] = 'Linux'

    if 'Mobi' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
        details['device_type'] = 'Mobile'
    elif 'iPad' in user_agent or 'Tablet' in user_agent:
        details['device_type'] = 'Tablet'

    return details


def get_ip_location(ip_address):
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError:
        return {
            'country': '',
            'state': '',
            'city': '',
        }

    if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
        return {
            'country': '',
            'state': '',
            'city': '',
        }

    url = f'https://ipapi.co/{ip_address}/json/'

    try:
        with urlopen(url, timeout=IP_LOCATION_TIMEOUT_SECONDS) as response:
            response_body = response.read().decode('utf-8')

        result = json.loads(response_body)
    except Exception:
        return {
            'country': '',
            'state': '',
            'city': '',
        }

    return {
        'country': result.get('country_name', '') or '',
        'state': result.get('region', '') or '',
        'city': result.get('city', '') or '',
    }


def record_site_visit(request):
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referrer_url = request.META.get('HTTP_REFERER', '')
    browser_details = parse_browser_details(user_agent)
    location = get_ip_location(ip_address)
    now = timezone.now()
    muted_ip_exists = UserSiteVisit.objects.filter(
        ip_address=ip_address,
        is_active=False,
    ).exists()

    site_visit, created = UserSiteVisit.objects.get_or_create(
        ip_address=ip_address,
        browser_name=browser_details['browser_name'],
        defaults={
            'browser_version': browser_details['browser_version'],
            'operating_system': browser_details['operating_system'],
            'device_type': browser_details['device_type'],
            'user_agent': user_agent,
            'referrer_url': referrer_url[:500],
            'country': location['country'],
            'state': location['state'],
            'city': location['city'],
            'is_active': not muted_ip_exists,
            'first_visited_at': now,
            'last_visited_at': now,
        },
    )

    if not created:
        site_visit.browser_version = browser_details['browser_version']
        site_visit.operating_system = browser_details['operating_system']
        site_visit.device_type = browser_details['device_type']
        site_visit.user_agent = user_agent
        if referrer_url:
            site_visit.referrer_url = referrer_url[:500]
        if location['country'] or location['state'] or location['city']:
            site_visit.country = location['country']
            site_visit.state = location['state']
            site_visit.city = location['city']
        if muted_ip_exists and site_visit.is_active:
            site_visit.is_active = False
        site_visit.visit_count = F('visit_count') + 1
        site_visit.last_visited_at = now
        site_visit.save(update_fields=[
            'browser_version',
            'operating_system',
            'device_type',
            'user_agent',
            'referrer_url',
            'country',
            'state',
            'city',
            'is_active',
            'visit_count',
            'last_visited_at',
            'updated_at',
        ])
        site_visit.refresh_from_db()

    return site_visit, created


def add_site_visit_duration(site_visit_id, duration_seconds):
    try:
        duration_seconds = int(duration_seconds)
    except (TypeError, ValueError):
        return False

    if duration_seconds <= 0:
        return False

    duration_seconds = min(duration_seconds, TRACKED_DURATION_MAX_SECONDS)

    return UserSiteVisit.objects.filter(id=site_visit_id).update(
        total_duration_seconds=F('total_duration_seconds') + duration_seconds,
        updated_at=timezone.now(),
    ) > 0


def format_duration(seconds):
    minutes, seconds = divmod(int(seconds or 0), 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f'{hours}h {minutes}m {seconds}s'

    if minutes:
        return f'{minutes}m {seconds}s'

    return f'{seconds}s'


def send_telegram_notification(message):
    if not settings.SEND_TELEGRAM_ALERTS:
        return False

    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        return False

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = urlencode({
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true',
    }).encode('utf-8')
    request = Request(url, data=payload, method='POST')

    with urlopen(request, timeout=TELEGRAM_TIMEOUT_SECONDS) as response:
        response_body = response.read().decode('utf-8')

    result = json.loads(response_body)
    if not result.get('ok'):
        description = result.get('description', 'Telegram API returned an error.')
        raise RuntimeError(description)

    return True


def build_contact_telegram_message(contact_submission):
    created_at = timezone.localtime(contact_submission.created_at).strftime('%d %b %Y, %I:%M %p')
    lines = [
        '🔔 <b>New Contact Message</b>',
        '',
        f'🖥️ <b>Server:</b> {escape(get_server_display())}',
        f'👤 <b>Name:</b> {escape(contact_submission.name)}',
        f'📧 <b>Email:</b> {escape(contact_submission.email)}',
        f'📝 <b>Subject:</b> {escape(contact_submission.subject)}',
    ]

    if contact_submission.phone_number:
        lines.append(f'📱 <b>Phone:</b> {escape(contact_submission.phone_number)}')

    lines.extend([
        '',
        '💬 <b>Message</b>',
        escape(contact_submission.message),
        '',
        f'🕒 <b>Submitted:</b> {escape(created_at)}',
    ])
    return '\n'.join(lines)


def build_site_visit_telegram_message(site_visit, is_new_visit):
    visited_at = timezone.localtime(site_visit.last_visited_at).strftime('%d %b %Y, %I:%M %p')
    first_visited_at = timezone.localtime(site_visit.first_visited_at).strftime('%d %b %Y, %I:%M %p')
    status = 'New Visitor' if is_new_visit else 'Returning Visitor'
    server_display = get_server_display()
    lines = [
        f'👁️ <b>{escape(status)}</b>',
        '',
        f'🖥️ <b>Server:</b> {escape(server_display)}',
        f'🌐 <b>IP:</b> {escape(site_visit.ip_address)}',
        f'📍 <b>Country:</b> {escape(site_visit.country or "Not available")}',
        f'🏙️ <b>State:</b> {escape(site_visit.state or "Not available")}',
        f'🏢 <b>City:</b> {escape(site_visit.city or "Not available")}',
        f'🧭 <b>Browser:</b> {escape(site_visit.browser_name)} {escape(site_visit.browser_version)}'.strip(),
        f'💻 <b>OS:</b> {escape(site_visit.operating_system)}',
        f'📱 <b>Device:</b> {escape(site_visit.device_type)}',
        f'🔢 <b>Visit Count:</b> {site_visit.visit_count}',
        f'⏱️ <b>Total Time:</b> {escape(format_duration(site_visit.total_duration_seconds))}',
        f'🕒 <b>First Visit:</b> {escape(first_visited_at)}',
        f'🔁 <b>Last Visit:</b> {escape(visited_at)}',
    ]

    if site_visit.referrer_url:
        lines.extend([
            '',
            f'↩️ <b>Referrer:</b> {escape(site_visit.referrer_url)}',
        ])

    return '\n'.join(lines)


def build_site_visit_email_context(site_visit, is_new_visit):
    visited_at = timezone.localtime(site_visit.last_visited_at).strftime('%d %b %Y, %I:%M %p')
    first_visited_at = timezone.localtime(site_visit.first_visited_at).strftime('%d %b %Y, %I:%M %p')
    status = 'New visitor' if is_new_visit else 'Returning visitor'

    return {
        'site_visit': site_visit,
        'status': status,
        'server': get_server_display(),
        'ip_address': site_visit.ip_address,
        'country': site_visit.country or 'Not available',
        'state': site_visit.state or 'Not available',
        'city': site_visit.city or 'Not available',
        'browser': f'{site_visit.browser_name} {site_visit.browser_version}'.strip(),
        'operating_system': site_visit.operating_system,
        'device_type': site_visit.device_type,
        'visit_count': site_visit.visit_count,
        'total_time': format_duration(site_visit.total_duration_seconds),
        'first_visited_at': first_visited_at,
        'last_visited_at': visited_at,
        'referrer_url': site_visit.referrer_url or 'Direct visit',
        'user_agent': site_visit.user_agent,
    }


def build_site_visit_email(site_visit, is_new_visit):
    context_data = build_site_visit_email_context(site_visit, is_new_visit)
    subject = f'{context_data["status"]} on your portfolio [{context_data["server"]}]'
    context_data['title'] = 'Site Visit Notification'
    fallback = """
<div style="border:1px solid rgba(255,255,255,0.10);border-radius:12px;background:#101417;padding:18px;margin:0 0 18px;">
    <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#89e3c8;margin:0 0 8px;">{{ server }} Server</div>
    <p style="margin:0;color:#f3f7f8;font-size:18px;line-height:1.4;"><strong>{{ status }}</strong> visited your portfolio.</p>
</div>

<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;margin:0 0 18px;">
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;width:38%;">IP address</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ ip_address }}</td>
    </tr>
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;">Location</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ city }}, {{ state }}, {{ country }}</td>
    </tr>
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;">Browser</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ browser }}</td>
    </tr>
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;">Device</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ device_type }} / {{ operating_system }}</td>
    </tr>
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;">Visits</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ visit_count }} total, {{ total_time }} tracked</td>
    </tr>
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;">First visit</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ first_visited_at }}</td>
    </tr>
    <tr>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#101417;color:#9fb0b6;">Last visit</td>
        <td style="padding:12px 14px;border:1px solid rgba(255,255,255,0.10);background:#141a1e;color:#f3f7f8;">{{ last_visited_at }}</td>
    </tr>
</table>

<p style="margin:0 0 12px;"><strong>Referrer:</strong> {{ referrer_url }}</p>
<p style="margin:0;"><strong>User agent:</strong><br>{{ user_agent }}</p>
"""
    body = render_template_content(
        SITE_VISIT_TEMPLATE_SLUG,
        context_data,
        fallback,
        fallback_title='Site Visit Notification',
    )
    return subject, body


def build_contact_email_bodies(contact_submission, profile):
    context_data = build_contact_email_context(contact_submission, profile)
    owner_subject = f'New contact message: {context_data["contact_subject"]}'
    visitor_subject = f'Thank you for reaching out to {context_data["site_name"]}'
    owner_context = {
        **context_data,
        'title': 'New Contact Message',
    }
    visitor_context = {
        **context_data,
        'title': 'Thank You For Reaching Out',
    }
    owner_fallback = """
<p>You received a new contact message from <strong>{{ contact.name }}</strong>.</p>
<p><strong>Server:</strong> {{ server }}<br>
<strong>Email:</strong> {{ contact.email }}<br>
<strong>Subject:</strong> {{ contact_subject }}</p>
<p><strong>Message</strong></p>
<p>{{ contact.message|linebreaksbr }}</p>
"""
    visitor_fallback = """
<p>Hi {{ contact.name }},</p>
<p>Thank you for reaching out. I have received your message and will read it soon.</p>
<p><strong>Your submitted details</strong></p>
<p><strong>Email:</strong> {{ contact.email }}<br>
<strong>Subject:</strong> {{ contact_subject }}</p>
<p>{{ contact.message|linebreaksbr }}</p>
"""

    owner_html = render_template_content(
        OWNER_CONTACT_TEMPLATE_SLUG,
        owner_context,
        owner_fallback,
        fallback_title='New Contact Message',
    )
    visitor_html = render_template_content(
        VISITOR_CONFIRMATION_TEMPLATE_SLUG,
        visitor_context,
        visitor_fallback,
        fallback_title='Thank You For Reaching Out',
    )
    return owner_subject, owner_html, visitor_subject, visitor_html


def send_contact_owner_email(contact_submission, profile):
    owner_subject, owner_html, _, _ = build_contact_email_bodies(contact_submission, profile)
    return send_html_email(owner_subject, profile.email if profile else '', owner_html)


def send_contact_confirmation_email(contact_submission, profile):
    _, _, visitor_subject, visitor_html = build_contact_email_bodies(contact_submission, profile)
    return send_html_email(visitor_subject, contact_submission.email, visitor_html)


def send_contact_telegram_notification(contact_submission):
    return send_telegram_notification(build_contact_telegram_message(contact_submission))


def send_contact_notifications(contact_submission, profile):
    notification_setting = get_notification_setting(NotificationSetting.NotificationType.CONTACT_US)
    owner_sent = False
    telegram_sent = False
    email_error = ''
    telegram_error = ''

    if notification_setting and notification_setting.email_notification:
        try:
            owner_sent = send_contact_owner_email(contact_submission, profile)
            if not owner_sent:
                email_error = 'Profile email is not configured.'
        except Exception as exc:
            email_error = str(exc)

    telegram_enabled = bool(
        settings.SEND_TELEGRAM_ALERTS
        and notification_setting
        and notification_setting.telegram_notification
    )

    if telegram_enabled:
        try:
            telegram_sent = send_contact_telegram_notification(contact_submission)
            if not telegram_sent:
                telegram_error = 'Telegram bot token or chat ID is not configured.'
        except Exception as exc:
            telegram_error = str(exc)

    confirmation_sent = send_contact_confirmation_email(contact_submission, profile)

    return {
        'owner_email_sent': owner_sent,
        'confirmation_email_sent': confirmation_sent,
        'telegram_notification_sent': telegram_sent,
        'email_error': email_error,
        'telegram_error': telegram_error,
        'email_enabled': bool(notification_setting and notification_setting.email_notification),
        'telegram_enabled': telegram_enabled,
    }


def send_site_visit_notifications(site_visit, profile, is_new_visit):
    notification_setting = get_notification_setting(NotificationSetting.NotificationType.SITE_VISIT)
    result = {
        'email_sent': False,
        'telegram_sent': False,
        'email_error': '',
        'telegram_error': '',
    }

    if notification_setting and notification_setting.email_notification:
        try:
            subject, html_body = build_site_visit_email(site_visit, is_new_visit)
            result['email_sent'] = send_html_email(subject, profile.email if profile else '', html_body)
            if not result['email_sent']:
                result['email_error'] = 'Profile email is not configured.'
        except Exception as exc:
            result['email_error'] = str(exc)

    if (
        settings.SEND_TELEGRAM_ALERTS
        and notification_setting
        and notification_setting.telegram_notification
    ):
        try:
            result['telegram_sent'] = send_telegram_notification(
                build_site_visit_telegram_message(site_visit, is_new_visit),
            )
            if not result['telegram_sent']:
                result['telegram_error'] = 'Telegram bot token or chat ID is not configured.'
        except Exception as exc:
            result['telegram_error'] = str(exc)

    return result


def send_contact_emails(contact_submission, profile):
    owner_subject, owner_html, visitor_subject, visitor_html = build_contact_email_bodies(
        contact_submission,
        profile,
    )
    owner_sent = send_html_email(owner_subject, profile.email if profile else '', owner_html)
    confirmation_sent = send_html_email(visitor_subject, contact_submission.email, visitor_html)
    return owner_sent, confirmation_sent
