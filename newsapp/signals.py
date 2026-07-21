"""Define application signal handlers."""
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import CustomUser


ROLE_PERMISSIONS = {
    'reader': [
        'view_article',
        'view_newsletter',
    ],
    'editor': [
        'view_article',
        'change_article',
        'delete_article',
        'view_newsletter',
        'change_newsletter',
        'delete_newsletter',
    ],
    'journalist': [
        'add_article',
        'view_article',
        'change_article',
        'delete_article',
        'add_newsletter',
        'view_newsletter',
        'change_newsletter',
        'delete_newsletter',
    ],
}


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    """Create role groups."""
    if sender.name != 'newsapp':
        return

    for role, permission_codenames in ROLE_PERMISSIONS.items():
        group_name = role.capitalize()
        group, created = Group.objects.get_or_create(name=group_name)

        permissions = Permission.objects.filter(
            content_type__app_label='newsapp',
            codename__in=permission_codenames,
        )

        group.permissions.set(permissions)


@receiver(post_save, sender=CustomUser)
def assign_user_group(sender, instance, **kwargs):
    """Handle assign user group."""
    if instance.is_superuser:
        return

    group_name = instance.role.capitalize()
    group, created = Group.objects.get_or_create(name=group_name)

    instance.groups.clear()
    instance.groups.add(group)

    if instance.role != 'reader':
        instance.subscribed_publishers.clear()
        instance.subscribed_journalists.clear()
