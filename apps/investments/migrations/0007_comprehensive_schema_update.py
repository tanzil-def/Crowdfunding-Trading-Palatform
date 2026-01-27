# Generated migration for investments schema updates
# Add idempotency_key field and rename payment to payment_transaction

import django.core.validators
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0006_alter_paymenttransaction_amount_and_more'),
    ]

    operations = [
        # Add idempotency_key field to PaymentTransaction
        migrations.AddField(
            model_name='paymenttransaction',
            name='idempotency_key',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Client-provided key to prevent duplicate requests',
                max_length=255,
                null=True,
                unique=True
            ),
        ),
        
        # Change investor foreign key in PaymentTransaction to PROTECT
        migrations.AlterField(
            model_name='paymenttransaction',
            name='investor',
            field=models.ForeignKey(
                help_text='Investor who initiated this payment',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payment_transactions',
                to='users.user'
            ),
        ),
        
        # Change project foreign key in PaymentTransaction to PROTECT
        migrations.AlterField(
            model_name='paymenttransaction',
            name='project',
            field=models.ForeignKey(
                help_text='Project being invested in',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payment_transactions',
                to='projects.project'
            ),
        ),
        
        # Change investor foreign key in SharePurchase to PROTECT
        migrations.AlterField(
            model_name='sharepurchase',
            name='investor',
            field=models.ForeignKey(
                help_text='Investor who owns these shares',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='share_purchases',
                to='users.user'
            ),
        ),
        
        # Change project foreign key in SharePurchase to PROTECT
        migrations.AlterField(
            model_name='sharepurchase',
            name='project',
            field=models.ForeignKey(
                help_text='Project these shares belong to',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='share_purchases',
                to='projects.project'
            ),
        ),
        
        # Rename payment field to payment_transaction in SharePurchase
        migrations.RenameField(
            model_name='sharepurchase',
            old_name='payment',
            new_name='payment_transaction',
        ),
        
        # Add new index for idempotency_key
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(
                fields=['idempotency_key'],
                name='investments_idempot_key_idx'
            ),
        ),
    ]
