# Switch from Supabase Auth to local email/password auth.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_users_deleted_at_users_is_deleted"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="users",
            name="supabase_uid",
        ),
        # existing rows get an empty (unusable) password and must set one
        migrations.AddField(
            model_name="users",
            name="password",
            field=models.CharField(default="", max_length=128, verbose_name="password"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="users",
            name="last_login",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="last login"
            ),
        ),
    ]
