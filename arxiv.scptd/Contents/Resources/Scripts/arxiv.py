"""
Usage: arxiv.py <arxiv-id>
"""

# TODO: handle unicode author names
# TODO: refactor


import requests
import json
import urllib
import tempfile
from datetime import datetime
from xml.etree import ElementTree as ET
from docopt import docopt


# XML namespace for traversing arXiv API results
ARXIV_XMLNS = {
    'atom':  'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom'
}


def get_pdf_links(article_xml):
    return [
        a.attrib['href']
        for a in article.findall('atom:link', ARXIV_XMLNS)
        if 'type' in a.attrib
        and a.attrib['type'] == 'application/pdf'
    ]

def get_arxiv_links(article_xml):
    return [
        a.attrib['href']
        for a in article.findall('atom:link', ARXIV_XMLNS)
        if 'href' in a.attrib
        and a.attrib['href'].find('arxiv.org') != -1
        and a.attrib['rel'] == 'alternate'
    ]

def make_arxiv_tex(article_xml):
    return {
        'archivePrefix': 'arXiv',
        'eprint': article_xml.find('atom:id', ARXIV_XMLNS).text.split('/')[-1],
        'primaryClass': article_xml.find('arxiv:primary_category', ARXIV_XMLNS).attrib['term']
    }


if __name__ == '__main__':
    cli = docopt(__doc__)
    
    # arxiv.org API
    r = requests.get(f'http://export.arxiv.org/api/query?id_list=%s' % cli['<arxiv-id>'])
    if r.status_code != 200:
        raise Exception('arxiv.org response code was %s' % r.status_code)
    entries = ET.fromstring(r.text).findall('atom:entry', ARXIV_XMLNS)
    if len(entries) != 1:
        raise Exception('{} article{} returned; expected 1'.format(
            len(entries), '' if len(entries) == 1 else 's'))
    article = entries[0]
    
    # Common API responses
    doi = article.find('arxiv:doi', ARXIV_XMLNS)
    abstract = article.find('atom:summary', ARXIV_XMLNS)
    arxiv_links = get_arxiv_links(article)
    pdf_links = get_pdf_links(article)
    arxiv_id_dict = make_arxiv_tex(article)
    
    # Download all PDFs to temporary directories and update paths
    for i, web_path in enumerate(pdf_links):
        _, tmp_name = tempfile.mkstemp(suffix='.pdf')
        urllib.request.urlretrieve(web_path, tmp_name)
        pdf_links[i] = tmp_name
    
    # If a DOI exists, we just return the DOI, abstract, and arxiv ID metadata
    # If it doesn't exist, we built the bibtex string ourselves
    if doi is not None:
        print(json.dumps({
            'doi': doi.text.strip(),
            'bibtex': None,
            'abstract': abstract.text.strip(),
            'pdfs': pdf_links,
            'links': arxiv_links,
            'eprint': arxiv_id_dict
        }, indent=4))
    else:
        title = article.find('atom:title', ARXIV_XMLNS).text
        pub_date = datetime.strptime(article.find('atom:published', ARXIV_XMLNS).text, '%Y-%m-%dT%H:%M:%SZ')
        authors = [n.text for a in article.findall('atom:author', ARXIV_XMLNS) for n in a.findall('atom:name', ARXIV_XMLNS) ]
        bibtex = '''@article{{{key},
    author = {{{authors}}},
    title = {{{title}}},
    month = {{{month}}},
    year = {{{year}}},
    journal = {{ArXiv e-prints}},
    url = {{{url}}}}}'''.format(
            key=authors[0].split()[-1]+datetime.strftime(pub_date, '%Y'),
            title=title, month=datetime.strftime(pub_date, '%B'),
            year=datetime.strftime(pub_date, '%Y'), url=arxiv_links.pop(0),
            authors=' and '.join(authors), eprint=arxiv_id_dict['eprint'],
            category=arxiv_id_dict['primaryClass'])
        
        print(json.dumps({
            'doi': None,
            'bibtex': bibtex,
            'abstract': abstract.text.strip(),
            'pdfs': pdf_links,
            'links': arxiv_links,
            'eprint': arxiv_id_dict
        }, indent=4))
