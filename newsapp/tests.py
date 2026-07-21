"""Test the news application."""
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    ApprovedArticleLog,
    Article,
    CustomUser,
    Newsletter,
    Publisher,
)


class ModelTests(TestCase):
    """Test model behaviour."""
    def setUp(self):
        """Create the data required by the tests."""
        self.publisher = Publisher.objects.create(
            name='Ntando Media',
            description='Independent news publisher',
        )

        self.journalist = CustomUser.objects.create_user(
            username='journalist1',
            email='journalist@example.com',
            password='StrongPass123!',
            role='journalist',
        )

        self.editor = CustomUser.objects.create_user(
            username='editor1',
            email='editor@example.com',
            password='StrongPass123!',
            role='editor',
        )

        self.reader = CustomUser.objects.create_user(
            username='reader1',
            email='reader@example.com',
            password='StrongPass123!',
            role='reader',
        )

    def test_users_are_added_to_role_groups(self):
        """Verify that users are added to role groups."""
        self.assertTrue(
            self.journalist.groups.filter(
                name='Journalist'
            ).exists()
        )

        self.assertTrue(
            self.editor.groups.filter(
                name='Editor'
            ).exists()
        )

        self.assertTrue(
            self.reader.groups.filter(
                name='Reader'
            ).exists()
        )

    def test_article_is_unapproved_by_default(self):
        """Verify that article is unapproved by default."""
        article = Article.objects.create(
            title='Test Article',
            content='Test article content.',
            author=self.journalist,
            publisher=self.publisher,
        )

        self.assertFalse(article.approved)

    def test_newsletter_can_contain_articles(self):
        """Verify that newsletter can contain articles."""
        article = Article.objects.create(
            title='Newsletter Article',
            content='Newsletter article content.',
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

        newsletter = Newsletter.objects.create(
            title='Weekly News',
            description='Weekly article collection',
            author=self.journalist,
        )

        newsletter.articles.add(article)

        self.assertEqual(
            newsletter.articles.count(),
            1,
        )


class RegistrationTests(TestCase):
    """Test registration behaviour."""
    def test_registration_creates_user(self):
        """Verify that registration creates user."""
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newreader',
                'email': 'newreader@example.com',
                'role': 'reader',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            CustomUser.objects.filter(
                username='newreader'
            ).exists()
        )

    def test_registration_rejects_different_passwords(self):
        """Verify that registration rejects different passwords."""
        response = self.client.post(
            reverse('register'),
            {
                'username': 'invalidreader',
                'email': 'invalid@example.com',
                'role': 'reader',
                'password1': 'StrongPass123!',
                'password2': 'DifferentPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            CustomUser.objects.filter(
                username='invalidreader'
            ).exists()
        )


