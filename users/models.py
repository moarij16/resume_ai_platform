from django.db import models
from django.utils import timezone
from core.base import BaseModel


class UserProfile(BaseModel):

    PLAN_FREE = "free"
    PLAN_PREMIUM = "premium"  # SRS calls it Premium not Pro
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PREMIUM, "Premium"),
    ]

    ROLE_USER = "user"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ADMIN, "Admin"),
    ]

    supabase_uid = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Usage tracking — SRS section 5
    resume_improvements_used = models.PositiveIntegerField(default=0)
    cover_letters_used = models.PositiveIntegerField(default=0)
    ats_scans_used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return self.email or self.cognito_sub

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

    def upgrade_plan(self, plan):
        if plan not in dict(self.PLAN_CHOICES):
            raise ValueError(f"Invalid plan: {plan}")
        self.plan = plan
        self.save(update_fields=["plan"])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def is_within_limits(self, feature):
        """
        Check if user has remaining usage for a feature.
        SRS section 5 — free tier limits.
        """
        FREE_LIMITS = {
            "resume_improvements": 2,
            "cover_letters": 2,
            "ats_scans": 3,
        }
        if self.plan == self.PLAN_PREMIUM:
            return True  # unlimited
        limit = FREE_LIMITS.get(feature)
        if limit is None:
            return True
        usage_field = f"{feature}_used"
        return getattr(self, usage_field, 0) < limit

    def increment_usage(self, feature):
        """Increment usage counter for a feature."""
        field = f"{feature}_used"
        if hasattr(self, field):
            setattr(self, field, getattr(self, field) + 1)
            self.save(update_fields=[field])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_premium(self):
        return self.plan == self.PLAN_PREMIUM

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN
