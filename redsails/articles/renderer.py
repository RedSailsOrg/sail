import itertools
import re
import copy
from html import escape, unescape
from pathlib import Path

from django.conf import settings

import yaml

import lxml.html

import latex2mathml.converter

import markdown


endings = '.!?>"\'*]«。'
mkd_extensions = ['tables', 'footnotes', 'md_in_html', 'smarty']
mkd = markdown.Markdown(extensions=mkd_extensions)
fixups = [
    (r'\s<sup',         '&nbsp;<sup'),          # hanging reference
    (r'&ndash;&gt;',    '→'),                   # →
    (r'\s*&ndash;',     '&nbsp;— '),            # ndash -> non-breaking mdash
    ('&rsquo;&ldquo;',  '&rsquo;&rdquo;'),      # ‘”    -> ’”
    (r'\B&lsquo;s\b',   '&rsquo;s'),            # x‘s   -> x’s
    ('</em>&ldquo;',    '</em>&rdquo;'),        # x‘s   -> x’s
    ('&rdquo;&hellip;', '&ldquo;&hellip;'),     # ”…    -> “…
]


def math_up(string):
    def replacer(match):
        string = match.group(1)
        output = latex2mathml.converter.convert(string)
        if string[0] == '\n':
            output = output.replace('display="inline"', 'display="block"')
        return output
    return re.sub(r'\$\$([\s\S]+?)\$\$', replacer, string)


def substitutions(string):
    for k, v in fixups:
        string = re.sub(k, v, string)
    return string


def _match_pairs(string, bite=50):
    string = re.sub(r'<script[\s\S]+?</script>', '', string)
    string = unescape(string)

    if 'å' in string or '„' in string:
        return

    pairs = {
        '“': '”',
        '(': ')',
        '{': '}',
        '[': ']',
    }
    is_counter = lambda string: string in 'αβßγabc123456789'
    pattern = re.compile('(' + '|'.join(re.escape(x) for pair in pairs.items() for x in pair) + ')')
    for block in string.split('\n\n'):
        stack = [None]
        for re_match in pattern.finditer(block):
            char, pos = re_match.group(1), re_match.start()
            if char in pairs and char != stack[-1]:
                stack.append(char)
            elif char == pairs.get(stack[-1]):
                stack.pop()
            elif is_counter(re.split(r'(-|\*|\s|>)', block[:pos])[-1].strip('\\')):
                continue
            else:
                raise RuntimeError(f'Unmatched `{char}` in\n```\n{block[pos - bite: pos + bite]}\n```')

        if stack != [None]:
            raise RuntimeError(f'Stack left pending: {stack[1:]} in\n{block}')


def validate(string):
    checks = {
        'spare_breaks': re.compile(r'\w+\n\n\n+\w+').findall,
        'spare_spaces': re.compile(r'\w+  +\w+').findall,
        'unmatched_pair': _match_pairs,
    }
    for name, check_function in checks.items():
        if bad_string := check_function(string):
            assert False, f'{name}: {bad_string}'


def curly_inlines_to_footnotes(raw):
    counter = itertools.count(1)

    def handle_parens(match):
        value = match.group(0)[1:-1]
        if value[0] == '@':
            return Path(value[1:]).read_text().replace('\n', '')
        else:
            if not value[-1] in endings:
                value += '.'
            key = f'[^inline{next(counter)}]'
            extra_foots.append(f'{key}: {value}\n')
            return key

    extra_foots = []
    raw = re.sub(r'\{.+?\}', handle_parens, raw)
    return raw + ''.join(extra_foots)


def apply_replacements(md, replacements):
    if replacements is None:
        return md
    if isinstance(replacements, list):
        replacements = dict(pair for group in replacements for pair in group.items())
    for aa, bb in replacements.items():
        md = re.sub(fr'\b({re.escape(aa)})\b', bb, md)
    return md


def convert(md, replacements=None):
    md = apply_replacements(md, replacements)
    md = math_up(md)
    md = curly_inlines_to_footnotes(md)
    html = mkd.reset().convert(md)
    html = substitutions(html)
    validate(html)
    return html


def summarize(string, lim=280):
    string = string.removeprefix('<p>').removesuffix('</p>')
    string = re.sub(r'<sup[\s\S]+?</sup>', '', string)
    string = re.sub(r'\[\^.+?\]:.+', '', string)
    string = re.sub(r'\[\^.+?\]', '', string)
    string = re.sub(r'\s+', ' ', string)
    summary = re.findall(fr'(\A.{{,{lim}}})(?=\s|\Z)', string)[0]
    summary = summary.rstrip(',')
    if summary != string and not summary.endswith(tuple('.!?')):
        summary += '…'
    return close_tags(summary)


def close_tags(summary):
    stack = []
    for sgn, tp in re.findall(r'(</?)(\w+)', summary):
        if sgn == '<':
            stack.append(tp)
        else:
            assert tp == stack.pop()
    return ''.join([summary] + [f'</{tp}>' for tp in stack])


