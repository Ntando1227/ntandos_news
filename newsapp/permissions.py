"""Custom permission classes for the Ntando's News REST API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def editor_can_manage_article(user, article):
    """Return whether an editor may manage the supplied article."""

    if not user.is_authenticated or user.role != "editor":
        return False

    if article.publisher is None:
        return True

    return article.publisher.editors.filter(pk=user.pk).exists()


class IsReader(BasePermission):
    """Allow access only to authenticated readers."""

    def has_permission(self, request, view):
        """Check whether the current user is a reader."""

        return (
            request.user.is_authenticated
            and request.user.role == "reader"
        )


class IsJournalist(BasePermission):
    """Allow access only to authenticated journalists."""

    def has_permission(self, request, view):
        """Check whether the current user is a journalist."""

        return (
            request.user.is_authenticated
            and request.user.role == "journalist"
        )


class IsEditor(BasePermission):
    """Allow access only to authenticated editors."""

    def has_permission(self, request, view):
        """Check whether the current user is an editor."""

        return (
            request.user.is_authenticated
            and request.user.role == "editor"
        )


class ArticleRolePermission(BasePermission):
    """Apply role and publisher permissions to article operations."""

    def has_permission(self, request, view):
        """Check general article endpoint access."""

        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        if request.method == "POST":
            return request.user.role == "journalist"

        if request.method in ["PUT", "PATCH", "DELETE"]:
            return request.user.role in ["journalist", "editor"]

        return False

    def has_object_permission(self, request, view, obj):
        """Check article permissions for a specific object."""

        if request.method in SAFE_METHODS:
            if obj.approved:
                return True

            return (
                request.user.is_authenticated
                and (
                    obj.author == request.user
                    or editor_can_manage_article(request.user, obj)
                )
            )

        if request.user.role == "journalist":
            return obj.author == request.user

        if request.user.role == "editor":
            return editor_can_manage_article(request.user, obj)

        return False


class NewsletterRolePermission(BasePermission):
    """Apply role permissions to newsletter operations."""

    def has_permission(self, request, view):
        """Check general newsletter endpoint access."""

        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and request.user.role in ["journalist", "editor"]
        )

    def has_object_permission(self, request, view, obj):
        """Check newsletter permissions for a specific object."""

        if request.method in SAFE_METHODS:
            return True

        if request.user.role == "editor":
            return True

        return (
            request.user.role == "journalist"
            and obj.author == request.user
        )


class EditorApprovalPermission(BasePermission):
    """Allow article approval only by authorised editors."""

    def has_permission(self, request, view):
        """Require the current user to have the editor role."""

        return (
            request.user.is_authenticated
            and request.user.role == "editor"
        )

    def has_object_permission(self, request, view, obj):
        """Require publisher membership for publisher articles."""

        return editor_can_manage_article(request.user, obj)
