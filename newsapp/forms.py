from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, CustomUser, Newsletter, Publisher


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'role',
            'password1',
            'password2',
        ]


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'title',
            'content',
            'publisher',
        ]
        widgets = {
            'content': forms.Textarea(
                attrs={'rows': 10}
            ),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = [
            'title',
            'description',
            'articles',
        ]
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 5}
            ),
            'articles': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)

        if author and author.role == 'journalist':
            self.fields['articles'].queryset = Article.objects.filter(
                author=author,
                approved=True,
            )


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = [
            'name',
            'description',
            'journalists',
            'editors',
        ]
        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 5}
            ),
            'journalists': forms.CheckboxSelectMultiple(),
            'editors': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['journalists'].queryset = CustomUser.objects.filter(
            role='journalist'
        ).order_by('username')

        self.fields['editors'].queryset = CustomUser.objects.filter(
            role='editor'
        ).order_by('username')
