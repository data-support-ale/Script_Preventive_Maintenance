# Generated by Django 4.0.1 on 2022-01-11 06:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ALEUser', '0003_alter_users_user_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actions',
            fields=[
                ('action_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('action', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('script_path', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Decision',
            fields=[
                ('decision', models.CharField(max_length=50, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Rules',
            fields=[
                ('rules_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('rule_name', models.CharField(max_length=255)),
                ('enabled', models.BooleanField()),
                ('timeout', models.IntegerField()),
                ('action_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ALEUser.actions')),
            ],
        ),
        migrations.CreateModel(
            name='RulesTypes',
            fields=[
                ('rule_type_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('type_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Settings_Value',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('value', models.JSONField()),
            ],
        ),
        migrations.AlterField(
            model_name='users',
            name='user_name',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('actions_status', models.CharField(max_length=50)),
                ('details', models.TextField()),
                ('timestamp', models.DateField()),
                ('decision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ALEUser.decision')),
                ('rule_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ALEUser.rules')),
            ],
        ),
        migrations.AddField(
            model_name='rules',
            name='rule_type_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ALEUser.rulestypes'),
        ),
        migrations.CreateModel(
            name='Decision_History',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('ip_address', models.CharField(max_length=50)),
                ('port', models.CharField(max_length=50)),
                ('decision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ALEUser.decision')),
                ('rule_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ALEUser.rules')),
            ],
        ),
    ]
