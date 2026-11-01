import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from core.base import BaseModel


class UsersManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, email):
        # case-insensitive login; soft-deleted accounts cannot log in
        return self.get(email__iexact=email, is_deleted=False)


class Users(AbstractBaseUser, BaseModel):

    # ROLE_USER = "user"
    # ROLE_ADMIN = "admin"
    # ROLE_CHOICES = [
    #     (ROLE_USER, "User"),
    #     (ROLE_ADMIN, "Admin"),
    # ]
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="user_id"
    )
    # password and last_login come from AbstractBaseUser
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    # role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    # plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    is_active = models.BooleanField(default=True)

    # Usage tracking — SRS section 5
    # resume_improvements_used = models.PositiveIntegerField(default=0)
    # cover_letters_used = models.PositiveIntegerField(default=0)
    # ats_scans_used = models.PositiveIntegerField(default=0)

    objects = UsersManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email

    # ------------------------------------------------------------------
    # Domain methods
    # ------------------------------------------------------------------

    @classmethod
    def register(cls, email, password, first_name="", last_name=""):
        return cls.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    @classmethod
    def email_taken(cls, email):
        return cls.objects.filter(email__iexact=email).exists()

    def change_password(self, new_password):
        self.set_password(new_password)
        self.save(update_fields=["password"])

    def record_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=["last_login"])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])
