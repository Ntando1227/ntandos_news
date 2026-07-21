"""Define template-based views for the news application."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ArticleForm, NewsletterForm, RegistrationForm
from .models import Article, CustomUser, Newsletter, Publisher
from .views import (
    email_approved_article,
    post_article_to_approved_endpoint,
)


def role_required(allowed_roles):
    """Handle role required."""
    def decorator(view_function):
        """Handle decorator."""
        @wraps(view_function)
        def wrapped_view(request, *args, **kwargs):
            """Handle wrapped view."""
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    'You do not have permission to access this page.',
                )
                return redirect('home')

            return view_function(request, *args, **kwargs)

        return wrapped_view

    return decorator


def home(request):
    """Handle home."""
    articles = Article.objects.filter(
        approved=True
    ).select_related(
        'author',
        'publisher',
    ).order_by(
        '-created_at'
    )

    newsletters = Newsletter.objects.all().select_related(
        'author'
    ).prefetch_related(
        'articles'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'newsapp/home.html',
        {
            'articles': articles,
            'newsletters': newsletters,
        },
    )


def register(request):
    """Handle register."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                'Your account was created successfully.',
            )

            return redirect('home')
    else:
        form = RegistrationForm()

    return render(
        request,
        'registration/register.html',
        {'form': form},
    )


def article_detail(request, article_id):
    """Handle article detail."""
    article = get_object_or_404(
        Article.objects.select_related(
            'author',
            'publisher',
        ),
        id=article_id,
    )

    if not article.approved:
        allowed = (
            request.user.is_authenticated
            and (
                request.user.role == 'editor'
                or article.author == request.user
            )
        )

        if not allowed:
            messages.error(
                request,
                'This article is not available.',
            )
            return redirect('home')

    return render(
        request,
        'newsapp/article_detail.html',
        {'article': article},
    )


@login_required
@role_required(['journalist'])
def article_create(request):
    """Handle article create."""
    if request.method == 'POST':
        form = ArticleForm(request.POST, user=request.user)

        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False
            article.save()

            messages.success(
                request,
                'Article submitted for editor approval.',
            )

            return redirect(
                'article_detail',
                article_id=article.id,
            )
    else:
        form = ArticleForm(user=request.user)

    return render(
        request,
        'newsapp/article_form.html',
        {
            'form': form,
            'page_title': 'Create Article',
        },
    )


@login_required
@role_required(['journalist', 'editor'])
def article_update(request, article_id):
    """Handle article update."""
    article = get_object_or_404(
        Article,
        id=article_id,
    )

    if (
        request.user.role == 'journalist'
        and article.author != request.user
    ):
        messages.error(
            request,
            'You can only edit your own articles.',
        )
        return redirect('home')

    if request.method == 'POST':
        form = ArticleForm(
            request.POST,
            instance=article,
            user=request.user,
        )

        if form.is_valid():
            updated_article = form.save(commit=False)

            if request.user.role == 'journalist':
                updated_article.approved = False

            updated_article.save()

            messages.success(
                request,
                'Article updated successfully.',
            )

            return redirect(
                'article_detail',
                article_id=article.id,
            )
    else:
        form = ArticleForm(instance=article, user=request.user)

    return render(
        request,
        'newsapp/article_form.html',
        {
            'form': form,
            'page_title': 'Edit Article',
        },
    )


@login_required
@role_required(['editor'])
def editor_review(request):
    """Handle editor review."""
    articles = Article.objects.filter(
        approved=False
    ).select_related(
        'author',
        'publisher',
    ).order_by(
        'created_at'
    )

    return render(
        request,
        'newsapp/editor_review.html',
        {'articles': articles},
    )


