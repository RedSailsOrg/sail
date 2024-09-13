import re
from datetime import date
from email.utils import formatdate
from pathlib import Path

import yaml

from django import template
from django.utils.html import mark_safe

from articles.renderer import render


register = template.Library()
localizations = yaml.safe_load(Path('localizations.yaml').read_text())


@register.filter
def no_tags(string):
    return re.sub(r'<[^>]+>', '', str(string))


@register.filter
def get_host(url):
    host = re.split(r'https?://(?:www\.)?', url)[-1].split('/')[0]
    if host != url:
        return host


@register.filter
def localize_url(value, lang_code=None):
    # depending on language prepend the language prefix
    prefix = '/' if lang_code  in {'en', None} else f'/{lang_code}/'
    tail = '' if '.' in value or '@' in value else '/'
    return mark_safe(re.sub(r'//+', '/', prefix + value + tail))


@register.filter
def translate(value, language='en'):
    return localizations.get(value, {}).get(language, value)


@register.filter
def with_host(value):
    # make an url absolute i.e. not relative to host
    url = 'https://redsails.org' + re.sub(r'//+', '/', '/' + value + '/')
    if '@' in url or 'rss.xml' in url:
        url = url.rstrip('/')
    return url


@register.filter
def jinja_truncate(s, length=60, end='…', leeway=5):
    if len(s) <= length + leeway:
        return s

    result = s[: length - len(end)].rsplit(" ", 1)[0]
    return result + end


@register.filter
def rfc(dt):
    return formatdate((dt - date(1970, 1, 1)).total_seconds())


register.filter(render)
