import collections
from pathlib import Path

import yaml

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from articles.models import Article, Author, Category, Image, Language


class Command(BaseCommand):
    help = 'Reloads from static file directory'

    @staticmethod
    def handle(*args, **options):
        clear_all()
        populate_languages()
        populate_articles()
        populate_authors()
        populate_categories()
        populate_images()


@transaction.atomic
def clear_all():
    Image.objects.all().delete()
    Article.objects.all().delete()
    Author.objects.all().delete()
    Category.objects.all().delete()
    Language.objects.all().delete()


def populate_languages():
    string = Path('/data/src/localizations.yaml').read_text()
    data = yaml.safe_load(string)

    languages = []
    for lang_id, name in data['lang_long'].items():
        languages.append(Language(id=lang_id, name=name))

    Language.objects.bulk_create(languages)


def _article_from_source(path, hidden_articles):
    _, _, _, *extra, slug, _ = path.parts
    [language] = extra if extra else ['en']
    _, head, body = path.read_text().split('---\n', 2)
    meta = yaml.safe_load(head)
    is_listed = not meta.get('hidden') and 'isoListDate' in meta

    extra_info = {}
    for key, value in meta.items():
        match key:
            case ('twitter'|'toc'|'authors'|'original'|'translators'|'editor'|'image'|'replacements'):
                extra_info[key] = value
            case 'translator':
                extra_info['translators'] = [value]
            case default:
                pass
    if (language, slug) in hidden_articles:
        extra_info['is_hidden'] = True
    if 'translators' in extra_info:
        extra_info['translators'] = ', '.join(extra_info['translators'])

    article = Article(
        title=meta['title'],
        body=body,
        slug=slug,
        language_id=language,
        pub_date=meta.get('isoListDate'),
        is_listed=is_listed,
        write_date=meta.get('isoSourceDate'),
        read_time=meta['read_time_minutes'],
        summary=meta['summary'],
        extra=extra_info,
    )
    article.full_clean()
    article._extra = meta
    return article


def populate_articles():
    hidden_articles = set()
    for path in Path('/data/src/').rglob('*/_*.md'):
        slug, *langs, lang = path.stem.split('.')
        hidden_articles.add((lang, slug.strip('_')))

    articles = []
    for path in Path('/data/dst/').rglob('*/source.md'):
        if article := _article_from_source(path, hidden_articles):
            articles.append(article)
    Article.objects.bulk_create(articles)

    names = {au for at in articles for au in at._extra.get('authors', [])}
    authors = {name: Author(name=name) for name in names}
    Author.objects.bulk_create(authors.values())

    ThroughAuthor = Article.authors.through
    through_models = []
    for article in articles:
        for name in article._extra.get('authors', []):
            through_models.append(ThroughAuthor(article_id=article.id, author_id=authors[name].id))
    ThroughAuthor.objects.bulk_create(through_models)


def populate_authors():
    string = Path('/data/src/authors.yaml').read_text()
    data = yaml.safe_load(string)

    authors = {author.name: author for author in Author.objects.all()}
    for name, info in data.items():
        author = authors[name]
        author.shorthand = info['at'].strip('@')
        author.birth_date = info['b'] if 'b' in info and info['b'].year < 3000 else None
        author.death_date = info.get('d')
        author.is_listed = True

    Author.objects.bulk_update(authors.values(), ['shorthand', 'birth_date', 'death_date', 'is_listed'])


def populate_categories():
    by_slug = collections.defaultdict(set)
    for article in Article.objects.prefetch_related('authors'):
        by_slug[article.slug].add(article)

    by_dirx = collections.defaultdict(set)
    for path in Path('/data/src/').rglob('*.md'):
        slug = path.stem.split('.')[0].strip('_')
        dirs = path.parts[3:-1]
        for dirx in dirs:
            by_dirx[dirx].add(slug)

    string = Path('/data/src/categories.yaml').read_text()
    data = yaml.safe_load(string)
    categories = []
    for name, info in data.items():
        category = Category.objects.create(name=name, shorthand=info['at'].strip('@'))
        slugs = info['articles']
        slugs += [slug for dirx in info.get('directories', []) for slug in by_dirx[dirx]]
        articles = [article for slug in slugs for article in by_slug.get(slug, [])]
        category.article_set.set(filter(None, articles))


def populate_images():
    authors = {author.shorthand: author for author in Author.objects.all()}
    root = Path('/data/src/_media')

    for path in root.rglob('*.*'):
        if path.name == '.DS_Store':
            continue
        if path.suffix == '.yaml':
            continue
        if 'authors' in path.parts:
            shorthand = path.stem.split('-')[0]
            image = Image(image=f'authors/{path.name}')
            image.save()
            authors[shorthand].images.add(image)
