
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('resumes', '0003_job_resume_resumeversion_resume_head_version_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=80)),
                ('mode', models.CharField(choices=[('structured', 'Structured'), ('code', 'Code')], max_length=16)),
                ('content', models.JSONField(blank=True, null=True)),
                ('tex_source', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='resumes.template')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user'], name='custom_temp_user_id_2b4076_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('content__isnull', False), ('mode', 'structured')), models.Q(('mode', 'code'), ('tex_source__isnull', False)), _connector='OR'), name='custom_templates_body_matches_mode')],
            },
        ),
    ]
