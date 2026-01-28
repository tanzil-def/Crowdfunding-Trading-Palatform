from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0010_add_payment_transaction_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymenttransaction',
            name='reference_id',
            field=models.CharField(
                max_length=255,
                unique=True,
                db_index=True,
                null=True 
            ),
        ),
    ]
