
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
            name='AiRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('step', models.CharField(choices=[('import', 'Import'), ('jd_parse', 'Jd Parse'), ('plan', 'Plan'), ('rewrite', 'Rewrite'), ('verify', 'Verify'), ('inline_edit', 'Inline Edit'), ('chat_edit', 'Chat Edit'), ('fix_compile', 'Fix Compile'), ('draft', 'Draft'), ('ats_match', 'Ats Match'), ('ats_review', 'Ats Review')], max_length=16)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('succeeded', 'Succeeded'), ('failed', 'Failed')], max_length=16)),
                ('model', models.CharField(max_length=128)),
                ('input_tokens', models.IntegerField(default=0)),
                ('cached_input_tokens', models.IntegerField(default=0)),
                ('output_tokens', models.IntegerField(default=0)),
                ('cost_usd_micros', models.IntegerField(default=0)),
                ('latency_ms', models.IntegerField(blank=True, null=True)),
                ('patch_ops', models.JSONField(blank=True, null=True)),
                ('accepted_op_ids', models.JSONField(blank=True, null=True)),
                ('error', models.TextField(blank=True, null=True)),
                ('byok', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.job')),
                ('resume', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.resume')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resumes.resumeversion')),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'created_at'], name='ai_airun_user_id_32baeb_idx'), models.Index(fields=['created_at'], name='ai_airun_created_0c4427_idx'), models.Index(fields=['resume'], name='ai_airun_resume__76a18b_idx'), models.Index(fields=['version'], name='ai_airun_version_634db2_idx'), models.Index(fields=['job'], name='ai_airun_job_id_21ce76_idx')],
            },
        ),
        migrations.CreateModel(
            name='UserAiKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('openai', 'Openai'), ('anthropic', 'Anthropic'), ('openrouter', 'Openrouter')], max_length=16)),
                ('enabled', models.BooleanField(default=True)),
                ('model_id', models.CharField(blank=True, max_length=128, null=True)),
                ('model_ids', models.JSONField(blank=True, default=list)),
                ('encrypted_key', models.TextField()),
                ('key_hint', models.CharField(max_length=16)),
                ('verified_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'provider')},
            },
        ),
    ]
