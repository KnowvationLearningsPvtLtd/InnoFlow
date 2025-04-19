# Generated by Django 5.1.6 on 2025-04-17 11:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AIModelConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider', models.CharField(choices=[('OPENAI', 'OpenAI'), ('ANTHROPIC', 'Anthropic (Claude)'), ('DEEPSEEK', 'DeepSeek'), ('OLLAMA', 'Ollama'), ('HUGGINGFACE', 'Hugging Face')], max_length=20)),
                ('model_name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('api_key', models.CharField(blank=True, max_length=255, null=True)),
                ('base_url', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parameters', models.JSONField(default=dict)),
                ('model_type', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'AI Model Configuration',
                'verbose_name_plural': 'AI Model Configurations',
            },
        ),
        migrations.CreateModel(
            name='TaskStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('result', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ModelComparison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('compared_models', models.ManyToManyField(related_name='comparisons', to='ai_integration.aimodelconfig')),
            ],
        ),
        migrations.CreateModel(
            name='ModelResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.TextField()),
                ('latency', models.FloatField(help_text='Response time in seconds')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comparison', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='ai_integration.modelcomparison')),
                ('model_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ai_integration.aimodelconfig')),
            ],
            options={
                'ordering': ['latency'],
            },
        ),
    ]