class WebPermissionTests(TestCase):
    """Test web permission behaviour."""
    def setUp(self):
        """Create the data required by the tests."""
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            description='Test description',
        )

        self.reader = CustomUser.objects.create_user(
            username='reader',
            password='StrongPass123!',
            role='reader',
        )

        self.journalist = CustomUser.objects.create_user(
            username='journalist',
            password='StrongPass123!',
            role='journalist',
        )

        self.editor = CustomUser.objects.create_user(
            username='editor',
            password='StrongPass123!',
            role='editor',
        )

        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)

        self.article = Article.objects.create(
            title='Pending Story',
            content='Pending article content.',
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

    def test_reader_cannot_open_article_creation_page(self):
        """Verify that reader cannot open article creation page."""
        self.client.login(
            username='reader',
            password='StrongPass123!',
        )

        response = self.client.get(
            reverse('article_create')
        )

        self.assertRedirects(
            response,
            reverse('home'),
        )

    def test_journalist_can_create_article(self):
        """Verify that journalist can create article."""
        self.client.login(
            username='journalist',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('article_create'),
            {
                'title': 'Created Story',
                'content': 'Created story content.',
                'publisher': self.publisher.id,
            },
        )

        self.assertEqual(response.status_code, 302)

        article = Article.objects.get(
            title='Created Story'
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

        self.assertFalse(article.approved)

    def test_editor_can_view_review_page(self):
        """Verify that editor can view review page."""
        self.client.login(
            username='editor',
            password='StrongPass123!',
        )

        response = self.client.get(
            reverse('editor_review')
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Pending Story',
        )

    def test_reader_cannot_view_pending_article(self):
        """Verify that reader cannot view pending article."""
        self.client.login(
            username='reader',
            password='StrongPass123!',
        )

        response = self.client.get(
            reverse(
                'article_detail',
                args=[self.article.id],
            )
        )

        self.assertRedirects(
            response,
            reverse('home'),
        )


class APITests(TestCase):
    """Test a p i behaviour."""
    def setUp(self):
        """Create the data required by the tests."""
        self.client = APIClient()

        self.publisher = Publisher.objects.create(
            name='API Publisher',
            description='API test publisher',
        )

        self.reader = CustomUser.objects.create_user(
            username='api_reader',
            email='api_reader@example.com',
            password='StrongPass123!',
            role='reader',
        )

        self.journalist = CustomUser.objects.create_user(
            username='api_journalist',
            email='api_journalist@example.com',
            password='StrongPass123!',
            role='journalist',
        )

        self.editor = CustomUser.objects.create_user(
            username='api_editor',
            email='api_editor@example.com',
            password='StrongPass123!',
            role='editor',
        )

        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)

        self.approved_article = Article.objects.create(
            title='Approved API Story',
            content='Approved API article content.',
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )

        self.pending_article = Article.objects.create(
            title='Pending API Story',
            content='Pending API article content.',
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

    def test_public_api_only_lists_approved_articles(self):
        """Verify that public api only lists approved articles."""
        response = self.client.get(
            reverse('article-list')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        titles = [
            item['title']
            for item in response.data
        ]

        self.assertIn(
            'Approved API Story',
            titles,
        )

        self.assertNotIn(
            'Pending API Story',
            titles,
        )

    def test_reader_cannot_create_article_using_api(self):
        """Verify that reader cannot create article using api."""
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.post(
            reverse('article-list'),
            {
                'title': 'Reader Story',
                'content': 'Reader content.',
                'publisher': self.publisher.id,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_journalist_can_create_article_using_api(self):
        """Verify that journalist can create article using api."""
        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.post(
            reverse('article-list'),
            {
                'title': 'Journalist API Story',
                'content': 'Journalist API content.',
                'publisher': self.publisher.id,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        article = Article.objects.get(
            title='Journalist API Story'
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

        self.assertFalse(article.approved)

    def test_reader_can_view_subscribed_articles(self):
        """Verify that reader can view subscribed articles."""
        self.reader.subscribed_publishers.add(
            self.publisher
        )

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse('article-subscribed')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        titles = [
            item['title']
            for item in response.data
        ]

        self.assertIn(
            'Approved API Story',
            titles,
        )

    def test_editor_can_approve_article_using_api(self):
        """Verify that editor can approve article using api."""
        self.reader.subscribed_publishers.add(
            self.publisher
        )

        self.client.force_authenticate(
            user=self.editor
        )

        response = self.client.post(
            reverse(
                'article-approve',
                args=[self.pending_article.id],
            ),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.pending_article.refresh_from_db()

        self.assertTrue(
            self.pending_article.approved
        )

        self.assertTrue(
            ApprovedArticleLog.objects.filter(
                article=self.pending_article
            ).exists()
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            'api_reader@example.com',
            mail.outbox[0].to,
        )

    def test_reader_cannot_approve_article_using_api(self):
        """Verify that reader cannot approve article using api."""
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.post(
            reverse(
                'article-approve',
                args=[self.pending_article.id],
            ),
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class URLTests(TestCase):
    """Test u r l behaviour."""
    def test_home_url(self):
        """Verify that home url."""
        response = self.client.get(
            reverse('home')
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_article_api_url(self):
        """Verify that article api url."""
        response = self.client.get(
            reverse('article-list')
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_approved_api_url(self):
        """Verify that approved api url."""
        response = self.client.get(
            reverse('approved-article-list')
        )

        self.assertEqual(
            response.status_code,
            200,
        )



class PublisherPermissionTests(TestCase):
    """Test publisher assignments and article permission rules."""

    def setUp(self):
        """Create publishers and users for publisher permission tests."""

        self.client = APIClient()

        self.publisher_one = Publisher.objects.create(
            name="Publisher One",
            description="First publisher",
        )

        self.publisher_two = Publisher.objects.create(
            name="Publisher Two",
            description="Second publisher",
        )

        self.journalist = CustomUser.objects.create_user(
            username="publisher_journalist",
            email="publisher_journalist@example.com",
            password="StrongPass123!",
            role="journalist",
        )

        self.assigned_editor = CustomUser.objects.create_user(
            username="assigned_editor",
            email="assigned_editor@example.com",
            password="StrongPass123!",
            role="editor",
        )

        self.unassigned_editor = CustomUser.objects.create_user(
            username="unassigned_editor",
            email="unassigned_editor@example.com",
            password="StrongPass123!",
            role="editor",
        )

        self.reader = CustomUser.objects.create_user(
            username="publisher_reader",
            email="publisher_reader@example.com",
            password="StrongPass123!",
            role="reader",
        )

        self.publisher_one.journalists.add(self.journalist)
        self.publisher_one.editors.add(self.assigned_editor)

    def test_journalist_can_create_article_for_assigned_publisher(self):
        """Allow a journalist to create an assigned publisher article."""

        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            reverse("article-list"),
            {
                "title": "Assigned Publisher Story",
                "content": "Article for an assigned publisher.",
                "publisher": self.publisher_one.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        article = Article.objects.get(
            title="Assigned Publisher Story"
        )

        self.assertEqual(
            article.publisher,
            self.publisher_one,
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

    def test_journalist_cannot_create_article_for_unassigned_publisher(self):
        """Reject an unassigned publisher selected by a journalist."""

        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            reverse("article-list"),
            {
                "title": "Unassigned Publisher Story",
                "content": "This article must be rejected.",
                "publisher": self.publisher_two.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Article.objects.filter(
                title="Unassigned Publisher Story"
            ).exists()
        )

    def test_assigned_editor_can_approve_publisher_article(self):
        """Allow an assigned editor to approve a publisher article."""

        article = Article.objects.create(
            title="Assigned Approval Story",
            content="Pending assigned publisher article.",
            author=self.journalist,
            publisher=self.publisher_one,
            approved=False,
        )

        self.client.force_authenticate(
            user=self.assigned_editor
        )

        response = self.client.post(
            reverse(
                "article-approve",
                args=[article.id],
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        article.refresh_from_db()

        self.assertTrue(article.approved)

    def test_unassigned_editor_cannot_approve_publisher_article(self):
        """Reject approval by an editor outside the publisher."""

        article = Article.objects.create(
            title="Blocked Approval Story",
            content="Pending publisher article.",
            author=self.journalist,
            publisher=self.publisher_one,
            approved=False,
        )

        self.client.force_authenticate(
            user=self.unassigned_editor
        )

        response = self.client.post(
            reverse(
                "article-approve",
                args=[article.id],
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        article.refresh_from_db()

        self.assertFalse(article.approved)

    def test_publisher_subscriber_receives_approved_article_email(self):
        """Email a reader subscribed to the article publisher."""

        article = Article.objects.create(
            title="Publisher Subscriber Story",
            content="Article sent to publisher subscribers.",
            author=self.journalist,
            publisher=self.publisher_one,
            approved=False,
        )

        self.reader.subscribed_publishers.add(
            self.publisher_one
        )

        self.client.force_authenticate(
            user=self.assigned_editor
        )

        response = self.client.post(
            reverse(
                "article-approve",
                args=[article.id],
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            self.reader.email,
            mail.outbox[0].to,
        )

    def test_journalist_subscriber_receives_approved_article_email(self):
        """Email a reader subscribed to the article journalist."""

        article = Article.objects.create(
            title="Journalist Subscriber Story",
            content="Article sent to journalist subscribers.",
            author=self.journalist,
            publisher=self.publisher_one,
            approved=False,
        )

        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.client.force_authenticate(
            user=self.assigned_editor
        )

        response = self.client.post(
            reverse(
                "article-approve",
                args=[article.id],
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            self.reader.email,
            mail.outbox[0].to,
        )
