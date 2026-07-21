"""Forms used by the Ntando's News web application."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Article, CustomUser, Newsletter, Publisher


class RegistrationForm(UserCreationForm):
    """Register a user with an email address and application role."""

    email = forms.EmailField(required=True)

    class Meta:
        """Configure the registration form model and fields."""

        model = CustomUser
        fields = [
            "username",
            "email",
            "role",
            "password1",
            "password2",
        ]


class ArticleForm(forms.ModelForm):
    """Create or update an article using permitted publishers."""

    class Meta:
        """Configure article form fields and widgets."""

        model = Article
        fields = [
            "title",
            "content",
            "publisher",
        ]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 10,
                    "placeholder": "Write the article content here.",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Limit publisher choices to the journalist's assignments."""

        super().__init__(*args, **kwargs)
        self.user = user

        if user and getattr(user, "role", None) == "journalist":
            self.fields["publisher"].queryset = Publisher.objects.filter(
                journalists=user
            ).order_by("name")
        else:
            self.fields["publisher"].queryset = Publisher.objects.none()

        self.fields["publisher"].required = False
        self.fields["publisher"].empty_label = "Independent article"

    def clean_publisher(self):
        """Reject publishers not assigned to the current journalist."""

        publisher = self.cleaned_data.get("publisher")

        if publisher is None:
            return None

        if not self.user or self.user.role != "journalist":
            raise ValidationError(
                "Only journalists can select a publisher."
            )

        if not publisher.journalists.filter(pk=self.user.pk).exists():
            raise ValidationError(
                "You are not assigned to this publisher."
            )

        return publisher


class NewsletterForm(forms.ModelForm):
    """Create or update a newsletter containing approved articles."""

    class Meta:
        """Configure newsletter form fields and widgets."""

        model = Newsletter
        fields = [
            "title",
            "description",
            "articles",
        ]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 5}
            ),
            "articles": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Limit newsletter articles according to the current user's role."""

        super().__init__(*args, **kwargs)
        self.user = user

        if user and user.role == "journalist":
            self.fields["articles"].queryset = Article.objects.filter(
                author=user,
                approved=True,
            ).order_by("-created_at")
        elif user and user.role == "editor":
            self.fields["articles"].queryset = Article.objects.filter(
                approved=True
            ).order_by("-created_at")
        else:
            self.fields["articles"].queryset = Article.objects.none()
