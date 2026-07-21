"""Database models for the Ntando's News application.

This module defines users, publishers, articles, newsletters,
and approved article records.
""""""Define database models for the news application."""
from django.db import models
from django.contrib.auth.models import AbstractUser


class Publisher(models.Model):
    """Represent publisher."""
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    editors = models.ManyToManyField(
        'CustomUser',
        blank=True,
        related_name='editor_publishers'
    )

    journalists = models.ManyToManyField(
        'CustomUser',
        blank=True,
        related_name='journalist_publishers'
    )

    def __str__(self):
        """Return a readable string representation."""
        return self.name


class CustomUser(AbstractUser):
    """Represent custom user."""
    ROLE_CHOICES = [
        ('reader', 'Reader'),
        ('journalist', 'Journalist'),
        ('editor', 'Editor'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='reader'
    )

    subscribed_publishers = models.ManyToManyField(
        Publisher,
        blank=True,
        related_name='subscribers'
    )

    subscribed_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='journalist_subscribers'
    )

    def __str__(self):
        """Return a readable string representation."""
        return self.username


class Article(models.Model):
    """Represent article."""
    title = models.CharField(max_length=200)
    content = models.TextField()

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='articles'
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        """Return a readable string representation."""
        return self.title


class Newsletter(models.Model):
    """Represent newsletter."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='newsletters'
    )

    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name='newsletters'
    )

    def __str__(self):
        """Return a readable string representation."""
        return self.title


class ApprovedArticleLog(models.Model):
    """Represent approved article log."""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    publisher = models.CharField(max_length=150, blank=True)
    approved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a readable string representation."""
        return self.title

