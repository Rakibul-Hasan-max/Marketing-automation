from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class WhatsAppTemplate(models.Model):
	id = models.BigAutoField(primary_key=True)

	tenant_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=255, blank=True, null=True)

	name = models.CharField(max_length=255)
	template_id = models.CharField(max_length=255, help_text="WhatsApp approved template ID")
	language = models.CharField(max_length=50)
	category = models.CharField(max_length=100, blank=True, null=True)

	HEADER_TYPE_CHOICES = [
		("text", "text"),
		("image", "image"),
		("video", "video"),
		("document", "document"),
	]
	header_type = models.CharField(max_length=20, choices=HEADER_TYPE_CHOICES, blank=True, null=True)
	header_content = models.TextField(blank=True, null=True)

	body_content = models.TextField()
	footer_content = models.TextField(blank=True, null=True)
	buttons = models.JSONField(default=list, blank=True)

	APPROVAL_STATUS_CHOICES = [
		("pending", "pending"),
		("approved", "approved"),
		("rejected", "rejected"),
	]
	approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default="pending")

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "whatsapp_template"
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["tenant_id"]),
			models.Index(fields=["template_id"]),
		]
		verbose_name = "WhatsApp Template"
		verbose_name_plural = "WhatsApp Templates"

	def __str__(self):
		return f"{self.name} ({self.language})"


class WhatsAppCampaign(models.Model):
	id = models.BigAutoField(primary_key=True)

	tenant_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=255, blank=True, null=True)

	campaign = models.ForeignKey(
		'campaign.Campaign',
		on_delete=models.SET_NULL,
		related_name='whatsapp_campaigns',
		null=True,
		blank=True,
	)

	name = models.CharField(max_length=255)
	whatsapp_template = models.ForeignKey(
		WhatsAppTemplate,
		on_delete=models.PROTECT,
		related_name='campaigns',
	)
	customer_segment = models.ForeignKey(
		'campaign.CustomerSegment',
		on_delete=models.PROTECT,
		related_name='whatsapp_campaigns',
	)

	MESSAGE_TYPE_CHOICES = [
		("promotional", "promotional"),
		("transactional", "transactional"),
		("utility", "utility"),
	]
	message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default="promotional")

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
	read_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	replied_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "whatsapp_campaign"
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["campaign", "status"]),
			models.Index(fields=["tenant_id"]),
			models.Index(fields=["scheduled_time"]),
		]
		verbose_name = "WhatsApp Campaign"
		verbose_name_plural = "WhatsApp Campaigns"

	def __str__(self):
		return f"{self.name} [{self.status}]"


class WhatsAppMessage(models.Model):
	id = models.BigAutoField(primary_key=True)
	whatsapp_campaign = models.ForeignKey(
		WhatsAppCampaign,
		on_delete=models.CASCADE,
		related_name='messages',
	)

	customer_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	phone_number = models.CharField(max_length=32)

	message_id = models.CharField(max_length=255, blank=True, null=True, help_text="WhatsApp message ID")

	STATUS_CHOICES = [
		("sent", "sent"),
		("delivered", "delivered"),
		("read", "read"),
		("failed", "failed"),
	]
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")

	sent_at = models.DateTimeField(blank=True, null=True)
	delivered_at = models.DateTimeField(blank=True, null=True)
	read_at = models.DateTimeField(blank=True, null=True)
	failed_reason = models.TextField(blank=True, null=True)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "whatsapp_message"
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["whatsapp_campaign", "status"]),
			models.Index(fields=["message_id"]),
		]
		verbose_name = "WhatsApp Message"
		verbose_name_plural = "WhatsApp Messages"

	def __str__(self):
		return f"Msg {self.message_id or self.id} [{self.status}] to {self.phone_number}"

	def mark_delivered(self):
		self.status = 'delivered'
		self.delivered_at = timezone.now()
		self.save(update_fields=['status', 'delivered_at'])

	def mark_read(self):
		self.status = 'read'
		self.read_at = timezone.now()
		self.save(update_fields=['status', 'read_at'])

