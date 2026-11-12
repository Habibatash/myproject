from django.db import models


class ExternalNews(models.Model):
    COUNTRY_CHOICES = [(x, x.title()) for x in ("afghanistan", "world", "pakistan", "iran", "usa")]
    CATEGORY_CHOICES = [(x, x.title()) for x in ("urgent", "political", "security", "economy", "technology", "society", "education", "health", "sports", "other")]

    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    url = models.URLField(max_length=1500, unique=True)
    source = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=32, choices=COUNTRY_CHOICES, db_index=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="other", db_index=True)
    language = models.CharField(max_length=20, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    fetched_at = models.DateTimeField(auto_now=True)
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ("-published_at", "-fetched_at")
        indexes = [models.Index(fields=("country", "category", "-published_at"))]

    def __str__(self):
        return self.title[:100]
