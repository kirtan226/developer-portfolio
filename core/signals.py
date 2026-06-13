from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_keys import HOME_CONTEXT_CACHE_KEY
from .models import (
    Company,
    Education,
    ExperienceRole,
    ProfileDetail,
    Project,
    ProjectScreenshot,
    ProjectSkill,
    Skill,
    SkillCategory,
    SocialLink,
)


HOME_CONTEXT_MODELS = (
    ProfileDetail,
    SocialLink,
    Company,
    ExperienceRole,
    SkillCategory,
    Skill,
    Project,
    ProjectSkill,
    ProjectScreenshot,
    Education,
)


@receiver(post_save)
@receiver(post_delete)
def clear_home_context_cache(sender, **kwargs):
    if sender in HOME_CONTEXT_MODELS:
        cache.delete(HOME_CONTEXT_CACHE_KEY)
