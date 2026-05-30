from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.utils import DatabaseError, OperationalError, ProgrammingError
from django.template import Context, Template
from django.utils.html import escape, strip_tags

from .models import DynamicTemplate


OWNER_CONTACT_TEMPLATE_SLUG = 'contact-owner-notification'
VISITOR_CONFIRMATION_TEMPLATE_SLUG = 'contact-visitor-confirmation'


def get_dynamic_template(slug):
    try:
        return DynamicTemplate.objects.filter(slug=slug, is_active=True).first()
    except (DatabaseError, OperationalError, ProgrammingError):
        return None


def build_contact_email_context(contact_submission, profile):
    contact_subject = contact_submission.subject.strip() or 'Contact message'

    return {
        'contact': contact_submission,
        'profile': profile,
        'site_name': profile.name if profile and profile.name else 'Portfolio',
        'contact_subject': contact_subject,
    }


def render_template_content(slug, context_data, fallback_html):
    dynamic_template = get_dynamic_template(slug)
    source = dynamic_template.rich_enrichment if dynamic_template else fallback_html

    try:
        return Template(source).render(Context(context_data))
    except Exception:
        return Template(fallback_html).render(Context(context_data))


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


def send_contact_emails(contact_submission, profile):
    context_data = build_contact_email_context(contact_submission, profile)
    owner_subject = f'New contact message: {context_data["contact_subject"]}'
    visitor_subject = f'Thank you for reaching out to {context_data["site_name"]}'
    owner_fallback = """
<p>You received a new contact message from <strong>{{ contact.name }}</strong>.</p>
<p><strong>Email:</strong> {{ contact.email }}<br>
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

    owner_html = wrap_email_html(
        'New Contact Message',
        render_template_content(OWNER_CONTACT_TEMPLATE_SLUG, context_data, owner_fallback),
    )
    visitor_html = wrap_email_html(
        'Thank You For Reaching Out',
        render_template_content(VISITOR_CONFIRMATION_TEMPLATE_SLUG, context_data, visitor_fallback),
    )

    owner_sent = send_html_email(owner_subject, profile.email if profile else '', owner_html)
    confirmation_sent = send_html_email(visitor_subject, contact_submission.email, visitor_html)
    return owner_sent, confirmation_sent
