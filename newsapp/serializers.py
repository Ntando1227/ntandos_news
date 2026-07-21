"""Serializers for converting news application models to API data.""""""Serializers for the Ntando's News REST API."""

from rest_framework import serializers

from .models import (
    ApprovedArticleLog,
    Article,
    CustomUser,
    Newsletter,
    Publisher,
)


class UserSerializer(serializers.ModelSerializer):
    """Serialize application users and reader subscriptions."""

    class Meta:
        """Configure serialized user fields."""

        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "role",
            "subscribed_publishers",
            "subscribed_journalists",
        ]
        read_only_fields = [
            "id",
        ]

    def validate(self, attrs):
        """Ensure subscriptions are only assigned to readers."""

        role = attrs.get(
            "role",
            getattr(self.instance, "role", None),
        )

        if role != "reader":
            if attrs.get("subscribed_publishers"):
                raise serializers.ValidationError(
                    {
                        "subscribed_publishers": (
                            "Only readers may subscribe to publishers."
                        )
                    }
                )

            if attrs.get("subscribed_journalists"):
                raise serializers.ValidationError(
                    {
                        "subscribed_journalists": (
                            "Only readers may subscribe to journalists."
                        )
                    }
                )

        return attrs


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publishers and their assigned staff."""

    editor_names = serializers.SlugRelatedField(
        source="editors",
        many=True,
        read_only=True,
        slug_field="username",
    )

    journalist_names = serializers.SlugRelatedField(
        source="journalists",
        many=True,
        read_only=True,
        slug_field="username",
    )

    class Meta:
        """Configure serialized publisher fields."""

        model = Publisher
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "editors",
            "journalists",
            "editor_names",
            "journalist_names",
        ]


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize articles and enforce publisher assignments."""

    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    publisher_name = serializers.CharField(
        source="publisher.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        """Configure serialized article fields."""

        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "author_username",
            "publisher",
            "publisher_name",
            "created_at",
            "approved",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "approved",
        ]

    def validate_publisher(self, publisher):
        """Ensure a journalist may only use an assigned publisher."""

        request = self.context.get("request")

        if publisher is None:
            return None

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        if request.user.role != "journalist":
            raise serializers.ValidationError(
                "Only journalists can select a publisher."
            )

        if not publisher.journalists.filter(
            pk=request.user.pk
        ).exists():
            raise serializers.ValidationError(
                "You are not assigned to this publisher."
            )

        return publisher

    def validate(self, attrs):
        """Validate article ownership and publisher relationships."""

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return attrs

        publisher = attrs.get(
            "publisher",
            getattr(self.instance, "publisher", None),
        )

        if request.user.role == "journalist" and publisher:
            if not publisher.journalists.filter(
                pk=request.user.pk
            ).exists():
                raise serializers.ValidationError(
                    {
                        "publisher": (
                            "You are not assigned to this publisher."
                        )
                    }
                )

        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletters and their curated articles."""

    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
    )

    class Meta:
        """Configure serialized newsletter fields."""

        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "author_username",
            "articles",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
        ]

    def validate_articles(self, articles):
        """Require newsletters to contain approved articles only."""

        unapproved = [
            article.title
            for article in articles
            if not article.approved
        ]

        if unapproved:
            raise serializers.ValidationError(
                "Newsletters may contain approved articles only."
            )

        return articles


class ApprovedArticleLogSerializer(serializers.ModelSerializer):
    """Serialize records of approved article integrations."""

    class Meta:
        """Configure serialized approval-log fields."""

        model = ApprovedArticleLog
        fields = [
            "id",
            "article",
            "title",
            "author",
            "publisher",
            "approved_at",
        ]
        read_only_fields = [
            "id",
            "approved_at",
        ]

