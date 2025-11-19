from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class EmailTemplate(models.Model):
	id = models.BigAutoField(primary_key=True)
	tenant_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=255, blank=True, null=True)

	name = models.CharField(max_length=255)

	TEMPLATE_TYPE_CHOICES = [
		("welcome", "welcome"),
		("birthday", "birthday"),
		("promo", "promo"),
		("newsletter", "newsletter"),
		("other", "other"),
	]
	template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, default="other")

	html_content = models.TextField()
	text_content = models.TextField(blank=True, null=True)
	thumbnail_url = models.URLField(blank=True, null=True)

	is_platform_template = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "email_template"
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["tenant_id"]),
		]
		verbose_name = "Email Template"
		verbose_name_plural = "Email Templates"

	def __str__(self):
		return f"{self.name} ({self.template_type})"


class EmailCampaign(models.Model):
	id = models.BigAutoField(primary_key=True)

	tenant_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=255, blank=True, null=True)

	campaign = models.ForeignKey(
		'campaign.Campaign',
		on_delete=models.SET_NULL,
		related_name='email_campaigns',
		null=True,
		blank=True,
	)

	name = models.CharField(max_length=255)
	subject_line = models.CharField(max_length=255)
	preview_text = models.CharField(max_length=255, blank=True, null=True)
	from_name = models.CharField(max_length=255, blank=True, null=True)
	from_email = models.EmailField()
	reply_to_email = models.EmailField(blank=True, null=True)

	email_template = models.ForeignKey(
		EmailTemplate,
		on_delete=models.PROTECT,
		related_name='email_campaigns',
	)
	customer_segment = models.ForeignKey(
		'campaign.CustomerSegment',
		on_delete=models.PROTECT,
		related_name='email_campaigns',
	)

	personalization_fields = models.JSONField(default=dict, blank=True)

	ab_test_enabled = models.BooleanField(default=False)
	AB_TEST_VARIANT_CHOICES = [("A", "A"), ("B", "B"), ("winner", "winner")]
	ab_test_variant = models.CharField(max_length=10, choices=AB_TEST_VARIANT_CHOICES, blank=True, null=True)

	scheduled_time = models.DateTimeField(blank=True, null=True)

	STATUS_CHOICES = [
		("draft", "draft"),
		("scheduled", "scheduled"),
		("sending", "sending"),
		("sent", "sent"),
		("failed", "failed"),
	]
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

	sent_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	delivered_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	opened_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	clicked_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	bounced_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	unsubscribed_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "email_campaign"
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["campaign", "status"]),
			models.Index(fields=["tenant_id"]),
			models.Index(fields=["scheduled_time"]),
		]
		verbose_name = "Email Campaign"
		verbose_name_plural = "Email Campaigns"

	def __str__(self):
		return f"{self.name} [{self.status}]"


class EmailEvent(models.Model):
	id = models.BigAutoField(primary_key=True)
	email_campaign = models.ForeignKey(
		EmailCampaign,
		on_delete=models.CASCADE,
		related_name='events',
	)

	customer_id = models.BigIntegerField(null=True, blank=True, db_index=True)

	EVENT_TYPE_CHOICES = [
		("sent", "sent"),
		("delivered", "delivered"),
		("opened", "opened"),
		("clicked", "clicked"),
		("bounced", "bounced"),
		("unsubscribed", "unsubscribed"),
	]
	event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)

	email_address = models.EmailField()
	timestamp = models.DateTimeField(default=timezone.now)
	user_agent = models.TextField(blank=True, null=True)
	ip_address = models.GenericIPAddressField(blank=True, null=True)
	link_clicked = models.URLField(blank=True, null=True)
	bounce_reason = models.TextField(blank=True, null=True)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "email_event"
		ordering = ["-timestamp"]
		indexes = [
			models.Index(fields=["email_campaign", "event_type", "timestamp"]),
			models.Index(fields=["customer_id"]),
		]
		verbose_name = "Email Event"
		verbose_name_plural = "Email Events"

	def __str__(self):
		return f"Event {self.event_type} for campaign {self.email_campaign_id} @ {self.timestamp.isoformat()}"

