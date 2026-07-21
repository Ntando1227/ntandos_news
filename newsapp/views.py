"""REST API views for articles, newsletters, publishers, and users.

This module also handles editor approval, subscriber email notifications,
and approved article logging.
""""""Define REST API views and supporting functions."""
import requests

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ApprovedArticleLog,
    Article,
    CustomUser,
    Newsletter,
    Publisher,
)
from .permissions import (
    ArticleRolePermission,
    EditorApprovalPermission,
    NewsletterRolePermission,
)
from .serializers import (
    ApprovedArticleLogSerializer,
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    UserSerializer,
)


def get_article_subscriber_emails(article):
    """Return article subscriber emails."""
    publisher_subscribers = CustomUser.objects.none()

    if article.publisher:
        publisher_subscribers = CustomUser.objects.filter(
            role='reader',
            subscribed_publishers=article.publisher,
        )

    journalist_subscribers = CustomUser.objects.filter(
        role='reader',
        subscribed_journalists=article.author,
    )

    subscribers = (
        publisher_subscribers | journalist_subscribers
    ).distinct()

    return list(
        subscribers.exclude(email='').values_list(
            'email',
            flat=True,
        )
    )


def email_approved_article(article):
    """Email approved article."""
    recipient_list = get_article_subscriber_emails(article)

    if not recipient_list:
        return 0

    publisher_name = (
        article.publisher.name
        if article.publisher
        else 'Independent journalist'
    )

    message = (
        f'{article.title}\n\n'
        f'Author: {article.author.username}\n'
        f'Publisher: {publisher_name}\n\n'
        f'{article.content}'
    )

    return send_mail(
        subject=f'New approved article: {article.title}',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def post_article_to_approved_endpoint(request, article):
    """Post article to approved endpoint."""
    publisher_name = (
        article.publisher.name
        if article.publisher
        else ''
    )

    payload = {
        'article': article.id,
        'title': article.title,
        'author': article.author.username,
        'publisher': publisher_name,
    }

    endpoint_url = request.build_absolute_uri(
        '/api/approved/'
    )

    try:
        response = requests.post(
            endpoint_url,
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        ApprovedArticleLog.objects.get_or_create(
            article=article,
            defaults={
                'title': article.title,
                'author': article.author.username,
                'publisher': publisher_name,
            },
        )
        return False


class ArticleViewSet(viewsets.ModelViewSet):
    """Provide REST API operations for article."""
    serializer_class = ArticleSerializer
    permission_classes = [ArticleRolePermission]

    def get_queryset(self):
        """Return the queryset available to the current user."""
        user = self.request.user

        if not user.is_authenticated:
            return Article.objects.filter(
                approved=True
            ).select_related(
                'author',
                'publisher',
            )

        if user.role == 'reader':
            return Article.objects.filter(
                approved=True
            ).select_related(
                'author',
                'publisher',
            )

        return Article.objects.all().select_related(
            'author',
            'publisher',
        )

    def perform_create(self, serializer):
        """Create the resource using request-specific values."""
        serializer.save(
            author=self.request.user,
            approved=False,
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscribed',
    )
    def subscribed(self, request):
        """Handle subscribed."""
        if request.user.role != 'reader':
            return Response(
                {
                    'detail': (
                        'Only readers can retrieve subscribed '
                        'articles.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        subscribed_publishers = (
            request.user.subscribed_publishers.all()
        )
        subscribed_journalists = (
            request.user.subscribed_journalists.all()
        )

        articles = Article.objects.filter(
            Q(publisher__in=subscribed_publishers)
            | Q(author__in=subscribed_journalists),
            approved=True,
        ).distinct().select_related(
            'author',
            'publisher',
        )

        serializer = self.get_serializer(
            articles,
            many=True,
        )

        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[EditorApprovalPermission],
        url_path='approve',
    )
    def approve(self, request, pk=None):
        """Handle approve."""
        article = self.get_object()

        self.check_object_permissions(request, article)

        if article.approved:
            return Response(
                {
                    'detail': 'This article is already approved.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        article.approved = True
        article.save(update_fields=['approved'])

        emails_sent = email_approved_article(article)

        api_post_successful = (
            post_article_to_approved_endpoint(
                request,
                article,
            )
        )

        return Response(
            {
                'detail': 'Article approved successfully.',
                'article': ArticleSerializer(article).data,
                'subscriber_emails_sent': emails_sent,
                'approved_endpoint_posted': (
                    api_post_successful
                ),
            },
            status=status.HTTP_200_OK,
        )


class NewsletterViewSet(viewsets.ModelViewSet):
    """Provide REST API operations for newsletter."""
    queryset = Newsletter.objects.all().select_related(
        'author'
    ).prefetch_related(
        'articles'
    )
    serializer_class = NewsletterSerializer
    permission_classes = [NewsletterRolePermission]

    def perform_create(self, serializer):
        """Create the resource using request-specific values."""
        serializer.save(author=self.request.user)


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """Provide REST API operations for publisher."""
    queryset = Publisher.objects.all().prefetch_related(
        'editors',
        'journalists',
    )
    serializer_class = PublisherSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Provide REST API operations for user."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class ApprovedArticleLogViewSet(
    viewsets.ModelViewSet
):
    """Provide REST API operations for approved article log."""
    queryset = ApprovedArticleLog.objects.all().order_by(
        '-approved_at'
    )
    serializer_class = ApprovedArticleLogSerializer
    http_method_names = [
        'get',
        'post',
        'head',
        'options',
    ]

    def create(self, request, *args, **kwargs):
        """Create and return a new resource."""
        article_id = request.data.get('article')

        try:
            article = Article.objects.get(
                id=article_id,
                approved=True,
            )
        except Article.DoesNotExist:
            return Response(
                {
                    'detail': (
                        'The approved article could not be found.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        log, created = (
            ApprovedArticleLog.objects.get_or_create(
                article=article,
                defaults={
                    'title': request.data.get(
                        'title',
                        article.title,
                    ),
                    'author': request.data.get(
                        'author',
                        article.author.username,
                    ),
                    'publisher': request.data.get(
                        'publisher',
                        (
                            article.publisher.name
                            if article.publisher
                            else ''
                        ),
                    ),
                },
            )
        )

        serializer = self.get_serializer(log)

        response_status = (
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        )

        return Response(
            serializer.data,
            status=response_status,
        )


