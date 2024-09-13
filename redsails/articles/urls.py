from django.conf import settings
from django.urls import include, path, re_path

import articles.views as articles


routes = [
    path('@<str:selector>', articles.selected_articles),
    path('authors/', articles.authors),
    path('site/', articles.site),
    path('toc/', articles.table_of_contents),
    path('rss.xml', articles.rss),
    path('', articles.index),
    path('<str:slug>/source.md', articles.source),
    path('<str:slug>/', articles.article),
]

urlpatterns = [
    re_path(r'^(?P<language>\w\w)/', include(routes)),
    re_path(r'^', include(routes)),
]
