import itertools
import re

from django.conf import settings
from django.db import models

import yaml


class Language(models.Model):
    id = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50, null=False)

    class Meta:
        ordering = ['id']


class Image(models.Model):
    image = models.FileField()
    source = models.CharField(max_length=200)

    def __repr__(self):
        return str(self.image)


class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)
    shorthand = models.CharField(max_length=30, unique=True, null=True, blank=True)
    is_listed = models.BooleanField(default=False)
    birth_date = models.DateField(blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)
    images = models.ManyToManyField(Image)

    class Meta:
        ordering = ['name']

    @property
    def url(self):
        return f'/@{self.shorthand}'

    def image_url(self):
        images = self.images.order_by('image')
        return settings.MEDIA_URL + str(images[0].image) if images else settings.STATIC_URL + 'social.png'

    def death_age(self):
        if self.death_date:
            return f' ({(self.death_date - self.birth_date).days // 365})'
        return ''

    def __str__(self):
        return f'Author(name={self.name})'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    shorthand = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    @property
    def url(self):
        return f'/@{self.shorthand}'

    def __str__(self):
        return f'Category(name={self.name})'


def _make_defered_field_manager(defered_fields):
    class DeferedFieldManager(models.Manager):
        def get_queryset(self, *args, **kwargs):
            return super().get_queryset(*args, **kwargs).defer(*defered_fields)
    return DeferedFieldManager()


class Article(models.Model):
    slug = models.SlugField(max_length=100)
    language = models.ForeignKey(Language, null=False, on_delete=models.RESTRICT)
    title = models.CharField(max_length=200)
    body = models.TextField()
    authors = models.ManyToManyField(Author)
    categories = models.ManyToManyField(Category)
    summary = models.CharField(max_length=500)
    pub_date = models.DateField(null=True, blank=True)
    is_listed = models.BooleanField()
    write_date = models.CharField(max_length=20, null=True, blank=True)
    parent_language = models.ForeignKey(Language, blank=True, null=True, on_delete=models.RESTRICT, related_name='parent')
    read_time = models.IntegerField()
    extra = models.JSONField(blank=True, null=True)

    objects = _make_defered_field_manager(['body'])

    class Meta:
        unique_together = [['slug', 'language']]
        ordering = ['-pub_date', 'slug']

    @property
    def url(self):
        return f'/{self.slug}/'

    @property
    def source_url(self):
        return f'/{self.slug}/source.md'

    @property
    def cover_image(self):
        if 'image' in self.extra:
            return self.extra['image'].strip('/')

    @property
    def ordered_authors(self):
        return sorted(self.authors.all(), key=lambda author: self.extra['authors'].index(author.name))

    @property
    def year(self):
        try:
            BC = {'es': 'a. C.'}.get(self.language_id, 'BC')
            if self.write_date:
                yy = int(re.findall(r'-?\d+', self.write_date)[0])
            elif self.pub_date:
                yy = self.pub_date.year
            return f'{abs(yy)} {BC}' if yy < 0 else yy
        except:
            return 'N/A'

    def __str__(self):
        return f'Article(slug={self.slug}, language={self.language_id})'
