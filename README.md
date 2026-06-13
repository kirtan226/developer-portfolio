# Dynamic Developer Portfolio

A backend-controlled Django portfolio website. The portfolio content is managed from Django admin, so profile details, skills, work experience, education, projects, project screenshots, social links, resume, notifications, and visitor tracking can be updated without changing templates or redeploying code.

## 🌐 Live Links

- Live site with backend: [https://kirtanpatel2261.pythonanywhere.com/](https://kirtanpatel2261.pythonanywhere.com/)
- Demo preview without backend: [https://kirtan-portfolio.onrender.com/](https://kirtan-portfolio.onrender.com/)

## ✨ Features

- Dynamic profile section with name, role, location, languages, profile photo, resume, and animated browser tab settings.
- Typing effect for the role displayed under the name.
- Dynamic social links with platform icons.
- Dynamic skill categories and skills with uploaded logos, direct logo URLs, or Simple Icons fallback.
- Dynamic work experience grouped by company and roles.
- Dynamic education section.
- Dynamic project section with cover image, description bullets, technologies, screenshots, GitHub link, and live site link.
- Project detail modal with image carousel, technology badges, description, GitHub button, and live site button.
- Contact form with server-side validation and saved contact submissions.
- Owner email notification, visitor confirmation email, and Telegram notification support.
- Site visit tracking with IP, browser, OS, device type, referrer, location, visit count, first visit, last visit, and total duration.
- Dynamic email templates using CKEditor.
- Admin image crop workflows for profile photos, company logos, project covers, screenshots, and skill logos.
- Custom 404 page and share metadata.

## 🛠️ Tech Stack

- Python
- Django 6
- SQLite or PostgreSQL
- Django Admin
- Django Templates
- HTML, CSS, JavaScript
- Bootstrap Icons
- CKEditor
- Celery
- Redis
- Whitenoise
- Gunicorn
- python-dotenv

## 📁 Project Structure

```text
developer-portfolio/
  core/                         Main portfolio app
  developer_portfolio/          Django project settings and URLs
  media/                        Uploaded user/admin files
  static/                       Source static files
  staticfiles/                  Collected static files
  templates/                    Site templates
  db.sqlite3                    SQLite database when SERVER=live
  manage.py
  requirements.txt
  sample.env
```

## 🚀 Local Setup

1. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create `.env` from `sample.env`.

```powershell
copy sample.env .env
```

4. Update `.env` values for your local database and notifications.

5. Run migrations.

```powershell
python manage.py migrate
```

6. Create an admin user.

```powershell
python manage.py createsuperuser
```

7. Run the server.

```powershell
python manage.py runserver
```

8. Open the site.

```text
http://127.0.0.1:8000/
```

Admin URL depends on `ADMIN_URL` in `.env`. With the sample value:

```text
http://127.0.0.1:8000/admin/
```

## ⬇️ Project Pull and Setup Guidelines

Use these steps when setting up the project after cloning it from GitHub or pulling the latest changes.

### 1. Clone the Project

```powershell
git clone <your-repository-url>
cd developer-portfolio
```

### 2. Pull Latest Changes

If the project already exists locally:

```powershell
git pull origin main
```

Replace `main` with your active branch name if needed.

### 3. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Requirements

```powershell
pip install -r requirements.txt
```

### 5. Configure Environment

```powershell
copy sample.env .env
```

Then update `.env` values for `SECRET_KEY`, database, email, Telegram, and allowed hosts.

### 6. Apply Database Changes

```powershell
python manage.py migrate
```

Run this after every pull when new migrations are added.

### 7. Collect Static Files

```powershell
python manage.py collectstatic
```

Use this for deployment or when static files need to be refreshed.

### 8. Create Admin User

```powershell
python manage.py createsuperuser
```

### 9. Run the Project

```powershell
python manage.py runserver
```

### 10. Admin Data Entry Order

Recommended order after a fresh setup:

1. Add `Profile Detail`.
2. Add `Social Links`.
3. Add `Skill Categories` and `Skills`.
4. Add `Companies` and `Experience Roles`.
5. Add `Education`.
6. Add `Projects`, `Project Skills`, and `Project Screenshots`.
7. Add `Notification Settings`.
8. Add `Dynamic Templates` if custom email designs are needed.

## ⚙️ Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=change-this-secret-key
ADMIN_URL=admin/
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SERVER=local
TRACK_SITE_VISIT_DURATION=True
SITE_VISIT_ALERT_DELAY_SECONDS=10

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=StrongPassword123

DB_NAME=developer_portfolio
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432

EMAIL_HOST_USER=your-gmail-address@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

SEND_TELEGRAM_ALERTS=True
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
```

### 🔐 `.env` Details

`SECRET_KEY`: Django secret key. Use a strong value in production.

`ADMIN_URL`: Admin path. Example: `admin/`, `secure-admin/`.

`DEBUG`: Use `True` locally and `False` in production.

`ALLOWED_HOSTS`: Comma-separated domains/IPs allowed by Django.

`SERVER`: Controls database mode in this project.

- `SERVER=local` uses PostgreSQL with `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.
- `SERVER=live` uses SQLite at `db.sqlite3` and ignores the PostgreSQL values.

`TRACK_SITE_VISIT_DURATION`: Set to `False` to stop frequent duration API calls and duration database updates. Visit counts and site-visit notifications continue to work.

`SITE_VISIT_ALERT_DELAY_SECONDS`: Seconds to wait after page load before requesting site-visit email/Telegram alerts. Visitors who leave before the delay do not generate an alert.

`DJANGO_SUPERUSER_*`: Useful when creating a superuser with Django's non-interactive `createsuperuser --noinput`.

`EMAIL_HOST_USER`: Gmail address used as sender.

`EMAIL_HOST_PASSWORD`: Gmail app password. Do not use your normal Gmail password.

`SEND_TELEGRAM_ALERTS`: Global Telegram alert switch. Telegram sends only when this is `True` and the matching Notification Setting model's `telegram_notification` field is enabled.

`TELEGRAM_BOT_TOKEN`: Token from BotFather.

`TELEGRAM_CHAT_ID`: Telegram chat/user/group ID where notifications should be sent.

## 🧩 Admin Content Setup

After logging into Django admin, fill these sections.

### 👤 Profile Detail

Add one active profile.

Recommended fields:

- `name`
- `role`
- `email`
- `phone_number`
- `about_description`
- `footer_text`
- `languages` as JSON list, for example `["Gujarati", "Hindi", "English"]`
- `city`, `state`, `country`
- `profile_picture`
- `resume`
- `browser_tab_icon_text`, for example `KP`
- `browser_tab_animation_speed_ms`, for example `1600`
- `browser_tab_title_frames` as JSON list
- `is_active=True`

Example `browser_tab_title_frames`:

```json
[
  "class KirtanPatel(Developer):",
  "portfolio = KirtanPatel()",
  "def build_portfolio():",
  "print('Kirtan Patel')"
]
```

### 🔗 Social Links

Add links for platforms such as:

- GitHub
- LinkedIn
- Email
- Website
- Instagram
- Twitter / X
- YouTube
- Telegram
- WhatsApp

Use `display_order` to control order. Only active links with a URL are displayed.

### 🧠 Skills

Create `Skill Category` records such as:

- Backend
- Frontend
- Database
- Tools

Then add skills inside each category. A skill can use:

- uploaded logo
- direct `logo_url`
- automatic Simple Icons fallback based on skill name

### 💼 Experience

Create a `Company`, then add one or more `Experience Role` entries under it.

Role descriptions support bullet points when each line starts with `-`.

Example:

```text
- Built Django APIs for business workflows.
- Integrated payment and notification systems.
- Improved admin data management and reporting.
```

### 🎓 Education

Add education items with:

- education type
- institution name
- degree name
- board or university
- score
- start year
- passing year
- display order

### 🚧 Projects

Each project supports:

- `name`
- `cover_image`
- `description`
- `github_link`
- `site_link`
- `display_order`
- `is_active`
- project skills
- project screenshots

Project descriptions support bullet points when each line starts with `-`.

Example:

```text
- Built a dynamic Django portfolio where all sections are controlled from admin.
- Added project screenshots, skill badges, GitHub links, and live site links.
- Integrated contact form, email notifications, Telegram alerts, and visitor tracking.
```

`github_link`: shown as a GitHub button in project detail modal if filled.

`site_link`: shown as a live/visit site button in project detail modal if filled.

Project skills are added inline in the Project admin. Example project skills:

- Python
- Django
- PostgreSQL
- JavaScript
- Bootstrap
- Razorpay

Project screenshots are also added inline. Add a useful caption for each screenshot.

## 🧾 Dynamic Templates

Dynamic templates let you customize email HTML from Django admin without editing code.

Go to:

```text
Django Admin -> Dynamic Templates
```

Create templates with the exact slugs below.

### 🏷️ Required Slugs

`contact-owner-notification`

Used for the email sent to the portfolio owner when someone submits the contact form.

`contact-visitor-confirmation`

Used for the confirmation email sent to the visitor after contact form submission.

`site-visit-notification`

Used for the site visit notification email sent to the owner.

If a dynamic template is missing or inactive, the app uses built-in fallback email HTML.

### 🧮 Template Variables

Dynamic templates use Django template syntax.

For `contact-owner-notification` and `contact-visitor-confirmation`, available variables include:

```django
{{ title }}
{{ site_name }}
{{ server }}
{{ contact_subject }}
{{ contact.name }}
{{ contact.email }}
{{ contact.phone_number }}
{{ contact.subject }}
{{ contact.message }}
{{ profile.name }}
{{ profile.email }}
{{ profile.role }}
```

For `site-visit-notification`, available variables include:

```django
{{ title }}
{{ status }}
{{ server }}
{{ ip_address }}
{{ country }}
{{ state }}
{{ city }}
{{ browser }}
{{ operating_system }}
{{ device_type }}
{{ visit_count }}
{{ total_time }}
{{ first_visited_at }}
{{ last_visited_at }}
{{ referrer_url }}
{{ user_agent }}
```

### 📩 Example Contact Owner Template

Slug:

```text
contact-owner-notification
```

Rich enrichment:

```html
<h2>New contact message</h2>
<p><strong>Server:</strong> {{ server }}</p>
<p><strong>Name:</strong> {{ contact.name }}</p>
<p><strong>Email:</strong> {{ contact.email }}</p>
<p><strong>Subject:</strong> {{ contact_subject }}</p>
<p><strong>Message:</strong></p>
<p>{{ contact.message|linebreaksbr }}</p>
```

### ✅ Example Visitor Confirmation Template

Slug:

```text
contact-visitor-confirmation
```

Rich enrichment:

```html
<h2>Thanks for reaching out</h2>
<p>Hi {{ contact.name }},</p>
<p>I have received your message and will get back to you soon.</p>
<p><strong>Your subject:</strong> {{ contact_subject }}</p>
```

### 👁️ Example Site Visit Template

Slug:

```text
site-visit-notification
```

Rich enrichment:

```html
<h2>{{ status }} on your portfolio</h2>
<p><strong>Server:</strong> {{ server }}</p>
<p><strong>IP:</strong> {{ ip_address }}</p>
<p><strong>Location:</strong> {{ city }}, {{ state }}, {{ country }}</p>
<p><strong>Browser:</strong> {{ browser }}</p>
<p><strong>Device:</strong> {{ device_type }}</p>
<p><strong>Visit count:</strong> {{ visit_count }}</p>
<p><strong>Total time:</strong> {{ total_time }}</p>
<p><strong>Referrer:</strong> {{ referrer_url }}</p>
```

## 🔔 Notification Setup

Notifications are controlled by both `.env` values and `Notification Setting` records in admin.

### 📬 Contact Notifications

To receive owner alerts when someone submits the contact form:

1. Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`.
2. Add an active `Profile Detail` with your owner email in `email`.
3. In admin, create or update `Notification Setting`.
4. Select `Contact Us Notification`.
5. Enable `email_notification` if you want owner email alerts.
6. Enable `telegram_notification` if you want Telegram alerts.
7. Keep `is_active=True`.

Important: the visitor confirmation email is sent to the visitor after contact form submission. Owner email/Telegram alerts depend on the `Contact Us Notification` setting.

### 👁️ Site Visit Notifications

To receive alerts when someone visits the portfolio:

1. Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` for email alerts.
2. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` for Telegram alerts.
3. Add an active `Profile Detail` with owner email.
4. In admin, create or update `Notification Setting`.
5. Select `Site Visit Notification`.
6. Enable `email_notification` and/or `telegram_notification`.
7. Keep `is_active=True`.

Site visit location is detected from public IP using `ipapi.co`. Localhost/private IPs do not return city/state/country.

### 💬 Telegram Setup

1. Open Telegram and message `@BotFather`.
2. Create a bot and copy the bot token.
3. Send a message to your bot.
4. Get your chat ID using a Telegram bot/API helper.
5. Add values to `.env`.

```env
TELEGRAM_BOT_TOKEN=123456789:your-token
TELEGRAM_CHAT_ID=123456789
```

### 📧 Gmail SMTP Setup

1. Enable 2-step verification on your Google account.
2. Create a Gmail app password.
3. Add it to `.env`.

```env
EMAIL_HOST_USER=your-gmail-address@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
```

## 📝 Contact Form Limits

The contact form validates these limits:

- name: 24 characters
- email: 35 characters
- phone number: 30 characters
- subject: 55 characters
- message: 355 characters

## 📊 Site Visit Tracking

The app records:

- IP address
- browser name and version
- operating system
- device type
- user agent
- referrer URL
- country, state, city when available
- visit count
- first visited time
- last visited time
- total duration seconds

Set `TRACK_SITE_VISIT_DURATION=False` in `.env` to disable only total-duration tracking. The visit count and site-visit email/Telegram notifications continue to work.

If you want to stop notifications for a visitor/IP, open `User Site Visits` in admin and set `is_active=False`.

## 🖼️ Static and Media Files

Collect static files for deployment:

```powershell
python manage.py collectstatic
```

Uploaded files are stored under `media/`.

Static source files are stored under `static/`.

Collected files are stored under `staticfiles/`.

## ⏱️ Celery and Redis

The project includes Celery and django-celery-beat configuration.

Redis is expected at:

```text
redis://127.0.0.1:6379/0
```

Start a worker when background tasks are needed:

```powershell
celery -A developer_portfolio worker -l info
```

Start beat if scheduled tasks are used:

```powershell
celery -A developer_portfolio beat -l info
```

## 🧰 Useful Commands

Run checks:

```powershell
python manage.py check
```

Create migrations:

```powershell
python manage.py makemigrations
```

Apply migrations:

```powershell
python manage.py migrate
```

Create superuser:

```powershell
python manage.py createsuperuser
```

Collect static:

```powershell
python manage.py collectstatic
```

Run local server:

```powershell
python manage.py runserver
```

## 🚢 Deployment Notes

- Set `DEBUG=False`.
- Set a strong `SECRET_KEY`.
- Set `ALLOWED_HOSTS` to your production domain.
- Set `ADMIN_URL` to a non-default admin path if desired.
- Configure email and Telegram variables only if notifications are needed.
- Run `python manage.py migrate`.
- Run `python manage.py collectstatic`.
- Serve static files through Whitenoise or your web server.
- Make sure media uploads are persisted.

## 📌 Notes

- `site_link` on projects is optional. If it is empty, the live site button is hidden.
- `github_link` on projects is optional. If it is empty, the GitHub button is hidden.
- Dynamic templates are optional because fallback templates are built into the code.
- The app currently uses CKEditor 4 through `django-ckeditor`; Django checks may show a CKEditor support/security warning from the package.
