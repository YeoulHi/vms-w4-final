# Generated migration for adding compound index
# Purpose: Optimize dashboard query pattern (year, department)
# Ref: docs/5.dataflow.md - "인덱스: (year, department) 한 개만 고정"

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='metricrecord',
            index=models.Index(
                fields=['year', 'department'],
                name='idx_metric_records_year_department'
            ),
        ),
    ]
