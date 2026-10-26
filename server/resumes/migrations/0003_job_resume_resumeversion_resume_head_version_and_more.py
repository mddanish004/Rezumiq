
import django.db.models.deletion
import resumes.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resumes', '0002_template'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('company', models.CharField(blank=True, max_length=200, null=True)),
                ('role', models.CharField(blank=True, max_length=200, null=True)),
                ('source_url', models.CharField(blank=True, max_length=2048, null=True)),
                ('raw_text', models.TextField()),
                ('text_hash', models.CharField(max_length=64)),
                ('parsed', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Resume',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=120)),
                ('mode', models.CharField(choices=[('structured', 'Structured'), ('code', 'Code')], default='structured', max_length=16)),
                ('page_limit', models.IntegerField(default=1)),
                ('layout', models.JSONField(blank=True, default=resumes.models._default_layout)),
                ('archived_at', models.DateTimeField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.job')),
                ('source_resume', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='variants', to='resumes.resume')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='resumes.template')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ResumeVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(choices=[('import', 'Import'), ('manual', 'Manual'), ('ai', 'AI'), ('restore', 'Restore'), ('named', 'Named')], max_length=16)),
                ('content', models.JSONField(blank=True, null=True)),
                ('tex_source', models.TextField(blank=True, null=True)),
                ('label', models.CharField(blank=True, max_length=80, null=True)),
                ('semver', models.CharField(blank=True, max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='resumes.resumeversion')),
                ('resume', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='resumes.resume')),
            ],
        ),
        migrations.AddField(
            model_name='resume',
            name='head_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='resumes.resumeversion'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['text_hash'], name='resumes_job_text_ha_a068ae_idx'),
        ),
        migrations.AddIndex(
            model_name='resumeversion',
            index=models.Index(fields=['resume', 'created_at'], name='resumes_res_resume__e80e38_idx'),
        ),
        migrations.AddConstraint(
            model_name='resumeversion',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('content__isnull', False), ('tex_source__isnull', True)), models.Q(('content__isnull', True), ('tex_source__isnull', False)), _connector='OR'), name='resume_versions_one_content'),
        ),
    ]
