from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class SocialMediaPost(models.Model):
	id = models.BigAutoField(primary_key=True)

	# Multi-tenant fields (no hard FK to a tenant app to keep decoupled)
	tenant_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	tenant_schema = models.CharField(max_length=255, blank=True, null=True)

	# Optional linkage to a marketing campaign
	campaign = models.ForeignKey(
		'campaign.Campaign',
		on_delete=models.SET_NULL,
		related_name='social_posts',
		null=True,
		blank=True,
	)

	content = models.TextField(blank=True, null=True)

	# JSON arrays
	platforms = models.JSONField(default=list, blank=True)  # e.g. ["facebook","instagram"]
	media_urls = models.JSONField(default=list, blank=True)  # store MediaAsset IDs or direct URLs
	hashtags = models.JSONField(default=list, blank=True)    # e.g. ["#launch","#promo"]

	STATUS_CHOICES = [
		("draft", "draft"),
		("scheduled", "scheduled"),
		("published", "published"),
		("failed", "failed"),
	]
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

	scheduled_time = models.DateTimeField(blank=True, null=True)
	published_time = models.DateTimeField(blank=True, null=True)

	POST_TYPE_CHOICES = [
		("post", "post"),
		("story", "story"),
		("reel", "reel"),
		("video", "video"),
	]
	post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default="post")

	is_ai_generated = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'social_media_post'
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['campaign', 'status']),
			models.Index(fields=['tenant_id']),
		]
		verbose_name = 'Social Media Post'
		verbose_name_plural = 'Social Media Posts'

	def __str__(self):
		base = (self.content or '').strip().split('\n')[0]
		snippet = (base[:40] + '…') if len(base) > 40 else base
		return f"Post {self.id} [{self.status}] {snippet}".strip()

	@property
	def is_published(self):
		return self.status == 'published' and self.published_time is not None

	def mark_published(self):
		self.status = 'published'
		self.published_time = timezone.now()
		self.save(update_fields=['status', 'published_time'])


class SocialMediaPostMetrics(models.Model):
	id = models.BigAutoField(primary_key=True)
	social_media_post = models.ForeignKey(
		SocialMediaPost,
		on_delete=models.CASCADE,
		related_name='metrics',
	)

	PLATFORM_CHOICES = [
		("facebook", "facebook"),
		("instagram", "instagram"),
		("x", "x"),
		("tiktok", "tiktok"),
	]
	platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
	platform_post_id = models.CharField(max_length=255, blank=True, null=True)

	likes_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	shares_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	comments_count = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	reach = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	impressions = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	clicks = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])

	# Stored engagement_rate (can be recomputed on save); Decimal for precision
	engagement_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)

	last_synced_at = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'social_media_post_metrics'
		ordering = ['-last_synced_at']
		indexes = [
			models.Index(fields=['social_media_post', 'platform']),
		]
		verbose_name = 'Social Media Post Metrics'
		verbose_name_plural = 'Social Media Post Metrics'
		unique_together = ('social_media_post', 'platform')

	def __str__(self):
		return f"Metrics {self.social_media_post_id} {self.platform} @ {self.last_synced_at.isoformat()}"

	def save(self, *args, **kwargs):
		try:
			if self.impressions and self.impressions > 0:
				interactions = (self.likes_count + self.shares_count + self.comments_count + self.clicks)
				self.engagement_rate = interactions / self.impressions
			else:
				self.engagement_rate = None
		except Exception:
			self.engagement_rate = None
		if 'update_fields' in kwargs and 'engagement_rate' not in kwargs['update_fields']:
			# ensure engagement_rate included when partial updates
			kwargs['update_fields'] = list(kwargs['update_fields']) + ['engagement_rate']
		super().save(*args, **kwargs)
