from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('workflows', '0002_node_is_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='retry_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='node',
            name='max_retries',
            field=models.IntegerField(default=3),
        ),
    ]
