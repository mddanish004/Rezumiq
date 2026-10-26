
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('kind', models.CharField(choices=[('pdf', 'PDF'), ('tex', 'Tex'), ('text', 'Text')], max_length=8)),
                ('storage_key', models.CharField(max_length=512)),
                ('file_name', models.CharField(max_length=200)),
                ('mime_type', models.CharField(max_length=64)),
                ('size_bytes', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user'], name='uploads_upl_user_id_90cec0_idx')],
            },
        ),
    ]
