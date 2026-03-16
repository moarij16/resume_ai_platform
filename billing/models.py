from users.models import Users
import uuid

from core.base import BaseModel
from django.db import models


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CANCELED = "canceled", "Canceled"
    EXPIRED = "expired", "Expired"


class SubscriptionPlans(BaseModel):

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="plan_id"
    )
    name = models.CharField(max_length=100, db_column="plan_name")
    monthly_token_limit = models.IntegerField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    features_json = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "subscription_plans"


class UserSubscription(BaseModel):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="subscription_id",
    )
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        db_column="user_id",
    )
    plan = models.ForeignKey(
        "billing.SubscriptionPlans",
        on_delete=models.PROTECT,
        related_name="user_subscriptions",
        db_column="plan_id",
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    start_date = models.DateTimeField(null=False, blank=False)
    renewal_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_subscriptions"

    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'No Plan'}"

    # Domain methods for status transitions
    def cancel(self):
        self.status = SubscriptionStatus.CANCELED
        self.save(update_fields=["status"])

    def expire(self):
        self.status = SubscriptionStatus.EXPIRED
        self.save(update_fields=["status"])

    def is_active(self):
        return self.status == SubscriptionStatus.ACTIVE


class Feature(BaseModel):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="feature_id"
    )
    name = models.TextField(unique=True, max_length=100, db_column="feature_name")
    token_cost_estimate = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "features"


class TokenUsage(BaseModel):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="usage_id"
    )

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="token_usage",
        db_column="user_id",
    )

    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, db_column="feature_id"
    )

    tokens_consumed = models.IntegerField()

    class Meta:
        db_table = "token_usage"
