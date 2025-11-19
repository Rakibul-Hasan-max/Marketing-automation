from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class QRCode(models.Model):
	id = models.BigAutoField(primary_key=True)

	tenant_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=255, blank=True, null=True)

	code = models.CharField(max_length=100, unique=True, help_text="Unique QR code identifier")
	name = models.CharField(max_length=255)

	QR_TYPE_CHOICES = [
		("table", "table"),
		("campaign", "campaign"),
		("location", "location"),
		("event", "event"),
	]
	qr_type = models.CharField(max_length=20, choices=QR_TYPE_CHOICES)

	REDIRECT_ACTION_CHOICES = [
		("app_download", "app_download"),
		("signup", "signup"),
		("ordering", "ordering"),
		("contact", "contact"),
	]
	redirect_action = models.CharField(max_length=30, choices=REDIRECT_ACTION_CHOICES, blank=True, null=True)
	redirect_url = models.URLField(blank=True, null=True)

	landing_page_config = models.JSONField(default=dict, blank=True)

	table_number = models.IntegerField(blank=True, null=True)
	location = models.CharField(max_length=255, blank=True, null=True)
	offer_text = models.TextField(blank=True, null=True)
	discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

	expiry_date = models.DateTimeField(blank=True, null=True)

	max_scans = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	current_scans = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

	is_active = models.BooleanField(default=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = "qr_code"
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["tenant_id"]),
			models.Index(fields=["is_active"]),
		]
		verbose_name = "QR Code"
		verbose_name_plural = "QR Codes"

	def __str__(self):
		return f"{self.name} ({self.code})"

	@property
	def is_expired(self):
		return bool(self.expiry_date and timezone.now() > self.expiry_date)

	@property
	def scans_remaining(self):
		if self.max_scans == 0:
			return None  # unlimited
		return max(0, self.max_scans - self.current_scans)


class QRCodeScan(models.Model):
	id = models.BigAutoField(primary_key=True)
	qr_code = models.ForeignKey(
		QRCode,
		on_delete=models.CASCADE,
		related_name='scans',
	)

	customer_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	scanned_at = models.DateTimeField(default=timezone.now)
	ip_address = models.GenericIPAddressField(blank=True, null=True)
	user_agent = models.TextField(blank=True, null=True)

	DEVICE_TYPE_CHOICES = [
		("ios", "iOS"),
		("android", "Android"),
		("desktop", "Desktop"),
	]
	device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, blank=True, null=True)

	location_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
	location_lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

	ACTION_TAKEN_CHOICES = [
		("signed_up", "signed_up"),
		("downloaded", "downloaded"),
		("ordered", "ordered"),
		("none", "none"),
	]
	action_taken = models.CharField(max_length=30, choices=ACTION_TAKEN_CHOICES, default="none")
	conversion_value = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "qr_code_scan"
		ordering = ["-scanned_at"]
		indexes = [
			models.Index(fields=["qr_code", "scanned_at"]),
			models.Index(fields=["customer_id"]),
		]
		verbose_name = "QR Code Scan"
		verbose_name_plural = "QR Code Scans"

	def __str__(self):
		return f"Scan {self.id} for {self.qr_code_id} @ {self.scanned_at.isoformat()}"

