"""Define URL routes for the application."""
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ApprovedArticleLogViewSet,
    ArticleViewSet,
    NewsletterViewSet,
    PublisherViewSet,
    UserViewSet,
)
from .web_views import (
    approve_article,
    article_create,
    article_detail,
    article_update,
    editor_review,
    home,
    manage_subscriptions,
    newsletter_create,
    register,
    subscribe_journalist,
    subscribe_publisher,
    subscribed_articles,
    unsubscribe_journalist,
    unsubscribe_publisher,
)

router = DefaultRouter()

router.register(
    'articles',
    ArticleViewSet,
    basename='article',
)

router.register(
    'newsletters',
    NewsletterViewSet,
    basename='newsletter',
)

router.register(
    'publishers',
    PublisherViewSet,
    basename='publisher',
)

router.register(
    'users',
    UserViewSet,
    basename='user',
)

router.register(
    'approved',
    ApprovedArticleLogViewSet,
    basename='approved-article',
)

urlpatterns = [
    path('', home, name='home'),

    path(
        'register/',
        register,
        name='register',
    ),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html'
        ),
        name='login',
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout',
    ),

    path(
        'articles/create/',
        article_create,
        name='article_create',
    ),

    path(
        'articles/subscribed/',
        subscribed_articles,
        name='subscribed_articles',
    ),

    path(
        'articles/<int:article_id>/',
        article_detail,
        name='article_detail',
    ),

    path(
        'articles/<int:article_id>/edit/',
        article_update,
        name='article_update',
    ),

    path(
        'editor/review/',
        editor_review,
        name='editor_review',
    ),

    path(
        'editor/approve/<int:article_id>/',
        approve_article,
        name='approve_article',
    ),

    path(
        'newsletters/create/',
        newsletter_create,
        name='newsletter_create',
    ),

    path(
        'subscriptions/',
        manage_subscriptions,
        name='manage_subscriptions',
    ),

    path(
        'subscriptions/publishers/<int:publisher_id>/subscribe/',
        subscribe_publisher,
        name='subscribe_publisher',
    ),

    path(
        'subscriptions/publishers/<int:publisher_id>/unsubscribe/',
        unsubscribe_publisher,
        name='unsubscribe_publisher',
    ),

    path(
        'subscriptions/journalists/<int:journalist_id>/subscribe/',
        subscribe_journalist,
        name='subscribe_journalist',
    ),

    path(
        'subscriptions/journalists/<int:journalist_id>/unsubscribe/',
        unsubscribe_journalist,
        name='unsubscribe_journalist',
    ),

    path(
        'api/',
        include(router.urls),
    ),
]
