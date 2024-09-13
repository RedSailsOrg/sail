import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.CharField(max_length=2, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('shorthand', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(upload_to='')),
                ('source', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('shorthand', models.CharField(max_length=30, unique=True, null=True, blank=True)),
                ('is_listed', models.BooleanField(default=False)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('death_date', models.DateField(blank=True, null=True)),
                ('images', models.ManyToManyField(to='articles.image')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('authors', models.ManyToManyField(to='articles.author')),
                ('categories', models.ManyToManyField(to='articles.category')),
                ('slug', models.SlugField(max_length=100)),
                ('summary', models.CharField(max_length=500)),
                ('pub_date', models.DateField(blank=True, null=True)),
                ('is_listed', models.BooleanField()),
                ('write_date', models.CharField(max_length=20, blank=True, null=True)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='articles.language')),
                ('parent_language', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='parent', to='articles.language')),
                ('read_time', models.IntegerField()),
                ('extra', models.JSONField(blank=True, null=True)),
            ],
            options={
                'unique_together': {('slug', 'language')},
                'ordering': ['-pub_date', 'slug'],
            },
        ),
    ]
