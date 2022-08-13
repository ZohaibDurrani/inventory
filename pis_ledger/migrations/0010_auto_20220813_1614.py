# Generated by Django 3.0.7 on 2022-08-13 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pis_ledger', '0009_ledger_invoice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ledger',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=77, null=True),
        ),
        migrations.AlterField(
            model_name='ledger',
            name='payment',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=77, null=True),
        ),
    ]