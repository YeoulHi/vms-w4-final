from django.db import models

class MetricRecord(models.Model):
    year = models.IntegerField()
    department = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=50)
    metric_value = models.DecimalField(max_digits=18, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("year", "department", "metric_type")

    def __str__(self):
        return f"{self.year} - {self.department} - {self.metric_type}"