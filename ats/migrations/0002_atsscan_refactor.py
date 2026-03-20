import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ats", "0001_initial"),
        ("jobs", "0002_jobdescription_deleted_at_jobdescription_is_deleted"),
        ("resumes", "0003_resume_deleted_at_resume_is_deleted"),
    ]

    operations = [
        # BaseModel fields
        migrations.AddField(
            model_name="atsscan",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="atsscan",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="atsscan",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="atsscan",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Make job nullable
        migrations.AlterField(
            model_name="atsscan",
            name="job",
            field=models.ForeignKey(
                blank=True,
                db_column="job_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="jobs.jobdescription",
            ),
        ),
        # Change ats_score to FloatField
        migrations.AlterField(
            model_name="atsscan",
            name="ats_score",
            field=models.FloatField(),
        ),
        # New fields
        migrations.AddField(
            model_name="atsscan",
            name="scan_mode",
            field=models.CharField(
                choices=[("resume_only", "Resume Only"), ("jd_match", "JD Match")],
                default="resume_only",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="atsscan",
            name="breakdown",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="atsscan",
            name="scan_result",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
