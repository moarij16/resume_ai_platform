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
