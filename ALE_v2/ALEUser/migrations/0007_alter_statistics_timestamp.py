# Generated by Django 4.0.1 on 2022-02-02 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ALEUser', '0006_alter_actions_options_alter_decision_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statistics',
            name='timestamp',
            field=models.DateTimeField(),
        ),
    ]