def to_xml(string):
    return lxml.html.fromstring(string)


def render_xml(xml, **opts):
    return lxml.html.tostring(xml, pretty_print=True, **opts).decode()


def xml_cleanup(xml, article):
    frame_all_pictures(xml, article.slug)
    order_and_prettify_footnotes(xml)
    make_outbound_links_open_in_new_tab(xml)
    return xml


def _slugify(string):
    return re.sub(r'[^\w\s]', '', string.lower()).replace(' ', '-')


def insert_toc(xml, toc_title_string):
    headers = xml.xpath('//h2')
    if not headers:
        return xml

    toc_title = xml.makeelement('h2')
    toc_title.attrib['id'] = 'toc'
    toc_title.text = toc_title_string
    place = headers[0]
    place.addprevious(toc_title)

    toc = xml.makeelement('ul')
    for el in headers:
        el.attrib['id'] = _slugify(el.text_content())
        el.classes.add('content-header')

        # create header element
        anchor = copy.deepcopy(el)
        anchor.tag = 'a'
        del anchor.attrib['id']
        del anchor.attrib['class']
        for sup in anchor.xpath('//sup'):
            sup.getparent().remove(sup)
        anchor.attrib['href'] = f'#{el.attrib["id"]}'
        li = xml.makeelement('li')
        li.append(anchor)
        toc.append(li)

        # add back-link to header
        anchor = xml.makeelement('a')
        anchor.attrib['href'] = '#toc'
        el.append(anchor)

    place.addprevious(toc)
    return xml


def order_and_prettify_footnotes(xml):
    # collect all footnotes
    refs = xml.xpath('//a[@class="footnote-ref"]')
    match xml.xpath('//div[@class="footnote"]/ol'):
        case [result]: foots = result
        case []: return

    # map ID to footnote
    mapping = {}
    for foot in foots.findall('./li'):
        mapping[foot.attrib['id']] = foot
        foot.getparent().remove(foot)

    # re-label all in-text references based on order of appearance
    new_foots = []
    for new_id, ref in enumerate(refs, 1):
        old_id = ref.attrib['href'].lstrip('#')
        new_foots.append([old_id, new_id])

        ref.text = f'[{new_id}]'
        ref.attrib['href'] = f'#fn{new_id}'
        ref.getparent().attrib['id'] = f'fnref{new_id}'

    # append all footnotes
    for old_id, new_id in new_foots:
        foot = copy.deepcopy(mapping[old_id])
        foot.tag = 'p'
        foot.attrib['id'] = f'fn{new_id}'
        foots.append(foot)

        for back_arrow in foot.findall('.//a[@title]'):
            back_arrow.getparent().remove(back_arrow)
        back_arrow.attrib['href'] = f'#fnref{new_id}'
        back_arrow.text = f'[{new_id}]'
        back_arrow.tail = ' '
        del back_arrow.attrib['title']
        foot[0].tag = 'span'
        foot.insert(0, back_arrow)
    foots.tag = 'div'

    # prettify footnote URLs
    for anchor in foots.xpath('.//a[not(@class)]'):
        if '://' in anchor.text_content():
            anchor.classes.add('crimson')
            anchor.text = '[web]'


def make_outbound_links_open_in_new_tab(xml):
    for anchor in xml.xpath('//a'):
        if '://' in anchor.attrib['href']:
            anchor.attrib['target'] = '_blank'


def _find_absolute_urlpath(article_id, path):
    if path.startswith('http'):
        return path
    return settings.MEDIA_URL + f'{article_id}/{path}'


def frame_all_pictures(xml, article_id):
    groups = []
    for img in xml.xpath('//img'):
        frame = img.getprevious()
        if frame is None:
            groups.append([img])
        else:
            groups[-1].append(img)

    for group in groups:
        figure = xml.makeelement('figure')
        group[0].addprevious(figure)

        container = xml.makeelement('div')
        container.classes.add('frame')
        container.classes.add('centered')
        container.classes.add('full-width')

        for img in group:
            path = img.attrib['src']
            url = _find_absolute_urlpath(article_id, path)
            img.attrib['src'] = url.strip('/')

            anchor = xml.makeelement('a')
            anchor.append(img)
            anchor.attrib['target'] = '_blank'
            anchor.attrib['href'] = url.strip('/')
            container.append(anchor)
        figure.append(container)

        # captioning
        # if alt := img.attrib.get('alt'):
        #     figcaption = xml.makeelement('figcaption')
        #     figcaption.text = alt
        #     figure.append(figcaption)


localizations = yaml.safe_load(Path('localizations.yaml').read_text())


def render(md, article):
    replacements = article.extra.get('replacements')
    html = convert(md, replacements)
    xml = to_xml(html)
    xml = xml_cleanup(xml, article)
    if 'toc' in article.extra:
        string = localizations['contents'][article.language_id]
        xml = insert_toc(xml, string)
    html = render_xml(xml)
    return html
