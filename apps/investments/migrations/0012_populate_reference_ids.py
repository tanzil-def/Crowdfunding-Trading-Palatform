import uuid
from django.db import migrations

def set_unique_reference_ids(apps, schema_editor):
    PaymentTransaction = apps.get_model('investments', 'PaymentTransaction')
    for pt in PaymentTransaction.objects.filter(reference_id__isnull=True):
        pt.reference_id = str(uuid.uuid4())
        pt.save(update_fields=['reference_id'])

class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0011_add_reference_id_to_paymenttransaction'),
    ]

    operations = [
        migrations.RunPython(set_unique_reference_ids),
    ]
