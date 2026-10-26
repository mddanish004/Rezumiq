
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
            name='PromoCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=64, unique=True)),
                ('kind', models.CharField(choices=[('promo', 'Promo'), ('ambassador', 'Ambassador')], default='promo', max_length=16)),
                ('plan', models.CharField(choices=[('season_pass', 'Season Pass'), ('pro', 'Pro')], default='season_pass', max_length=16)),
                ('months', models.IntegerField()),
                ('max_redemptions', models.IntegerField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('owner', models.CharField(blank=True, max_length=128, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.CharField(max_length=128, primary_key=True, serialize=False)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('plan', models.CharField(choices=[('season_pass', 'Season Pass'), ('pro', 'Pro')], max_length=16)),
                ('status', models.CharField(choices=[('created', 'Created'), ('active', 'Active'), ('past_due', 'Past Due'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='created', max_length=16)),
                ('razorpay_subscription_id', models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PromoRedemption',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('promo_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billing.promocode')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, unique=True)),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='billing.subscription')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('razorpay_order_id', models.CharField(max_length=128)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ('amount_paise', models.IntegerField()),
                ('currency', models.CharField(default='INR', max_length=8)),
                ('status', models.CharField(choices=[('created', 'Created'), ('captured', 'Captured'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='created', max_length=16)),
                ('method', models.CharField(blank=True, max_length=32, null=True)),
                ('captured_at', models.DateTimeField(blank=True, null=True)),
                ('refunded_at', models.DateTimeField(blank=True, null=True)),
                ('refunded_paise', models.IntegerField(blank=True, null=True)),
                ('razorpay_refund_id', models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ('raw', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='billing.subscription')),
            ],
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['user'], name='billing_sub_user_id_a87c1b_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user'], name='billing_pay_user_id_09fdcc_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['razorpay_order_id'], name='billing_pay_razorpa_b1b083_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['subscription'], name='billing_pay_subscri_1f691a_idx'),
        ),
    ]
