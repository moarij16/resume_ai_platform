import uuid

from django.db import models
from django.utils import timezone
from core.base import BaseModel


class Users(BaseModel):

    # ROLE_USER = "user"
    # ROLE_ADMIN = "admin"
    # ROLE_CHOICES = [
    #     (ROLE_USER, "User"),
    #     (ROLE_ADMIN, "Admin"),
    # ]
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="user_id"
    )
    supabase_uid = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    # role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    # plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Usage tracking — SRS section 5
    # resume_improvements_used = models.PositiveIntegerField(default=0)
    # cover_letters_used = models.PositiveIntegerField(default=0)
    # ats_scans_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email or self.supabase_uid

    # ------------------------------------------------------------------
    # DRF required properties
    # ------------------------------------------------------------------

    @property
    def is_authenticated(self):
        return self.is_active

    @property
    def is_anonymous(self):
        return False

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------

    @classmethod
    def get_or_create_from_supabase(
        cls, supabase_uid, email="", given_name="", family_name=""
    ):
        user, created = cls.objects.get_or_create(
            supabase_uid=supabase_uid,
            defaults={
                "email": email,
                "first_name": given_name,
                "last_name": family_name,
            },
        )
        if not created:
            updated_fields = []
            if email and user.email != email:
                user.email = email
                updated_fields.append("email")
            if given_name and user.first_name != given_name:
                user.first_name = given_name
                updated_fields.append("first_name")
            if family_name and user.last_name != family_name:
                user.last_name = family_name
                updated_fields.append("last_name")
            if updated_fields:
                user.save(update_fields=updated_fields)

        user.record_login()
        return user, created

    def record_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=["last_login"])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])
