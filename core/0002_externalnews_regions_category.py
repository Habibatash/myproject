from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]

    operations = [
        migrations.AddField(model_name='externalnews', name='regions', field=models.CharField(blank=True, db_index=True, default='', max_length=80)),
        migrations.AddField(model_name='externalnews', name='category', field=models.CharField(db_index=True, default='other', max_length=16)),
        migrations.AddField(model_name='externalnews', name='is_breaking', field=models.BooleanField(default=False)),
    ]
