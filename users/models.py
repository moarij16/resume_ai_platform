from django.db import models
from django.utils import timezone
from core.base import BaseModel


class UserProfile(BaseModel):

    PLAN_FREE = "free"
    PLAN_PRO = "pro"
    PLAN_ENTERPRISE = "enterprise"
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PRO, "Pro"),
        (PLAN_ENTERPRISE, "Enterprise"),
    ]

    cognito_sub = models.CharField(max_length=128, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return self.email or self.cognito_sub

    # ------------------------------------------------------------------
    # Required by DRF's IsAuthenticated permission check
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
    def get_or_create_from_cognito(
        cls, cognito_sub, email="", given_name="", family_name=""
    ):
        """
        Called on every request by the auth class.
        Creates user on first login, syncs fields on subsequent logins.
        """
        user, created = cls.objects.get_or_create(
            cognito_sub=cognito_sub,
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

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_pro(self):
        return self.plan in (self.PLAN_PRO, self.PLAN_ENTERPRISE)
