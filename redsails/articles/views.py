import collections
import re

from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from articles.models import Article, Author, Category, Language


def _annotate_language_siblings(articles, exclude=frozenset()):
    grouper = collections.defaultdict(list)
    for article in Article.objects.select_related('language'):
        if not article.extra.get('is_hidden') and article.language_id not in exclude:
            grouper[article.slug].append((article.language.id, article.language.name))

    for article in articles:
        article.siblings = sorted(grouper[article.slug])


def _special_sort(article):
    # sorting is a bit complicated, account for ISO dates but also negative year singletons
    return int(re.findall(r'-?\d+', article.write_date)[0]), article.pub_date


def index(request, language='en'):
    articles = (
        Article.objects
        .filter(language_id=language, is_listed=True)
        .prefetch_related('authors', 'categories')
    )
    _annotate_language_siblings(articles)
    context = {
        'articles': articles,
        'language': language,
        'url': {'en': ''}.get(language, language),
    }
    return render(request, 'article_list.html', context)


def selected_articles(request, selector, language='en'):
    selected = Author.objects.filter(shorthand=selector).first()
    if selected is None:
        selected = get_object_or_404(Category, shorthand=selector)
    articles = (
        selected.article_set
        .filter(language_id=language, is_listed=True)
        .prefetch_related('authors', 'categories')
    )
    _annotate_language_siblings(articles)
    context = {
        'articles': articles,
        'language': language,
        'title': selected.name,
        'url': {'en': ''}.get(language, language),
    }
    return render(request, 'article_list.html', context)


def source(request, slug, language='en'):
    article = get_object_or_404(Article, slug=slug, language_id=language)
    text = f'# {article.title}\n\n{article.body}'
    return HttpResponse(text, content_type='text/plain')


def article(request, slug, language='en'):
    article = get_object_or_404(Article, slug=slug, language_id=language)
    _annotate_language_siblings([article])
    context = {
        'article': article,
        'language': language,
        'title': article.title,
        'description': article.summary,
        'url': article.url,
        'render_extra_info': True,
    }
    if 'image' in article.extra:
        context['image'] = article.extra['image']
    return render(request, 'article.html', context)


def table_of_contents(request, language='en'):
    articles = Article.objects.filter(language_id=language, is_listed=True)
    articles = sorted(articles, key=_special_sort)
    _annotate_language_siblings(articles, exclude={language})
    context = {
        'language': language,
        'articles': articles,
    }
    return render(request, 'table_of_contents.html', context)


def site(request, language='en'):
    categories = Category.objects.prefetch_related('article_set')
    for category in categories:
        ats = category.article_set.all()
        category.relevant_articles = [at for at in ats if at.is_listed and at.language_id == language]
    context = {
        'language': language,
        'languages': Language.objects.all(),
        'categories': categories,
    }
    return render(request, 'site.html', context)


def rss(request, language='en'):
    context = {
        'language': language,
        'articles': Article.objects.filter(is_listed=True, language_id=language),
    }
    return render(request, 'rss.xml', context)


def authors(request, language='en'):
    context = {
        'language': language,
        'authors': Author.objects
            .filter(is_listed=True)
            .prefetch_related('images')
            .order_by(F('birth_date').asc(nulls_last=True), 'name'),
    }
    return render(request, 'authors_list.html', context)