@login_required
@role_required(['editor'])
def approve_article(request, article_id):
    """Approve article."""
    article = get_object_or_404(
        Article.objects.select_related(
            'author',
            'publisher',
        ),
        id=article_id,
    )

    if request.method != 'POST':
        messages.error(
            request,
            'Articles can only be approved using the approval button.',
        )
        return redirect('editor_review')

    if article.approved:
        messages.warning(
            request,
            "This article has already been approved.",
        )
        return redirect("editor_review")

    if (
        article.publisher
        and not article.publisher.editors.filter(
            pk=request.user.pk
        ).exists()
    ):
        messages.error(
            request,
            (
                "You cannot approve this article because you are "
                "not assigned to its publisher."
            ),
        )
        return redirect("editor_review")

    article.approved = True
    article.save(update_fields=['approved'])

    try:
        emails_sent = email_approved_article(article)
    except Exception:
        emails_sent = 0

    endpoint_posted = post_article_to_approved_endpoint(
        request,
        article,
    )

    if endpoint_posted:
        messages.success(
            request,
            (
                f'Article approved successfully. '
                f'{emails_sent} subscriber email(s) were sent, '
                f'and the approval was logged through the API.'
            ),
        )
    else:
        messages.success(
            request,
            (
                f'Article approved successfully. '
                f'{emails_sent} subscriber email(s) were sent. '
                f'The approval was saved locally because the API '
                f'POST request could not be completed.'
            ),
        )

    return redirect('editor_review')


@login_required
@role_required(['journalist', 'editor'])
def newsletter_create(request):
    """Handle newsletter create."""
    if request.method == 'POST':
        form = NewsletterForm(request.POST, user=request.user)

        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()

            messages.success(
                request,
                'Newsletter created successfully.',
            )

            return redirect('home')
    else:
        form = NewsletterForm(user=request.user)

    return render(
        request,
        'newsapp/newsletter_form.html',
        {'form': form},
    )



@login_required
@role_required(['reader'])
def manage_subscriptions(request):
    """Handle manage subscriptions."""
    publishers = Publisher.objects.all().order_by('name')

    journalists = CustomUser.objects.filter(
        role='journalist'
    ).order_by(
        'username'
    )

    return render(
        request,
        'newsapp/manage_subscriptions.html',
        {
            'publishers': publishers,
            'journalists': journalists,
        },
    )


@login_required
@role_required(['reader'])
def subscribe_publisher(request, publisher_id):
    """Subscribe the reader to publisher."""
    publisher = get_object_or_404(
        Publisher,
        id=publisher_id,
    )

    if request.method == 'POST':
        request.user.subscribed_publishers.add(
            publisher
        )

        messages.success(
            request,
            f'You subscribed to {publisher.name}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def unsubscribe_publisher(request, publisher_id):
    """Unsubscribe the reader from publisher."""
    publisher = get_object_or_404(
        Publisher,
        id=publisher_id,
    )

    if request.method == 'POST':
        request.user.subscribed_publishers.remove(
            publisher
        )

        messages.success(
            request,
            f'You unsubscribed from {publisher.name}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def subscribe_journalist(request, journalist_id):
    """Subscribe the reader to journalist."""
    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role='journalist',
    )

    if request.method == 'POST':
        request.user.subscribed_journalists.add(
            journalist
        )

        messages.success(
            request,
            f'You subscribed to {journalist.username}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def unsubscribe_journalist(request, journalist_id):
    """Unsubscribe the reader from journalist."""
    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role='journalist',
    )

    if request.method == 'POST':
        request.user.subscribed_journalists.remove(
            journalist
        )

        messages.success(
            request,
            f'You unsubscribed from {journalist.username}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def subscribed_articles(request):
    """Handle subscribed articles."""
    subscribed_publishers = (
        request.user.subscribed_publishers.all()
    )

    subscribed_journalists = (
        request.user.subscribed_journalists.all()
    )

    from django.db.models import Q

    articles = Article.objects.filter(
        Q(publisher__in=subscribed_publishers)
        | Q(author__in=subscribed_journalists),
        approved=True,
    ).distinct().select_related(
        'author',
        'publisher',
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'newsapp/subscribed_articles.html',
        {'articles': articles},
    )

