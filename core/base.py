from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Default manager — excludes soft deleted records automatically."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Use this when you explicitly need deleted records too."""

    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self):
        """Permanently remove from DB — use only when absolutely necessary."""
        super().delete()

    def restore(self):
        """Undo a soft delete."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    @property
    def is_active(self):
        return not self.is_deleted


class UserOwnedModel(BaseModel):
    """
    Base for records that belong to one user (resumes, jobs, scans, documents).
    Subclasses must define a `user` ForeignKey.

    The default manager hides soft-deleted rows; use `all_objects` when deleted
    rows are explicitly needed. (Not on BaseModel itself: the Users model would
    inherit these managers and Django's auth backend relies on its own manager.)
    """

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @classmethod
    def owned_by(cls, user):
        """Records belonging to `user`, excluding soft-deleted ones."""
        if not getattr(user, "is_authenticated", False):
            return cls.objects.none()
        return cls.objects.filter(user=user)

    def is_owned_by(self, user) -> bool:
        return getattr(user, "is_authenticated", False) and self.user_id == user.pk
