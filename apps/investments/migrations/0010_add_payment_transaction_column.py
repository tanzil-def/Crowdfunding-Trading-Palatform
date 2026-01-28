from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0009_paymenttransaction_updated_at'), 
    ]

    operations = [
        migrations.AddField(
            model_name='sharepurchase',
            name='payment_transaction',
            field=models.OneToOneField(
                to='investments.PaymentTransaction',
                on_delete=models.PROTECT,
                related_name='share_purchase',
                null=True,  
            )
        ),
    ]
