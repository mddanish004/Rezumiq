
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
            name='ShareLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=30)),
                ('show_contact', models.BooleanField(default=False)),
                ('is_listed', models.BooleanField(default=False)),
                ('password_hash', models.CharField(blank=True, max_length=255, null=True)),
                ('contact_password_hash', models.CharField(blank=True, max_length=255, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('view_count', models.IntegerField(default=0)),
                ('last_viewed_at', models.DateTimeField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pinned_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.resumeversion')),
                ('resume', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resumes.resume')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LinkView',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('visitor_hash', models.CharField(blank=True, max_length=128, null=True)),
                ('referrer', models.CharField(blank=True, max_length=512, null=True)),
                ('country', models.CharField(blank=True, max_length=64, null=True)),
                ('region', models.CharField(blank=True, max_length=128, null=True)),
                ('city', models.CharField(blank=True, max_length=128, null=True)),
                ('device', models.CharField(blank=True, max_length=64, null=True)),
                ('share_link', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='share_links.sharelink')),
            ],
        ),
        migrations.AddIndex(
            model_name='sharelink',
            index=models.Index(fields=['resume'], name='share_links_resume__174faa_idx'),
        ),
        migrations.AddIndex(
            model_name='sharelink',
            index=models.Index(fields=['pinned_version'], name='share_links_pinned__14d7c1_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='sharelink',
            unique_together={('user', 'slug')},
        ),
        migrations.AddIndex(
            model_name='linkview',
            index=models.Index(fields=['share_link', 'viewed_at'], name='share_links_share_l_95f542_idx'),
        ),
        migrations.AddIndex(
            model_name='linkview',
            index=models.Index(fields=['viewed_at'], name='share_links_viewed__c0e5ce_idx'),
        ),
    ]
