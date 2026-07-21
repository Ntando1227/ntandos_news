"""Configure Django administration for the news application."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Publisher, Article, Newsletter, ApprovedArticleLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Configure administration for custom user."""
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role and subscriptions', {
            'fields': (
                'role',
                'subscribed_publishers',
                'subscribed_journalists',
            )
        }),
    )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Configure administration for publisher."""
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configure administration for article."""
    list_display = ('title', 'author', 'publisher', 'approved', 'created_at')
    list_filter = ('approved', 'publisher', 'created_at')
    search_fields = ('title', 'content')


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Configure administration for newsletter."""
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'description')


@admin.register(ApprovedArticleLog)
class ApprovedArticleLogAdmin(admin.ModelAdmin):
    """Configure administration for approved article log."""
    list_display = ('title', 'author', 'publisher', 'approved_at')
    search_fields = ('title', 'author', 'publisher')
