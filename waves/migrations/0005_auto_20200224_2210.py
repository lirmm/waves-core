# Generated by Django 3.0.3 on 2020-02-24 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0004_auto_20200220_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aparam',
            name='required',
            field=models.NullBooleanField(choices=[(False, 'Optional'), (True, 'Required'), (None, 'Not submitted by user')], default=True, help_text='Submitted and/or Required', verbose_name='Required'),
        ),
        migrations.AlterUniqueTogether(
            name='adaptorinitparam',
            unique_together={('name', 'value', 'content_type', 'object_id')},
        ),
    ]
