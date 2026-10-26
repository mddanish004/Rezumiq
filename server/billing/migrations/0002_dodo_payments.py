from django.db import migrations, models


class Migration(migrations.Migration):
    """Razorpay's order ids give way to Dodo Payments ids."""

    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="payment",
            name="billing_pay_razorpa_b1b083_idx",
        ),
        migrations.RenameField(
            model_name="subscription",
            old_name="razorpay_subscription_id",
            new_name="dodo_subscription_id",
        ),
        migrations.RenameField(
            model_name="payment",
            old_name="razorpay_order_id",
            new_name="dodo_checkout_session_id",
        ),
        migrations.RenameField(
            model_name="payment",
            old_name="razorpay_payment_id",
            new_name="dodo_payment_id",
        ),
        migrations.RenameField(
            model_name="payment",
            old_name="razorpay_refund_id",
            new_name="dodo_refund_id",
        ),
        migrations.AlterField(
            model_name="payment",
            name="dodo_checkout_session_id",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["dodo_checkout_session_id"], name="billing_pay_dodo_ch_9c3f5b_idx"
            ),
        ),
    ]
