
# Generated by Django 1.11.21 on 2019-06-24 09:22


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submissionoutput',
            name='extension',
            field=models.CharField(blank=True, default='', help_text='Used on WEB for display/download ', max_length=15, verbose_name='File extension (internal)'),
        ),
    ]