"""Web views for the Ntando's News application."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ArticleForm,
    NewsletterForm,
    PublisherForm,
    RegistrationForm,
)
from .models import Article, CustomUser, Newsletter, Publisher
from .views import (
    email_approved_article,
    post_article_to_approved_endpoint,
)


def role_required(allowed_roles):
    """Create a decorator that restricts a view to selected user roles."""
    def decorator(view_function):
        """Provide the application behaviour implemented by decorator."""
        @wraps(view_function)
        def wrapped_view(request, *args, **kwargs):
            """Provide the application behaviour implemented by wrapped_view."""
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
    """Display approved articles and newsletters on the homepage."""
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
    """Register and authenticate a new user."""
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


@login_required
@role_required(['journalist', 'editor'])
def dashboard(request):
    """Display content-management tools for journalists and editors."""
    if request.user.role == 'journalist':
        articles = Article.objects.filter(
            author=request.user
        ).select_related(
            'publisher'
        ).order_by(
            '-created_at'
        )

        newsletters = Newsletter.objects.filter(
            author=request.user
        ).prefetch_related(
            'articles'
        ).order_by(
            '-created_at'
        )
    else:
        articles = Article.objects.all().select_related(
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
        'newsapp/dashboard.html',
        {
            'articles': articles,
            'newsletters': newsletters,
        },
    )


def article_detail(request, article_id):
    """Display an article when the current user has permission."""
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
    """Allow a journalist to create an article."""
    if request.method == 'POST':
        form = ArticleForm(request.POST)

        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False
            article.save()

            messages.success(
                request,
                'Article submitted for editor approval.',
            )

            return redirect('dashboard')
    else:
        form = ArticleForm()

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
    """Allow an authorised user to update an article."""
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
        return redirect('dashboard')

    if request.method == 'POST':
        form = ArticleForm(
            request.POST,
            instance=article,
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

            return redirect('dashboard')
    else:
        form = ArticleForm(instance=article)

    return render(
        request,
        'newsapp/article_form.html',
        {
            'form': form,
            'page_title': 'Edit Article',
        },
    )


@login_required
@role_required(['journalist', 'editor'])
def article_delete(request, article_id):
    """Allow an authorised user to delete an article."""
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
            'You can only delete your own articles.',
        )
        return redirect('dashboard')

    if request.method == 'POST':
        title = article.title
        article.delete()

        messages.success(
            request,
            f'Article "{title}" was deleted successfully.',
        )

        return redirect('dashboard')

    return render(
        request,
        'newsapp/confirm_delete.html',
        {
            'object_name': article.title,
            'object_type': 'article',
            'cancel_url': 'dashboard',
        },
    )


@login_required
@role_required(['editor'])
def editor_review(request):
    """Display articles awaiting editor review."""
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
    """Approve an article and notify subscribed readers."""
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
            'This article has already been approved.',
        )
        return redirect('editor_review')

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
                f'{emails_sent} subscriber email(s) were sent.'
            ),
        )
    else:
        messages.warning(
            request,
            'Article approved, but the API log request was unsuccessful.',
        )

    return redirect('editor_review')


@login_required
@role_required(['journalist', 'editor'])
def newsletter_create(request):
    """Allow a journalist or editor to create a newsletter."""
    if request.method == 'POST':
        form = NewsletterForm(
            request.POST,
            author=request.user,
        )

        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()

            messages.success(
                request,
                'Newsletter created successfully.',
            )

            return redirect('dashboard')
    else:
        form = NewsletterForm(author=request.user)

    return render(
        request,
        'newsapp/newsletter_form.html',
        {
            'form': form,
            'page_title': 'Create Newsletter',
        },
    )


@login_required
@role_required(['journalist', 'editor'])
def newsletter_update(request, newsletter_id):
    """Allow an authorised user to update a newsletter."""
    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
    )

    if (
        request.user.role == 'journalist'
        and newsletter.author != request.user
    ):
        messages.error(
            request,
            'You can only edit your own newsletters.',
        )
        return redirect('dashboard')

    if request.method == 'POST':
        form = NewsletterForm(
            request.POST,
            instance=newsletter,
            author=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Newsletter updated successfully.',
            )

            return redirect('dashboard')
    else:
        form = NewsletterForm(
            instance=newsletter,
            author=request.user,
        )

    return render(
        request,
        'newsapp/newsletter_form.html',
        {
            'form': form,
            'page_title': 'Edit Newsletter',
        },
    )


@login_required
@role_required(['journalist', 'editor'])
def newsletter_delete(request, newsletter_id):
    """Allow an authorised user to delete a newsletter."""
    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
    )

    if (
        request.user.role == 'journalist'
        and newsletter.author != request.user
    ):
        messages.error(
            request,
            'You can only delete your own newsletters.',
        )
        return redirect('dashboard')

    if request.method == 'POST':
        title = newsletter.title
        newsletter.delete()

        messages.success(
            request,
            f'Newsletter "{title}" was deleted successfully.',
        )

        return redirect('dashboard')

    return render(
        request,
        'newsapp/confirm_delete.html',
        {
            'object_name': newsletter.title,
            'object_type': 'newsletter',
            'cancel_url': 'dashboard',
        },
    )


@login_required
@role_required(['editor'])
def publisher_list(request):
    """Display all publishers and assigned users."""
    publishers = Publisher.objects.all().prefetch_related(
        'journalists',
        'editors',
    ).order_by(
        'name'
    )

    return render(
        request,
        'newsapp/publisher_list.html',
        {'publishers': publishers},
    )


@login_required
@role_required(['editor'])
def publisher_create(request):
    """Allow an editor to create a publisher."""
    if request.method == 'POST':
        form = PublisherForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Publisher created successfully.',
            )

            return redirect('publisher_list')
    else:
        form = PublisherForm()

    return render(
        request,
        'newsapp/publisher_form.html',
        {
            'form': form,
            'page_title': 'Create Publisher',
        },
    )


@login_required
@role_required(['editor'])
def publisher_update(request, publisher_id):
    """Allow an editor to update a publisher."""
    publisher = get_object_or_404(
        Publisher,
        id=publisher_id,
    )

    if request.method == 'POST':
        form = PublisherForm(
            request.POST,
            instance=publisher,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Publisher updated successfully.',
            )

            return redirect('publisher_list')
    else:
        form = PublisherForm(instance=publisher)

    return render(
        request,
        'newsapp/publisher_form.html',
        {
            'form': form,
            'page_title': 'Edit Publisher',
        },
    )


@login_required
@role_required(['editor'])
def publisher_delete(request, publisher_id):
    """Allow an editor to delete a publisher."""
    publisher = get_object_or_404(
        Publisher,
        id=publisher_id,
    )

    if request.method == 'POST':
        name = publisher.name
        publisher.delete()

        messages.success(
            request,
            f'Publisher "{name}" was deleted successfully.',
        )

        return redirect('publisher_list')

    return render(
        request,
        'newsapp/confirm_delete.html',
        {
            'object_name': publisher.name,
            'object_type': 'publisher',
            'cancel_url': 'publisher_list',
        },
    )


@login_required
@role_required(['reader'])
def manage_subscriptions(request):
    """Display available publisher and journalist subscriptions."""
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
    """Subscribe the current reader to a publisher."""
    publisher = get_object_or_404(
        Publisher,
        id=publisher_id,
    )

    if request.method == 'POST':
        request.user.subscribed_publishers.add(publisher)

        messages.success(
            request,
            f'You subscribed to {publisher.name}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def unsubscribe_publisher(request, publisher_id):
    """Remove a publisher subscription."""
    publisher = get_object_or_404(
        Publisher,
        id=publisher_id,
    )

    if request.method == 'POST':
        request.user.subscribed_publishers.remove(publisher)

        messages.success(
            request,
            f'You unsubscribed from {publisher.name}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def subscribe_journalist(request, journalist_id):
    """Subscribe the current reader to a journalist."""
    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role='journalist',
    )

    if request.method == 'POST':
        request.user.subscribed_journalists.add(journalist)

        messages.success(
            request,
            f'You subscribed to {journalist.username}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def unsubscribe_journalist(request, journalist_id):
    """Remove a journalist subscription."""
    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role='journalist',
    )

    if request.method == 'POST':
        request.user.subscribed_journalists.remove(journalist)

        messages.success(
            request,
            f'You unsubscribed from {journalist.username}.',
        )

    return redirect('manage_subscriptions')


@login_required
@role_required(['reader'])
def subscribed_articles(request):
    """Display approved articles from followed sources."""
    articles = Article.objects.filter(
        Q(
            publisher__in=request.user.subscribed_publishers.all()
        )
        | Q(
            author__in=request.user.subscribed_journalists.all()
        ),
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
