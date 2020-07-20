import pandas 
import numpy
from google import google
from google.modules.utils import _get_search_url, get_html, get_pdf, get_pdf_summary
from google.modules.standard_search import _get_link
from urllib.parse import urlencode
title = 'Merchants Bancorp Commences Perpetual Preferred Stock Offering' 
#url = 'http://10.115.1.31:8983/solr/core1/select?fl=id%20title&indent=on&q='
url = 'http://10.115.1.195:8983/solr/opensemanticsearch/select?fl=id,%20title_txt&q='

if '"' not in title:
    query = '"' + title + '"'
    fuzzy_query = title #set up for fuzzy query
else:
    query = title
    fuzzy_query = title.replace('"', '') #if necessary adjust for fuzzy query formatting

print('this is the title --->', title)
params_solr = {'q':query.encode('utf8')} #query encoding                                             
params_solr = urlencode(params_solr)
params_solr = params_solr.replace('q=','title_txt:')
search_url = url + params_solr +'&wt=json' #url formatting
print(search_url)
html = get_html(search_url)

print('complete')
print('double complete')