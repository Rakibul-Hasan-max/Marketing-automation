# from django.db import models
# from django.utils import timezone
# from django.core.validators import MinValueValidator
# from django.contrib.postgres.fields import ArrayField
# from django.contrib.postgres.indexes import GinIndex

# # Use BigAutoField for scalable primary keys
# class CustomerSegment(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "customer_segment"
#         ordering = ["-created_at"]
#         verbose_name = "Customer Segment"
#         verbose_name_plural = "Customer Segments"

#     def __str__(self):
#         return self.name


# class Campaign(models.Model):
#     id = models.BigAutoField(primary_key=True)

#     # tenant FK (adjust to your actual tenant app/model)
#     tenant = models.ForeignKey(
#         "tenants.Tenant",
#         on_delete=models.CASCADE,
#         related_name="campaigns",
#         null=True,
#         blank=True,
#     )
#     # Optional schema name for multi-tenant schemas
#     tenant_schema = models.CharField(max_length=255, blank=True, null=True)

#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)

#     CAMPAIGN_TYPE_CHOICES = [
#         ("new_menu", "new_menu"),
#         ("seasonal", "seasonal"),
#         ("event", "event"),
#         ("flash_sale", "flash_sale"),
#         ("other", "other"),
#     ]
#     campaign_type = models.CharField(
#         max_length=50, choices=CAMPAIGN_TYPE_CHOICES, default="other"
#     )

#     STATUS_CHOICES = [
#         ("draft", "draft"),
#         ("scheduled", "scheduled"),
#         ("active", "active"),
#         ("paused", "paused"),
#         ("completed", "completed"),
#     ]
#     status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")

#     start_date = models.DateTimeField(null=True, blank=True)
#     end_date = models.DateTimeField(null=True, blank=True)

#     # Monetary fields: use DecimalField (Postgres numeric)
#     budget = models.DecimalField(
#         max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
#     )

#     target_audience_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

#     # Channels: use PostgreSQL text array (ArrayField of CharField)
#     channels = ArrayField(
#         base_field=models.CharField(max_length=50),
#         default=list,
#         blank=True,
#     )

#     customer_segment = models.ForeignKey(
#         CustomerSegment,
#         on_delete=models.SET_NULL,
#         related_name="campaigns",
#         null=True,
#         blank=True,
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "campaign"
#         ordering = ["-created_at"]
#         indexes = [
#             GinIndex(fields=["channels"], name="campaign_channels_gin"),
#         ]
#         verbose_name = "Campaign"
#         verbose_name_plural = "Campaigns"

#     def __str__(self):
#         return f"{self.name} ({self.status})"

#     @property
#     def is_active(self):
#         now = timezone.now()
#         if self.start_date and self.end_date:
#             return self.start_date <= now <= self.end_date and self.status == "active"
#         return self.status == "active"


# class CampaignAnalytics(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     campaign = models.ForeignKey(
#         Campaign,
#         on_delete=models.CASCADE,
#         related_name="analytics",
#     )

#     # recorded_at lets you keep time-series snapshots
#     recorded_at = models.DateTimeField(default=timezone.now)

#     total_sent = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
#     total_delivered = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
#     total_opened = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
#     total_clicked = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
#     total_conversions = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

#     revenue_generated = models.DecimalField(
#         max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)]
#     )
#     cost = models.DecimalField(
#         max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)]
#     )
#     # ROI stored as decimal (nullable) or compute on the fly
#     roi = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "campaign_analytics"
#         ordering = ["-recorded_at"]
#         indexes = [
#             models.Index(fields=["recorded_at"]),
#             models.Index(fields=["campaign", "recorded_at"]),
#         ]
#         verbose_name = "Campaign Analytics"
#         verbose_name_plural = "Campaign Analytics"

#     def __str__(self):
#         return f"Analytics: {self.campaign.name} @ {self.recorded_at.isoformat()}"

#     def save(self, *args, **kwargs):
#         # compute ROI if possible: ROI = (revenue - cost) / cost
#         try:
#             if self.cost and self.cost > 0:
#                 self.roi = (self.revenue_generated - self.cost) / self.cost
#             else:
#                 self.roi = None
#         except Exception:
#             self.roi = None
#         super().save(*args, **kwargs)


# class CampaignMessage(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     campaign = models.ForeignKey(
#         Campaign,
#         on_delete=models.CASCADE,
#         related_name="messages",
#     )

#     CHANNEL_CHOICES = [
#         ("email", "email"),
#         ("sms", "sms"),
#         ("whatsapp", "whatsapp"),
#         ("social", "social"),
#         ("push", "push"),
#         ("other", "other"),
#     ]
#     channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES)

#     # message_template may contain placeholders (e.g. handlebars, jinja-style)
#     message_template = models.TextField(blank=True, null=True)
#     subject_line = models.CharField(max_length=255, blank=True, null=True)
#     content_body = models.TextField(blank=True, null=True)

#     scheduled_time = models.DateTimeField(null=True, blank=True)

#     STATUS_CHOICES = [
#         ("draft", "draft"),
#         ("scheduled", "scheduled"),
#         ("sent", "sent"),
#         ("failed", "failed"),
#         ("cancelled", "cancelled"),
#     ]
#     status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")

#     # metadata for provider-specific ids, attempts, provider response, etc.
#     metadata = models.JSONField(default=dict, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "campaign_message"
#         ordering = ["-scheduled_time", "-created_at"]
#         indexes = [
#             GinIndex(fields=["metadata"], name="campaign_message_metadata_gin"),
#             models.Index(fields=["campaign", "status"]),
#         ]
#         verbose_name = "Campaign Message"
#         verbose_name_plural = "Campaign Messages"

#     def __str__(self):
#         return f"{self.channel} message for {self.campaign.name} ({self.status})"
