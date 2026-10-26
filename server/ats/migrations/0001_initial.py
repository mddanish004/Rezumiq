
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
            name='AtsReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('score', models.IntegerField()),
                ('grade', models.CharField(max_length=16)),
                ('job_match', models.IntegerField(blank=True, null=True)),
                ('report', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.job')),
                ('resume', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ats_reports', to='resumes.resume')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.resumeversion')),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'created_at'], name='ats_atsrepo_user_id_d8ca5d_idx'), models.Index(fields=['resume', 'created_at'], name='ats_atsrepo_resume__c6e35b_idx'), models.Index(fields=['job', 'created_at'], name='ats_atsrepo_job_id_72c5ad_idx')],
            },
        ),
    ]
