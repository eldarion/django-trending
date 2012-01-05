import datetime

from django.db import models
from django.db.models import Count

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from trending.managers import TrendingManager


class DateTimeAuditModel(models.Model):
    
    created_at = models.DateTimeField(default=datetime.datetime.now)
    modified_at = models.DateTimeField(default=datetime.datetime.now)
    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.modified_at = datetime.datetime.now()
        super(DateTimeAuditModel, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        get_latest_by = "created_at"


class ViewLog(DateTimeAuditModel):
    
    session_key = models.CharField(max_length=40)
    
    viewed_content_type = models.ForeignKey(ContentType)
    viewed_object_id = models.PositiveIntegerField()
    viewed_object = generic.GenericForeignKey(
        ct_field="viewed_content_type",
        fk_field="viewed_object_id"
    )
    
    kind = models.CharField(max_length=50, blank=True) # Used to optionally delineate records that share a content type
    
    class Meta:
        unique_together = (
            ("session_key", "viewed_content_type", "viewed_object_id"),
        )


class DailyViewSummary(DateTimeAuditModel):
    
    views_on = models.DateField()
    count = models.PositiveIntegerField()
    
    viewed_content_type = models.ForeignKey(ContentType)
    viewed_object_id = models.PositiveIntegerField()
    viewed_object = generic.GenericForeignKey(
        ct_field="viewed_content_type",
        fk_field="viewed_object_id"
    )
    
    kind = models.CharField(max_length=50, blank=True) # Used to optionally delineate records that share a content type
    
    objects = TrendingManager()
    
    class Meta:
        unique_together = (
            ("views_on", "viewed_content_type", "viewed_object_id"),
        )
    
    @classmethod
    def summarize(cls, for_date, view_log=None):
        qs = ViewLog.objects.filter(
            created_at__year=for_date.year,
            created_at__month=for_date.month,
            created_at__day=for_date.day
        )
        
        if view_log:
            qs = qs.filter(
                viewed_content_type = view_log.viewed_content_type,
                viewed_object_id = view_log.viewed_object_id
            )
        
        qs = qs.values(
            "viewed_content_type",
            "viewed_object_id",
            "kind"
        ).annotate(
            num_views=Count("id")
        ).order_by()
        
        for view in qs:
            summary, created = DailyViewSummary.objects.get_or_create(
                views_on = for_date,
                viewed_content_type = ContentType.objects.get(pk=view["viewed_content_type"]),
                viewed_object_id = view["viewed_object_id"],
                kind = view["kind"],
                defaults = {"count": view["num_views"]}
            )
            if not created:
                summary.count = view["num_views"]
                summary.save()
