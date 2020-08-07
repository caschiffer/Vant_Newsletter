# -*- coding: utf-8 -*-
"""
Created on Tue Feb  5 12:21:06 2019

@author: julia.gray
"""

import mysql.connector as MySQLdb
import json
import datetime
from urllib.parse import urlencode
import add_tagged_entities 
import pickle
import logging
import time
from fuzzywuzzy import fuzz
import os
import codecs
import pandas as pd

from google.modules.utils import get_html

###############################################################################
"""Be sure to add log file path or remove log + try statements prior to running"""
logging.basicConfig(filename = 'get_documents_error_log.log')
###############################################################################


def start_db():
    try:
        db = MySQLdb.connect(host="10.115.1.196",    
                            user="julia",         
                             passwd="Roivant1",  
                             db="ome_star_schema")
        
    except Exception as e:
        logging.error('%s | error in get_documents.start_db %s'%(e, str(datetime.datetime.now())))
    return db


def get_solr_search_url(keyword_list, from_date=datetime.date.today(), to_date=datetime.date.today(), search_params='standard'):
    """Format SOLR search URL depending on the search parameters - 
    standard search = [keyword]
    concurrent search = [keyword0, keyword1, ...]
    """
    try:    
        keyword_fail_list = []
        
        yy = str(from_date).split("-")[0]
        mm = str(from_date).split("-")[1]
        dd = str(from_date).split("-")[2]
    
        eyy = str(to_date).split("-")[0]
        emm = str(to_date).split("-")[1]
        edd = str(to_date).split("-")[2]
        
        if search_params == 'standard':
            if '"' not in keyword_list[0]:
                keyword = '"' + keyword_list[0] + '"'
            else:
                keyword = keyword_list[0]
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +keyword.encode('utf8')}
            params_solr = urlencode(params_solr)
            #url_query = "http://10.115.1.31:8983/solr/core1/select?" + params_solr +'&wt=json&rows=100&fq=file_modified_dt:['+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+eyy+'-'+emm+'-'+edd+'T23:59:59Z]' # CS - adjust second day time stamp to from eyy, emm, edd to to yy,mm,dd
            #print(url_query)
            url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        
    except Exception as e:
        logging.error('%s | error in get_documents.get_solr_search_url %s'%(e, str(datetime.datetime.now())))
        
    return url_query



def construct_solr_search_url(search_terms, from_date=datetime.date.today(), to_date=datetime.date.today()):
    """Possible search terms: keyphrase1, keyphrase2, keyphrase_distance, source_select"""
    try:
        yy = str(from_date).split("-")[0]
        mm = str(from_date).split("-")[1]
        dd = str(from_date).split("-")[2]
    
        #eyy = str(to_date).split("-")[0] # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        #emm = str(to_date).split("-")[1] # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        #edd = str(to_date).split("-")[2] # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        
        if ('keyphrase2' in search_terms) and ('keyphrase_distance' in search_terms):
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +  '"(\\\"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '\\\") (\\\"'.encode('utf8') + search_terms['keyphrase2'].encode('utf8') + '\\\")"~'.encode('utf8') + search_terms['keyphrase_distance'].encode('utf8')}
        elif ('keyphrase2' in search_terms):        
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ':"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '" AND cleaned_html_content_txt:"'.encode('utf8') + search_terms['keyphrase2'].encode('utf8') + '"'.encode('utf8')}
        elif ('keyphrase_distance' in search_terms):
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +  '"(\\\"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '\\\")"~'.encode('utf8') + search_terms['keyphrase_distance'].encode('utf8')}
        else:
            params_solr = {'q':'cleaned_html_content_txt'.encode('utf8') + ":".encode('utf8') +  '"'.encode('utf8') + search_terms['keyphrase1'].encode('utf8') + '"'.encode('utf8')}

        
        params_solr = urlencode(params_solr)
        
        if ('source_select' in search_terms):
            if search_terms['source_select'] != 'all':
                source_select = search_terms['source_select'].split(', ')# CS- split on source_select consistent with splitting for aliases get_search_params_list
                if len(source_select) > 1:
                    #print('source select is longer than 1')
                    source_string_list = []
                    for i in range(0, len(source_select)):
                        if source_select[i] == "Ct.gov":
                            source_string_list.append("path_basename_s:CT.gov-added_or_modified_studies*")    
                        else:
                            source_string_list.append("path0_s:%22" + source_select[i]+"%22")    
                    source_string = ' OR '.join(source_string_list)
                    params_solr = params_solr + ' AND (' + source_string + ')'
                    params_solr = params_solr.replace(' ','%20')
                    #print(params_solr, '-----this is params solr')
                    #print('before url query')
                    url_query = 'http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:['+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500'# CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
                    #print('after url_query')
                else:
                    if source_select[0] == "Ct.gov":
                        url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=path_basename_s:" + "CT.gov-added_or_modified_studies*" + "&fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500' # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
                    else:
                        url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=path0_s:%22" + source_select[0].replace(' ', '%20') + "%22&fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500' # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
            else:
                url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500' # CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd
        else:
            url_query = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+yy+'-'+mm+'-'+dd+'T23:59:59Z]&' + params_solr + '&rows=500'# CS - adjust second day time stamp from eyy, emm, edd to to yy,mm,dd


    except Exception as e:
        logging.error('%s | error in get_documents.construct_solr_search_url %s', (e, str(datetime.datetime.now())))        
    
    #print(url_query , '---- this is the url query')
    return url_query


##CS get_solr_results function adjusted to accommodate new filters for journal_select, author_select, institutional_select, and the fuzzy match leeway
def get_solr_results(all_keywords, subscription_services ,keyword ,search_url, journal_select='', author_select='', institution_select='', filter_leeway=70, tags='tagged_entities_for_web', from_date=None, to_date=None):
    """Parse JSON result of search URL using re HTML. Add tags depending on parametes
    tagged_entities_for_web = tags are CSS classes 
    tagged_entities_for_web_new_moas_indications = tags are CSS classes + get MOA/Indication pairs not in DB
    tagged_entities = inline CSS for HTML email string
    """
    
    doc_count = 0
    
    #try:
    keyword_fail_list = []
    #print('KEYWORD: %s'%(keyword))
    #print(search_url)
    
    
    t0 = datetime.datetime.now()
    solr_results = {'keyword':[], 'path':[], 'file_modified_date':[], 'title':[], 'tagged_document_text':[], 'document_text':[], 'document_type':[], 'detailed_type':[], 'document_tags':[], 'normalized_tags':[], 'normalized_tags_ordered':[], 'normalized_tags2':[], 'normalized_tags_ordered2':[], 'document_id':[], 'new_moa_indication_pairs':[], 'new_moas':[], 'shorter_sentences':[], 'keyword_count':[],'LDA_class':[]}
    
    if tags in ['tagged_entities_indication_moa_pairs', 'tagged_entities_for_web_new_moas_indications']:
        path = '//rs-ny-nas/Roivant Sciences/Business Development/Computational Research/OME alerts/input data/' #YMR addition to load data - path redefined in get_documents.py ...
        with open (path+'dict_MoA_indications_DB', 'rb') as fp:
            dict_MoA_indications_DB = pickle.load(fp)
    try:
        html = get_html(search_url)
    except Exception as e:
        print(e)
    
    if html:
        #print('--- entering html document extraction---')
        d = json.loads(html.decode('utf-8'))
        #print(str(d['response']['numFound']) + ' documents found')
        journal_docid_list = []
        author_docid_list = []
        institution_docid_list = []
        
        #print(d['response']['numFound'], 'number of documents found')
        
        for doc_idx, doc in enumerate(d['response']['docs']):
            #print(doc['id'],'---- this is the document id')
            #if doc_idx % 100 == 0:
            #    print('DOC ' + str(doc_idx) + '/' + str(d['response']['numFound']))
            #if (doc['id'] in solr_results['document_id']) or (doc['title'][0] in solr_results['title']):
            #print(solr_results['title'],'---- lets check the solr _results title prior to filter')
            #print(doc['title_txt'][0], '--- doc title before filter')
            if (doc['id'] in solr_results['document_id']) or (doc['title_txt'][0] in solr_results['title']):
                #print(doc['id'],'--- doc id in id and title tiler')
                #print(doc['title_txt'][0], '--- in id and title filter')
                pass
            elif doc['id'] == "":
                #print(doc['id'],'---- doc id in empty id filter')
                #print(doc['title_txt'][0], 'in no id filter')
                pass
            elif 'cleaned_html_content_txt' not in doc:
                #print(doc['id'],'---- doc id in missing cleaned html content txt')
                #print(doc['title_txt'][0],'--- doc title_txt in missing cleaned html content txt filter')
                pass
            elif 'flag_OME_alert_exclusion_ss' in doc:
                #print(doc['id'],'---- doc id in flag_OME_alert_exclusion_ss filter')
                #print(doc['title_txt'][0],'--- doc title_txt in flag_OME_alert_exclusion_ss filter')
                pass
            else:
                #print(doc['title_txt'][0],'-- doc title text after filter')
                #print(doc)
                #if any(s in doc['id'] for s in ct_paths):
                #if doc['title'][0] not in clinical_trials['title']:
                document_type, detailed_type = get_document_type(doc['id'])
                #print(document_type, '--- this is the document type')
                                
                # document_text extraction should be contingent on tocument type for 
                #if (document_type == 'Cortellis') and ('Drug_Status_Changes_alert' in doc['id']):
                #    print(doc['id'] , '---- this is the doc id')
                #    file_to_read = doc['id']
                #    = codecs.open(file_to_read, "r", "utf-8")
                
                
                #document_text = text_to_sentences(doc['content'][0])
                document_text = ' '.join(add_tagged_entities.text_to_sentences(doc['cleaned_html_content_txt'][0]))
                #hs = highlight_sentences(t, keyword)
                
                # hss = insert_highlight("\n".join(hs), keyword)
                file_modified_date = doc['file_modified_dt'].split("T")[0]
                #file_path = 'http://ome.vant.com/test-app_ome/ome_alert_document/'+doc['id'].replace('/', '!!!').strip('!!!')
                file_path = 'http://52.23.161.54/redirect/<user_name>/' + doc['id'].replace('/', '!!!').strip('!!!')				

                
                ##CS Implementing journal, author, and institution checks. These are a work in progress
                
                ##CS pubmed list pulled from get_document_type function
                pubmed_list= ['pubmed_abstract', 'pubmed_article']
                
                ## CS Journal filter
                if (journal_select != '') and (document_type in pubmed_list):
                    journal_list = journal_select.split(', ')
                    
                    if 'Article_Journal_Title_ss' in doc:
                        #print('----- we entered the first field check for journal check')
                        for i in journal_list:
                            #print(i, '----this is user submitted journal')
                            fuzzy_journal_score = fuzz.ratio(i,doc['Article_Journal_Title_ss'][0])
                            #print(fuzzy_journal_score)
                            #print(doc['Article_Journal_Title_ss'])
                            if fuzzy_journal_score > filter_leeway:
                                journal_docid_list.append(doc['id'])
                            # CS append journals to filter list to only append these later
                    
                    elif 'journal_name_ss' in doc:
                        #print('----- we have entered the second field check for journals')
                        for i in journal_list:
                            fuzzy_journal_score = fuzz.ratio(i,doc['journal_name_ss'][0])
                            if fuzzy_journal_score > filter_leeway:
                                journal_docid_list.append(doc['id'])
                            # CS append journals to filter list to only append these later
                
                ##CS Author Filter
                if (author_select != '') and (document_type in pubmed_list):
                    author_list = author_select.split(', ')
                    if 'Article_AuthorList_Author_Name_ss' in doc:
                        for doc_author in doc['Article_AuthorList_Author_Name_ss']:
                            for user_author in author_list:
                                #print(doc_author,'---- this is the doc_author')
                                #print(user_author, ' ---- this is the user_author')
                                fuzzy_author_score = fuzz.ratio(user_author,doc_author)
                                #print(fuzzy_author_score, '----- this is the fuzzy match score')
                                if fuzzy_author_score > filter_leeway:
                                    #print(doc['id'],'----- append success!')
                                    author_docid_list.append(doc['id'])
                            # CS append authors to filter list to only append these later
                            
                            
                ##CS Institution filter
                if (institution_select != '') and (document_type in pubmed_list):
                    institution_list = institution_select.split(', ')
                    if 'company_OME_txt_ss' in doc:
                        for doc_ins in doc['company_OME_txt_ss']:
                            for user_ins in institution_list:
                                fuzzy_ins_score = fuzz.ratio(doc_ins, user_ins)
                                if fuzzy_ins_score > filter_leeway:
                                    institution_docid_list.append(doc['id'])
                        # CS append insititutions to filter list to only append these later
                            
                        
                if document_type in pubmed_list:
                    if ('Article_Journal_Title_ss' in doc) and ('Article_ArticleTitle_ss' in doc):
                        document_title = doc['Article_Journal_Title_ss'][0] + " | " + doc["Article_ArticleTitle_ss"][0]
                    elif "Article_ArticleTitle_ss" in doc:
                        document_title = doc["Article_ArticleTitle_ss"][0]
                    elif ('Article_Journal_Title_ss' in doc) and ('article_title_ss' in doc):
                        document_title = doc['Article_Journal_Title_ss'][0] + " | " + doc["article_title_ss"][0]
                    elif "journal_name_ss" in doc:
                        document_title = doc["journal_name_ss"][0] + " | " + doc["article_title_ss"][0]
                    elif "article_title_ss" in doc:
                        document_title = doc["article_title_ss"][0]
                    else:
                        document_title = doc["title_txt"][0]
                    #document_title = doc['cleaned_html_content_txt'][0].split('\t')[3]
                    
                    try:
                        if "DateCompleted_Year_ss" in doc:                            
                            original_pub_date = datetime.date(int(doc["DateCompleted_Year_ss"][0]), int(doc["DateCompleted_Month_ss"][0]), int(doc["DateCompleted_Day_ss"][0]))                    
                        elif "Article_Journal_JournalIssue_PubDate_dt" in doc:
                            original_pub_date = datetime.date(int(doc["Article_Journal_JournalIssue_PubDate_dt"].split('T')[0].split('-')[0]), int(doc["Article_Journal_JournalIssue_PubDate_dt"].split('T')[0].split('-')[1]), int(doc["Article_Journal_JournalIssue_PubDate_dt"].split('T')[0].split('-')[2]))
                        elif "Article_ArticleDate_Year_ss" in doc:
                            original_pub_date = datetime.date(int(doc["Article_ArticleDate_Year_ss"][0]), int(doc["Article_ArticleDate_Month_ss"][0]), int(doc["Article_ArticleDate_Day_ss"][0]))
                        elif "pub_date_dt" in doc:
                            original_pub_date = datetime.date(int(doc["pub_date_dt"].split('T')[0].split('-')[0]), int(doc["pub_date_dt"].split('T')[0].split('-')[1]), int(doc["pub_date_dt"].split('T')[0].split('-')[2]))
                        elif "History_PubMedPubDate_pubmed_ss" in doc:    
                            original_pub_date = datetime.date(int(doc["History_PubMedPubDate_pubmed_ss"][0].split('-')[0]), int(doc["History_PubMedPubDate_pubmed_ss"][0].split('-')[1]), int(doc["History_PubMedPubDate_pubmed_ss"][0].split('-')[2]))
                        elif "History_PubMedPubDate_pubmed_dt" in doc:
                            original_pub_date = datetime.date(int(doc["History_PubMedPubDate_pubmed_dt"].split('T')[0].split('-')[0]), int(doc["History_PubMedPubDate_pubmed_dt"].split('T')[0].split('-')[1]), int(doc["History_PubMedPubDate_pubmed_dt"].split('T')[0].split('-')[2]))
                        else:
                            original_pub_date = datetime.date.today()
                            #print(original_pub_date)
                        if original_pub_date < from_date:
                            #print('REVISED PUBMED ARTICLE')
                            continue
                    except:
                        print('no pub date')
                
                else:
                    document_title = doc['title_txt'][0]
           
                #if doc['id'] == 'pmc_6516158.xml':
                #    print(document_text)
                #doc_count += 1
                #print(doc_count,'--- number of documents that are actually returned')
                
                #We are going to move the highlighting of the shorter sentences to after collection of all sentences for all keywords
                #This will enable us to highlight ONLY for those keywords returned and not risk incorrect highlighting
                if keyword != '':
                    if document_type not in subscription_services:
                        keywords_found, shorter_sentences = add_tagged_entities.get_keyword_sentences(document_text, all_keywords)
                        tagged_document_text = add_tagged_entities.highlight_keyword(document_text, all_keywords)
                        #tagged_shorter_sentences = add_tagged_entities.highlight_keyword(shorter_sentences, all_keywords)
                    else:
                        keywords_found, shorter_sentences = add_tagged_entities.get_keyword_sentences_subscriptions(document_text, all_keywords)
                        tagged_document_text = add_tagged_entities.highlight_keyword_subscriptions(document_text, all_keywords)
                        #tagged_shorter_sentences = add_tagged_entities.highlight_keyword_subscriptions(shorter_sentences, all_keywords)
                else:
                    tagged_document_text = document_text
                    shorter_sentences = ''
                    keywords_found = {}
                    tagged_shorter_sentences = document_text
                
                if tags =='tagged_entities_for_web':
                    #print(doc['id'])
                    #normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                    #tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags)
                    #document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                    #tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags)
                    new_indication_moa_pairs = []
                    new_moas = []
                    if 'drug_OME_txt_ss_matchtext_ss' in doc:
                        drug_tag_list = doc['drug_OME_txt_ss_matchtext_ss']
                    else:
                        drug_tag_list = []
					
                    if 'target_OME_txt_ss_matchtext_ss' in doc:
                        target_tag_list = doc['target_OME_txt_ss_matchtext_ss']
                    else:
                        target_tag_list = []
						
                    if 'company_OME_txt_ss_matchtext_ss' in doc:
                        company_tag_list = doc['company_OME_txt_ss_matchtext_ss']
                    else:
                        company_tag_list = []
					
                    if 'indication_OME_txt_ss_matchtext_ss' in doc:
                        indication_tag_list = doc['indication_OME_txt_ss_matchtext_ss']
                    else:
                        indication_tag_list = []
						
                    
                    document_tags = drug_tag_list + target_tag_list + company_tag_list + indication_tag_list
                    normalized_tags, document_tags_list = add_tagged_entities.parse_tag_lists(drug_tag_list, target_tag_list, company_tag_list, indication_tag_list)
                    tagged_document_text = add_tagged_entities.highlight_tags_from_list(tagged_document_text, normalized_tags)
                elif tags =='tagged_entities_for_web_new_moas_indications':
                    #print(doc['id'])
                    normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                    tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags)
                    document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                    tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags)
                    new_indication_moa_pairs, new_moas = add_tagged_entities.get_new_indication_moa_pairs(document_text, normalized_tags, dict_MoA_indications_DB)
                elif tags =='tagged_entities':
                    #print(doc['id'])
                    normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                    tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags, for_web=False)
                    document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                    tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags, for_web=False)
                    new_indication_moa_pairs = []
                    new_moas = []
                elif tags =='tagged_entities_for_email':
                    #print(doc['id'])
                    #normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                    #tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags, for_web=False)
                    #document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                    #tagged_shorter_sentences = add_tagged_entities.highlight_tags(tagged_shorter_sentences, document_tags, for_web=False)
                    new_indication_moa_pairs = []
                    new_moas = []
                    
                    if 'drug_OME_txt_ss_matchtext_ss' in doc:
                        drug_tag_list = doc['drug_OME_txt_ss_matchtext_ss']
                    else:
                        drug_tag_list = []
                    
                    if 'target_OME_txt_ss_matchtext_ss' in doc:
                        target_tag_list = doc['target_OME_txt_ss_matchtext_ss']
                    else:
                        target_tag_list = []
                        
                    if 'company_OME_txt_ss_matchtext_ss' in doc:
                        company_tag_list = doc['company_OME_txt_ss_matchtext_ss']
                    else:
                        company_tag_list = []
                    
                    if 'indication_OME_txt_ss_matchtext_ss' in doc:
                        indication_tag_list = doc['indication_OME_txt_ss_matchtext_ss']
                    else:
                        indication_tag_list = []
                    
                    
                    #For the vant newsletter and most ome alerts we only want to return the company tag list
                    drug_tag_list = []
                    target_tag_list = []
                    indication_tag_list = []
                    
                    
                    
                    document_tags = drug_tag_list + target_tag_list + company_tag_list + indication_tag_list
                    normalized_tags, document_tags_list = add_tagged_entities.parse_tag_lists(drug_tag_list, target_tag_list, company_tag_list, indication_tag_list)
                
                elif tags == 'tagged_entities_indication_moa_pairs':
                    normalized_tags, document_tags = add_tagged_entities.dictionary_matcher(document_text)
                    #tagged_document_text = add_tagged_entities.highlight_tags(tagged_document_text, document_tags)
                    document_tags_list = sorted(normalized_tags.keys(), key=lambda x: normalized_tags[x]['result']['tag_count_cleaned'], reverse=True)
                    new_indication_moa_pairs, new_moas = add_tagged_entities.get_new_indication_moa_pairs(document_text, normalized_tags, dict_MoA_indications_DB)
                    
                    
                
                else:
                    document_tags = {}
                    normalized_tags = {}
                    document_tags_list = []
                    new_indication_moa_pairs = []
                    new_moas = []
                    
                
                solr_results['document_id'].append(doc['id'])
                if 'lda_class_ss' in doc.keys():
                    #print('this is -----', doc['lda_class_ss'][0])
                    solr_results['LDA_class'].append(str(doc['lda_class_ss'][0]))
                    #print('solr results here-----',solr_results['LDA_class'])
                else:
                    solr_results['LDA_class'].append('Not Evaluated')
                solr_results['keyword'].append(keyword.strip())
                #print(keyword, '--- this is the keyword')
                #print(keyword.strip(),'--- this is the stripped keyword')
                solr_results['path'].append(file_path)
                #print(file_path, '--- this is the filepath to be returned')
                solr_results['file_modified_date'].append(file_modified_date)
                solr_results['title'].append(document_title)
                solr_results['tagged_document_text'].append(tagged_document_text)
                solr_results['document_type'].append(document_type)
                solr_results['detailed_type'].append(detailed_type)
                solr_results['document_text'].append(document_text)
                solr_results['normalized_tags'].append(normalized_tags)
                solr_results['document_tags'].append(document_tags)
                solr_results['normalized_tags_ordered'].append(document_tags_list)
                solr_results['new_moa_indication_pairs'].append(new_indication_moa_pairs)
                solr_results['new_moas'].append(new_moas)
                solr_results['shorter_sentences'].append(shorter_sentences)
                solr_results['keyword_count'].append(keywords_found)
            
                
                #solr_results['normalized_tags2'].append(normalized_tags2)
                #solr_results['normalized_tags_ordered2'].append(document_tags2)
            


    tf = datetime.datetime.now()
    #print('SOLR execution time: %s'%(str(tf-t0)))    
    

    # except Exception as e:
    #     logging.error('%s | error in get_documents.get_solr_results %s'%(e, str(datetime.datetime.now())))
        
    ## CS edit returned function from get_solr_results function      
    return solr_results, journal_docid_list, author_docid_list, institution_docid_list


def get_solr_results_from_path(keyword, document_path, tags='tagged_entities_for_web'):
    """For display of single document"""
    try:   
        keyword_path = 'id:"' + '/' + document_path + '"' 
        
        params_solr = {'q':keyword_path.encode('utf8')}
        params_solr = urlencode(params_solr)
        search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?" + params_solr +'&wt=json&rows=100'
        
        
        solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results(keyword, search_url, tags=tags)
    except Exception as e:
        logging.error('%s | error in get_documents.get_solr_results_from_path %s'%(e, str(datetime.datetime.now())))            
    return solr_results
        
                            
def get_document_type(doc_id):
    try:    
        document_type = 'newswire'
        detailed_type = 'newswire'
        
        #ct_paths = ['CT.gov', 'EMEA', 'EU_CT', 'PMDA', 'FDA']
        
        #if any(s in doc_id for s in ct_paths):
        if 'CT.gov' in doc_id:    
            document_type = 'clinical_trials'
            detailed_type = 'CT.gov'
        elif 'EMEA' in doc_id:
            document_type = 'clinical_trials'
            detailed_type = 'EMEA'
        elif 'EU_CT' in doc_id:
            document_type = 'clinical_trials'
            detailed_type = 'EU_CT'
        elif 'Adis' in doc_id:
            document_type = 'Adis Insight'
            detailed_type = 'Adis Insight'
        elif 'evaluate' in doc_id: 
            document_type = 'Evaluate News'
            detailed_type = 'Evaluate News'
        elif 'PMDA' in doc_id:
            document_type = 'clinical_trials'
            detailed_type = 'PMDA'
        elif 'FDA_Medical_reviews' in doc_id:
            document_type = 'FDA_Medical_reviews'
            detailed_type = 'FDA_Medical_reviews'
        elif 'fda_guidance' in doc_id:
            document_type = 'fda_guidance'
            detailed_type = 'fda_guidance'
        elif 'fiercepharma' in doc_id:
            document_type = 'newswire'
            detailed_type = 'fiercepharma'
        elif 'fiercebiotech' in doc_id:
            document_type = 'newswire'
            detailed_type = 'fiercebiotech'
        elif 'politico' in doc_id:
            document_type = 'newswire'
            detailed_type = 'politico_morning_eHealth'
        elif 'alpha' in doc_id:
            document_type = 'newswire'
            detailed_type = 'seeking_alpha_healthcare'
        elif any(x in doc_id for x in ['cortellis','Cortellis']):
            document_type = 'Cortellis'
            detailed_type = 'Cortellis'
        elif any(x in doc_id for x in ['IPD','ipd']):
            document_type = 'IPD'
            detailed_type = 'IPD'
        elif 'GBD' in doc_id:
            document_type = 'GBD_email'
            detailed_type = 'GBD_email'
        elif 'PMC' in doc_id:
            document_type = 'pubmed_article'
            detailed_type = 'pubmed_article'
        elif 'Google_Search' in doc_id:
            document_type = 'google_news'
            detailed_type = 'google_news'
        elif 'google_news' in doc_id:
            document_type = 'google_news'
            detailed_type = 'google_news'
        elif 'PRNW' in doc_id:
            document_type = 'pr_newswire'
            detailed_type = 'pr_newswire'
        elif 'streetaccount' in doc_id:
            document_type = 'streetaccount'
            detailed_type = 'streetaccount'
        elif 'PubMed_abstracts' in doc_id:
            document_type = 'pubmed_abstract'
            detailed_type = 'pubmed_abstract'
        elif 'evercore' in doc_id:
            document_type = 'evercore'
            detailed_type = 'evercore'
        elif 'Twitter' in doc_id:
            document_type = 'twitter'
            detailed_type = 'twitter'
        elif 'SEC_Filings' in doc_id:
            document_type = 'SEC_filing'
            detailed_type = 'SEC_filing'
        elif 'Press releases' in doc_id:
            document_type = 'press_release'
            source_name = doc_id.split('/')[-1].split('_')[0]
            
            if source_name not in ['FirstWordPharma', 'PinkPharmaintelligenceInforma', 'EndPoints', 'MassDevice']:
                detailed_type = 'CompanyPR_' + source_name
            else:
                detailed_type = source_name
    except Exception as e:
        logging.error('%s | error in get_documents.get_document_type %t', (e, str(datetime.datetime.now())))        
    return document_type, detailed_type


def get_ome_alert_results(search_params_list, all_keywords_list, subscription_services, from_date=datetime.date.today(), to_date=datetime.date.today(), tags='tagged_entities_for_web'):
    """Execute multiple SOLR searches and return result as dictionary"""
    #try:
    ome_alert_results = {'keyword':[], 'full_keyword_list':[] ,'path':[], 'file_modified_date':[], 'title':[], 'tagged_document_text':[], 'document_text':[], 'document_type':[], 'document_tags':[], 'normalized_tags':[], 'normalized_tags_ordered':[], 'document_id':[], 'shorter_sentences':[], 'keyword_count':[],'LDA_class':[]}
    url_query = ''
    
    all_keywords_per_document = []
    kw_storage_list = []
    path_full_dict = {}
    for params in search_params_list:
        
        ##CS filter_leeway parameter must always be set to be an integer, 
        ##CS hide on front end until filters selected and edited. Then allow filter leeway editing
        filter_type = params['filter_type']
        filter_leeway = int(params['filter_leeway'])
 

        ##CS Create and execute solr_query, print statements to help with debugging
        ##CS note new returns from get_solr_results function
        url_query = construct_solr_search_url(params, from_date, to_date)
        #print('complete with url_query')
        solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results(all_keywords_list,subscription_services ,params['keyword'] ,url_query, params['journal_select'], params['author_select'], params['institution_select'], filter_leeway, tags=tags, from_date=from_date, to_date=to_date) #CS included params['journal select]
        #print(solr_results, '--- these are the solr results')
        #print('complete with getting solr_results')            
        #print(journal_docid_list,'---- this is the journal docid list')
        #print(author_docid_list, '---- this is the author docid list')
        #print(institution_docid_list, '----- this is the institution_docid_list')
        
        
        ##CS union or intersection parameters for filter type. Determined by user input
        if filter_type == 'and':
            journal_set = journal_set = set(journal_docid_list)
            author_set = set(author_docid_list)
            institution_set = set(institution_docid_list)
            jr_au_ins_filter_set = journal_set & author_set & institution_set
            jr_au_ins_filter_list = list(jr_au_ins_filter_set)
        
        else:
            journal_set = set(journal_docid_list)
            author_set = set(author_docid_list)
            institution_set = set(institution_docid_list)
            jr_au_ins_filter_set = journal_set | author_set | institution_set
            jr_au_ins_filter_list = list(jr_au_ins_filter_set)
            
        
        #print(jr_au_ins_filter_list, '------this is the final filtered list')
        #print(solr_results.keys())
    
        #print('we made it')

        ##Create if statement to handle granular filter parameters
        if (params['journal_select'] != '') or (params['author_select'] != '') or (params['institution_select'] != ''):
            for j in range(0, len(solr_results['path'])):
                kw = solr_results['keyword'][j]
                path = solr_results['path'][j]
                
                #Kw_cnt comes out as a list of tuples. The tuple describes keyword mentions in the text
                #Take the length to find the number of mentions for that keyword
                #print(solr_results['keyword_count'],'--- this is the keyword count')
                kw_cnt = len(solr_results['keyword_count'][j][kw])
                
                #print(kw, '---- this is the kw')
                #print(path, '--- this is the path')
                
                if path not in path_full_dict.keys():
                    path_full_dict[path] = [(kw, kw_cnt)]
                elif path in path_full_dict.keys():
                    path_full_dict[path].append((kw, kw_cnt))
                else:
                    print('problem investigate line 644')
                    pass
            
            
            #print('we entered the filtering stage')
            for j in range(0, len(solr_results['path'])):
                if (solr_results['path'][j] not in ome_alert_results['path']) & (solr_results['document_id'][j] in jr_au_ins_filter_list):
                    print('success for filters!!!!!!!')
                    ome_alert_results['keyword'].append(solr_results['keyword'][j])
                    ome_alert_results['path'].append(solr_results['path'][j])
                    ome_alert_results['file_modified_date'].append(solr_results['file_modified_date'][j])
                    ome_alert_results['title'].append(solr_results['title'][j])
                    ome_alert_results['tagged_document_text'].append(solr_results['tagged_document_text'][j])
                    ome_alert_results['document_text'].append(solr_results['document_text'][j])
                    ome_alert_results['document_type'].append(solr_results['document_type'][j])
                    ome_alert_results['document_tags'].append(solr_results['document_tags'][j])
                    ome_alert_results['normalized_tags'].append(solr_results['normalized_tags'][j])
                    ome_alert_results['normalized_tags_ordered'].append(solr_results['normalized_tags_ordered'][j])
                    ome_alert_results['LDA_class'].append(solr_results['LDA_class'][j])
                    #REMOVE AFTER CLEAWNED NORMALIZED TAGS
                    #ome_alert_results['normalized_tags2'].append(solr_results['normalized_tags2'][j])
                    #ome_alert_results['normalized_tags_ordered2'].append(solr_results['normalized_tags_ordered2'][j])
                    ome_alert_results['document_id'].append(solr_results['document_id'][j])
                    ome_alert_results['shorter_sentences'].append(solr_results['shorter_sentences'][j])
                    ome_alert_results['keyword_count'].append(solr_results['keyword_count'])
        

        ##CS alternative to filter statement where no granular filters in place (source select still functional though)
        ##This function removes redundant documents ---  to adjust listing for keywords make adjustments here
        else:
            for j in range(0, len(solr_results['path'])):
                kw = solr_results['keyword'][j]
                path = solr_results['path'][j]
                
                #Kw_cnt comes out as a list of tuples. The tuple describes keyword mentions in the text
                #Take the length to find the number of mentions for that keyword
                #print(solr_results['keyword_count'],'--- this is the keyword count')
                #print(solr_results['keyword_count'], '--- this is the keyword count')
                kw_cnt = len(solr_results['keyword_count'][j][kw])
                
                #print(kw, '---- this is the kw')
                #print(path, '--- this is the path')
                
                if path not in path_full_dict.keys():
                    path_full_dict[path] = [(kw, kw_cnt)]
                elif path in path_full_dict.keys():
                    path_full_dict[path].append((kw, kw_cnt))
                else:
                    print('problem investigate line 644')
                    pass
                
                if (solr_results['path'][j] not in ome_alert_results['path']):
                    ome_alert_results['keyword'].append(solr_results['keyword'][j])
                    ome_alert_results['path'].append(solr_results['path'][j])
                    ome_alert_results['file_modified_date'].append(solr_results['file_modified_date'][j])
                    ome_alert_results['title'].append(solr_results['title'][j])
                    ome_alert_results['tagged_document_text'].append(solr_results['tagged_document_text'][j])
                    ome_alert_results['document_text'].append(solr_results['document_text'][j])
                    ome_alert_results['document_type'].append(solr_results['document_type'][j])
                    ome_alert_results['document_tags'].append(solr_results['document_tags'][j])
                    ome_alert_results['normalized_tags'].append(solr_results['normalized_tags'][j])
                    ome_alert_results['normalized_tags_ordered'].append(solr_results['normalized_tags_ordered'][j])
                    #REMOVE AFTER CLEAWNED NORMALIZED TAGS
                    #ome_alert_results['normalized_tags2'].append(solr_results['normalized_tags2'][j])
                    #ome_alert_results['normalized_tags_ordered2'].append(solr_results['normalized_tags_ordered2'][j])
                    ome_alert_results['document_id'].append(solr_results['document_id'][j])
                    ome_alert_results['shorter_sentences'].append(solr_results['shorter_sentences'][j])
                
                    ome_alert_results['keyword_count'].append(solr_results['keyword_count'][j])
                    ome_alert_results['LDA_class'].append(solr_results['LDA_class'][j])
        
        
    #Create new for loop to include the full keyword list per path. 
    #print(path_full_dict,'--- this is the path to full dict')
    for p in range(0, len(ome_alert_results['path'])):
        path_to_inv = ome_alert_results['path'][p]
        ome_alert_results['full_keyword_list'].append(path_full_dict[path_to_inv])
    
    #Order list of tuples in ome_alert_results['full_keyword_list']
    for pos, kw_full_list in enumerate(ome_alert_results['full_keyword_list']):
        if len(ome_alert_results['full_keyword_list'][pos]) > 0:
            ome_alert_results['full_keyword_list'][pos] = sorted(ome_alert_results['full_keyword_list'][pos], key= lambda x:x[1], reverse = True)
        else:
            ome_alert_results['full_keyword_list'] = ome_alert_results['full_keyword_list']
            pass
    #ome_alert_results['full_keyword_list'] = [sorted(ome_alert_results['full_keyword_list'], key= lambda x:x[1], reverse = True)]


    #Add new field for specifically tagged/highlighted shorter sentences
    ome_alert_results['tagged_shorter_sentences'] = ome_alert_results['shorter_sentences']
    #This is where we clean tagged the shorter sentences so that we can only search for those keywords we are interested in


    for pos, path in enumerate(ome_alert_results['path']):
        d_type = ome_alert_results['document_type'][pos]
        d_path = ome_alert_results['path'][pos]
        d_shorter_sentence = ome_alert_results['shorter_sentences'][pos]
        d_all_keywords = ome_alert_results['full_keyword_list'][pos]
        ls_d_all_keywords = []
        for tup in d_all_keywords:
            if tup[0] not in ls_d_all_keywords:
                ls_d_all_keywords.append(tup[0])
            else:
                ##redundant keyword entry, there shouldn't be any
                pass
        if any(x in d_type for x in subscription_services):
            ome_alert_results['tagged_shorter_sentences'][pos] = add_tagged_entities.highlight_keyword_subscriptions(d_shorter_sentence, ls_d_all_keywords)
        else:
            #If not in the subscription services
            ome_alert_results['tagged_shorter_sentences'][pos] = add_tagged_entities.highlight_keyword(d_shorter_sentence, ls_d_all_keywords)


    # except Exception as e:
    #     print(e,'--- error in ome_alert_results')                
    #     logging.error('%s | error in get_documents.get_ome_alert_results %s'%(e, str(datetime.datetime.now())))      
                
    return ome_alert_results, url_query
        

def get_ome_alerts_of_user(user):
    try:
        ome_alerts = {'keyword':[], 'aliases':[], 'id':[], 'alert_type':[], 'email':[], 'source_select':[], 'alert_title':[]}
        ome_alert_ids = []
    
        query = """SELECT * FROM ome_star_schema.ome_alerts
                WHERE `user` LIKE "%s" """ %("%" + user + "%")
    
        db = start_db()
        cur = db.cursor()
        cur.execute(query)
    
        for row in cur.fetchall():
            #if row[5] in ['standard', 'standard_title']:
            ome_alerts['id'].append(row[0])
            ome_alerts['keyword'].append(row[1])
            ome_alerts['aliases'].append(row[2])
            ome_alerts['alert_type'].append(row[5])
            ome_alerts['email'].append(row[4])
            ome_alerts['source_select'].append(row[6])
            ome_alerts['alert_title'].append(row[7])
            ome_alert_ids.append(row[0])
    except Exception as e:                
        logging.error('%s | error in get_documents.get_ome_alert_results %s'%(e, str(datetime.datetime.now())))

    return ome_alerts, ome_alert_ids

def get_keyword_list_from_ome_alert_id(keyword_id):
    try:
        keyword_list = []
        clean_keyword_title = []
        clean_keyword_list = []
    
        query = """SELECT * FROM ome_star_schema.ome_alerts
                WHERE idome_alerts = %s"""%(keyword_id.strip('"').strip("'"))
    
        #print(keyword_id)
        #print(query)
    
        db = start_db()
        cur = db.cursor()
        cur.execute(query)
    
        for row in cur.fetchall():
            if row[5] == 'standard_title':
                clean_keyword_title.append(row[1])
            else:
                keyword_list.append(row[1])
                clean_keyword_title.append(row[1])
                
            if row[2] not in ['', None]:
                keyword_list += row[2].split(',')
    
        for k in keyword_list:
            clean_keyword_list.append([k.strip()])
    except Exception as e:
        logging.error('%s | error in get_documents.get_keyword_list_from_ome_alert_id %s'%(e, str(datetime.datetime.now())))        
    return clean_keyword_list, clean_keyword_title

def get_search_params_list(ome_alert_id):
    #keyword gets highlighted - keyphrase gets searched
    try:    
        search_params_list = []
        alert_title = ''
        
        query = """SELECT * FROM ome_star_schema.ome_alerts
                    WHERE idome_alerts = %s"""%(str(ome_alert_id))
            
        db = start_db()
        cur = db.cursor()
        cur.execute(query)
        for row in cur.fetchall():
            alert_title = row[7]
            if row[5] == 'standard':
                if len(row[2]) >= 2:# CS - prevents second, irrelevant + empty search params_list generation
                    search_list = [row[1]] + row[2].split(', ')# CS - prevents second, irrelevant + empty search params_list generation
                elif len(row[2]) < 2:# CS - prevents second, irrelevant + empty search params_list generation
                    search_list = [row[1]]# CS - prevents second, irrelevant + empty search params_list generation
                search_list = [ix for ix in search_list if ix != '']
                search_list = list(set(search_list))  #CS removing duplicate terms
                #print(search_list, '--- this is the search list')
                for i in search_list:
                    search_params_list.append({'search_type':'standard', 'keyphrase1':i, 'keyword':i, 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                    #^^^CS adjusted search_params_list to include new filter columns 
                    
            elif row[5] == 'standard_title':
                search_list = row[2].split(', ')
                search_list = [ix for ix in search_list if ix != '']
                search_list = list(set(search_list))  #CS removing duplicate terms
                #print(search_list, '--- this is the search list')
                for i in search_list:
                    search_params_list.append({'search_type':'standard', 'keyphrase1':i, 'keyword':i, 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                    #^^^CS adjusted search_params_list to include new filter columns 
                    
            elif 'cooccurence' in row[5]:
                search_list = row[2].split(', ')
                #print(search_list, '--- this is the search list')
                search_list = [ix for ix in search_list if ix != '']
                search_list = list(set(search_list))  #CS removing duplicate terms
                #print(search_list, '--- this is the search list')
                for i in search_list:
                    if len(row[5].split('_')) > 1:
                        search_params_list.append({'search_type':'coocurence', 'keyphrase1':row[1], 'keyphrase2':i, 'keyword':i, 'keyphrase_distance':row[5].split('_')[1], 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                        #^^^CS adjusted search_params_list to include new filter columns 
                    else:
                        search_params_list.append({'search_type':'coocurence', 'keyphrase1':row[1], 'keyphrase2':i, 'keyword':i, 'source_select':row[6], 'alert_title':row[7], 'filter_type':row[9], 'journal_select':row[10], 'author_select':row[11], 'institution_select':row[12], 'filter_leeway':row[13]})
                        #^^^CS adjusted search_params_list to include new filter columns 
    except Exception as e:        
        logging.error('%s | error in get_documents.get_search_params_list %s'%(e, str(datetime.datetime.now())))       
    return search_params_list, alert_title, search_list
        
                
                
def get_company_pr_solr_url(company_string, from_date=None, to_date=None):
	company_path = 'path_basename_s:*' + '\ '.join(company_string.split(' ')) + '*'
	params_solr = {'q':company_path.encode('utf8')}
	params_solr = urlencode(params_solr)
	
	if from_date:
		yy = str(from_date).split("-")[0]
		mm = str(from_date).split("-")[1]
		dd = str(from_date).split("-")[2]
    
		eyy = str(to_date).split("-")[0]
		emm = str(to_date).split("-")[1]
		edd = str(to_date).split("-")[2]
		
		search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=file_modified_dt:["+yy+'-'+mm+'-'+dd+'T00:00:00Z%20TO%20'+eyy+'-'+emm+'-'+edd+"T23:59:59Z]&fq=-id:*google_news_search*&fq=path0_s:%22Press%20releases%22&" + params_solr +'&wt=json&rows=100'
	else:
		search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=-id:*google_news_search*&fq=path0_s:%22Press%20releases%22&" + params_solr +'&wt=json&rows=100'
	#search_url = "http://10.115.1.195:8983/solr/opensemanticsearch/select?" + params_solr +'&wt=json&rows=100'
	
	return search_url



#url_query =  'http://10.115.1.195:8983/solr/opensemanticsearch/select?fq=path0_s:%22PubMed_abstracts%22&fq=file_modified_dt:[2019-04-02T00:00:00Z%20TO%202019-04-10T23:59:59Z]&q=cleaned_html_content_txt%3A%22blood%22&rows=500'
#solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results('blood',url_query,'Diabetes','','', tags='tagged_entities_for_web', from_date=None, to_date=None)

#url_query = get_company_pr_solr_url('GlaxoSmithKline plc')
#solr_results, journal_docid_list, author_docid_list, institution_docid_list = get_solr_results('', url_query, tags="tagged_entities_for_web")

#solr_results = get_solr_results_from_path('', "PubMed_abstracts/Archive/28/18/87/28188715.xml.gz")
#solr_results = get_solr_results_from_path('sickle cell disease', "PubMed_abstracts/Archive/30/04/43/30044354.xml.gz")
#solr_results = get_solr_results('multiple sclerosis', url_query, tags='tagged_entities_for_web')


#solr_results, daily_stats = get_daily_stats(datetime.date(2019, 2, 14))
#save_daily_stats(daily_stats)
        
        
#print(solr_results)

#url_query = get_solr_search_url(['multiple sclerosis'])
#solr_results = get_solr_results('multiple sclerosis', url_query, tags='tagged_entities_for_web')

#len(solr_results['shorter_sentences'][0])

#from_date = datetime.date.today() - datetime.timedelta(days=1)
#to_date = datetime.date.today()

#julias_alerts, julias_alert_ids = get_ome_alerts_of_user('julia.gray')
#clean_keyword_list, clean_keyword_title = get_keyword_list_from_ome_alert_id('124')
#clean_keyword_list, clean_keyword_title = get_search_params_list('124')
#ome_alert_results, url_query = get_ome_alert_results(clean_keyword_list, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')

#print('')
#print('------------------------------------')
#print('')
#from_date = datetime.date(2020,8,6)
#from_date = datetime.date.today() - datetime.timedelta(days=1)
#to_date = datetime.date(2020,8,6)
#to_date = datetime.date.today()
#internal_users = ['cody.schiffer']
#test_search_term_list, test_alert_title, search_list = get_search_params_list('485')
#test_ome_alert_results, test_url_query = get_ome_alert_results(test_search_term_list,search_list ,from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')



#get_solr_results(all_keywords_list, params['keyword'] ,url_query, params['journal_select'], params['author_select'], params['institution_select'], filter_leeway, tags=tags, from_date=from_date, to_date=to_date)

#test_search_terms = {'keyphrase1':'multiple sclerosis', 'keyphrase2':'efficacy', 'source_select':'Press releases'}
#test_url = construct_solr_search_url('psoriasis', from_date=from_date)


#doc_text = ome_alert_results['tagged_document_text'][0]
#doc_tags = ome_alert_results['normalized_tags'][0]

#tagged_doc_text = add_tagged_entities.highlight_tags_from_list(doc_text, doc_tags)
#test_text = ' '.join(text_to_sentences("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nCoronary artery plaque characteristics and treatment with biologic therapy in severe psoriasis: results from a prospective observational study | Cardiovascular Research | Oxford Academic\n\n\n    \n            \n            \n\n            \n    \n    \n    Skip to Main Content\n    \n\n\n\n\n\n\n\n\t\n\n\n        \n\n        \n        \n        \n        \n        \n\n        \n\n        \n    \n        \n                \n        \n    \n    \n        \n\n\n    \n\n\n\n    \n\n\n    \n\n\n    \n        \n\n            \n                \n            \n\n\n            \t\n                    \n                        Search\n                    \n                \n\t\n                    \n                        Account Menu\n                    \n                \n\t\n                    \n                        Menu\n                    \n                \n\t\n                    \n                        \nSign In                        \n                    \n                    \n                        \n\n                    \n\n                \n\tRegister\n\n\n        \n\n    \n\n\n\n\n    \n    \n        \n            \n                \n                    Navbar Search Filter\n                    All  Cardiovascular Research\nAll  ESC Family\nAll  Journals\n\n\n\n\n\n\n\n                    Mobile Microsite Search Term\n                    \n\n                    \n\n                \n\n            \n\n        \n\n    \n\n    \n    \n        \t\n                \n                    \nSign In                    \n                \n                \t\n                        \n\n                    \n\n\n            \n\t\n                    Register\n                \n\n\n    \n\n    \n    \n\n\n    \n    \t\n            Issues\n            \n        \n\t\n            Onlife\n            \n        \n\t\n            More Content\n                \n    \t\n            Advance articles\n            \n        \n\t\n            Editor's Choice\n            \n        \n\n\n\n        \n\t\n            Submit\n                \n    \t\n            Author Guidelines\n            \n        \n\t\n            Submission Site\n            \n        \n\t\n            Order Offprints\n            \n        \n\t\n            Open Access Options\n            \n        \n\n\n\n        \n\t\n            Purchase\n            \n        \n\t\n            Alerts\n            \n        \n\t\n            About\n                \n    \t\n            About Cardiovascular Research\n            \n        \n\t\n            About the European Society of Cardiology\n            \n        \n\t\n            ESC Journal Family\n            \n        \n\t\n            Journals Career Network\n            \n        \n\t\n            Editorial Board\n            \n        \n\t\n            Advertising and Corporate Services\n            \n        \n\t\n            Self-Archiving Policy\n            \n        \n\t\n            Dispatch Dates\n            \n        \n\t\n            Terms and Conditions\n            \n        \n\n\n\n        \n\n\n    \n\n\n\n\n\n\n    \n        \n                \n\n            \n\n                \n            \n                    \n                            \n                                \n                            \n                                            \n\n            \n \n        \n\n    \n\n\n\n    \n        \n\n\n    \n    \t\n            Issues\n            \n        \n\t\n            Onlife\n            \n        \n\t\n            More Content\n                \n    \t\n            Advance articles\n            \n        \n\t\n            Editor's Choice\n            \n        \n\n\n\n        \n\t\n            Submit\n                \n    \t\n            Author Guidelines\n            \n        \n\t\n            Submission Site\n            \n        \n\t\n            Order Offprints\n            \n        \n\t\n            Open Access Options\n            \n        \n\n\n\n        \n\t\n            Purchase\n            \n        \n\t\n            Alerts\n            \n        \n\t\n            About\n                \n    \t\n            About Cardiovascular Research\n            \n        \n\t\n            About the European Society of Cardiology\n            \n        \n\t\n            ESC Journal Family\n            \n        \n\t\n            Journals Career Network\n            \n        \n\t\n            Editorial Board\n            \n        \n\t\n            Advertising and Corporate Services\n            \n        \n\t\n            Self-Archiving Policy\n            \n        \n\t\n            Dispatch Dates\n            \n        \n\t\n            Terms and Conditions\n            \n        \n\n\n\n        \n\n\n        \n            \n                Close\n\n                \n                    \n                        search filter\n                        All  Cardiovascular Research\nAll  ESC Family\nAll  Journals\n\n\n\n                        search input\n                        \n\n                        \n\n                    \n\n                \n\n                Advanced Search\n\n            \n\n            \n\n    \n\n\n\n\n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n    \n\n    \n\n\n        \n        \n            \n                \n                    \n    \n        \n            \n                Article Navigation\n            \n\n            \n                \n                \n                    Close mobile search navigation\n                \n                Article navigation\n\n\n                    \n                    \n\n                    \n                            \n        \n\nArticle Contents\n\n\t\n            \n\n                Abstract\n            \n\n        \n\t\n            \n\n                1. Introduction\n            \n\n        \n\t\n            \n\n                2. Methods\n            \n\n        \n\t\n            \n\n                3. Results\n            \n\n        \n\t\n            \n\n                4. Discussion\n            \n\n        \n\t\n            \n\n                5. Conclusions\n            \n\n        \n\t\n            \n\n                Authors’ contributions\n            \n\n        \n\t\n            \n\n                Footnotes\n            \n\n        \n\t\n            \n\n                References\n            \n\n        \n\n\n\n    \n\n\n\t                \n\n            \n                    \n                \n\n            \n\n        \n \n    \n        \n            \n             \n                \n                    \n                        Article Navigation\n                    \n                \n\n            \n\n\n            \n                    \n        \n\n    \n\n    \n        \n                    Corrected Proof\n\n            \n\n\n\n    \n                Coronary artery plaque characteristics and treatment with biologic therapy in severe psoriasis: results from a prospective observational study\n                \n\n                \n                    \n                            \n                                    \n\n                                        \n\n\n\n    \n        Youssef A Elnabawi\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Youssef A Elnabawi\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Amit K Dey\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Amit K Dey\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Aditya Goyal\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Aditya Goyal\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Jacob W Groenendyk\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Jacob W Groenendyk\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Jonathan H Chung\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Jonathan H Chung\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Agastya D Belur\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Agastya D Belur\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Justin Rodante\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Justin Rodante\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Charlotte L Harrington\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Charlotte L Harrington\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Heather L Teague\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Heather L Teague\n                                    \n                                    \n\n                                        \n\n\n\n    \n        Yvonne Baumer\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                        \n                                        Yvonne Baumer\n                                    \n                                \n                                    ... Show more\n                                \n                                        \n\n                                            \n\n\n\n    \n        Andrew Keel\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Andrew Keel\n                                        \n                                        \n\n                                            \n\n\n\n    \n        Martin P Playford\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Martin P Playford\n                                        \n                                        \n\n                                            \n\n\n\n    \n        Veit Sandfort\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Veit Sandfort\n                                        \n                                        \n\n                                            \n\n\n\n    \n        Marcus Y Chen\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Marcus Y Chen\n                                        \n                                        \n\n                                            \n\n\n\n    \n        Benjamin Lockshin\n\n    \n\n\n        \n            DermAssociates, Silver Spring, MD, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Benjamin Lockshin\n                                        \n                                        \n\n                                            \n\n\n\n    \n        Joel M Gelfand\n\n    \n\n\n        \n            Department of Dermatology, University of Pennsylvania, Philadelphia, PA, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Joel M Gelfand\n                                        \n                                        \n\n                                            \n\n\n\n    \n        David A Bluemke\n\n    \n\n\n        \n            Department of Radiology, University of Wisconsin, Madison, WI, USA\n        \n\n\n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            David A Bluemke\n                                        \n                                        \n\n                                            \n\n\n\n    \n        Nehal N Mehta\n\n    \n\n\n        \n            Section of Inflammation and Cardiometabolic Disease, National Heart, Lung, and Blood Institute; National Institutes of Health, Bethesda, MD, USA\n        \n\n\n                \n                    \n                \n\n\n        \n            Corresponding author. Tel: +1 301 827 0483; fax: +1 301 827 0915, E-mail: nehal.mehta@nih.gov\n        \n\n\n\n\n        \n            Search for other works by this author on:\n        \n\n            \n                Oxford Academic\n            \n\n            \n                PubMed\n            \n\n            \n                Google Scholar\n            \n\n\n\n\n                                            \n                                            Nehal N Mehta\n                                        \n                                \n\n                            \n\n\n                    \n\n                \n\n            \n\n                    \n                        Cardiovascular Research, cvz009, https://doi.org/10.1093/cvr/cvz009\n\n                    \n\n                    \n                        \n                            Published:\n\n                            05 February 2019\n\n                        \n\n                            \n                                \n                                    Article history\n                                \n\n                            \n\n                    \n\n                                    \n                            \n                                Received:\n\n                                24 October 2018\n\n                            \n\n                            \n                                Revision Received:\n\n                                17 December 2018\n\n                            \n\n                            \n                                Accepted:\n\n                                12 January 2019\n\n                            \n\n\n                        Close\n\n                    \n\n            \n\n\n    \n\n\n\n\n\n\n\n    \n\n    \n        \n\n\n    \n\n\n        \n                \n                                    \n                    \n                        \t\n                                \n                                    \n                                    \n                                        Views\n\n                                        \n                                    \n\n                                \n                                \n\n\n                                    \n\tArticle contents\n\tFigures & tables\n\tVideo\n\tAudio\n\tSupplementary Data\n\n\n                            \n                                \t\n        \n            PDF\n        \n    \n\t\n                                    \n        \nCite\n\n\n    Citation\n\n    Youssef A Elnabawi, Amit K Dey, Aditya Goyal, Jacob W Groenendyk, Jonathan H Chung, Agastya D Belur, Justin Rodante, Charlotte L Harrington, Heather L Teague, Yvonne Baumer, Andrew Keel, Martin P Playford, Veit Sandfort, Marcus Y Chen, Benjamin Lockshin, Joel M Gelfand, David A Bluemke, Nehal N Mehta;  Coronary artery plaque characteristics and treatment with biologic therapy in severe psoriasis: results from a prospective observational study, Cardiovascular Research, , cvz009, https://doi.org/10.1093/cvr/cvz009\n\n    Download citation file:\n  \n    \tRis (Zotero)\n\tEndNote\n\tBibTex\n\tMedlars\n\tProCite\n\tRefWorks\n\tReference Manager\n\n\n    \n\n    \n    © 2019 Oxford University Press\n\n    Close\n\n\n    \n\n \n                            \n\t\n                                \n                                    \n            \n            Permissions\n    \n\n\n    \n\n\n                            \n\t\n                                \n                                    \n                                    \n                                        Share\n\n                                        \n                                    \n\n                                \n                                \n\n\n                                    \n\tEmail\n\tTwitter\n\tFacebook\n\n\n                            \n                        \n                    \n                        \n                                \n        \n\n\n\n\n    \n    \n        \n            \n                \n                    Navbar Search Filter\n                    All  Cardiovascular Research\nAll  ESC Family\nAll  Journals\n\n\n\n\n\n\n\n                    Mobile Microsite Search Term\n                    \n\n                    \n\n                \n\n            \n\n        \n\n    \n\n    \n    \n        \t\n                \n                    \nSign In                    \n                \n                \t\n                        \n\n                    \n\n\n            \n\t\n                    Register\n                \n\n\n    \n\n    \n    \n\n    \n\n\n\n\n\n\n\n\n    \n        \n\n        \n            \n                Close\n\n                \n                    \n                        search filter\n                        All  Cardiovascular Research\nAll  ESC Family\nAll  Journals\n\n\n\n                        search input\n                        \n\n                        \n\n                    \n\n                \n\n                Advanced Search\n\n            \n\n            \n\n    \n\n\n\n\n\n    \n\n\n                        \n\n                    \n                    \n                \n\n                    \n                            \n        \n    \n\n\n\n\n\n                            Abstract\n\nAims\nThe use of biologic therapy has increased over the past decade well beyond primary autoimmune diseases. Indeed, a recent trial using an anti-IL-1beta antibody reduced second myocardial infarction (MI) in those who have had MI. Psoriasis is a chronic inflammatory disease often treated with biologics when severe, is associated with increased risk of MI, in part driven by high-risk coronary plaque phenotypes by coronary computed tomography angiography (CCTA). We hypothesized that we would observe a reduction in inflammatory-driven phenotypes of coronary plaque, including non-calcified coronary plaque burden and lipid-rich necrotic core in those treated with biologic therapy after one-year compared with non-biologic therapy.\nMethods and results\nIn a prospective, observational study, 290 participants were recruited from 1 January 2013 through 31 October 2018 with 215 completing one-year follow-up. Of the 238, 121 consecutive participants who were biologic treatment naïve at baseline were included. A blinded reader (blinded to patient demographics, visit and treatment) quantified total coronary plaque burden and plaque subcomponents (calcified and non-calcified) in the three main coronary vessels >2 mm using dedicated software (QAngio, Medis, Netherlands). Psoriasis patients were middle-aged [mean (standard deviation) age, 50.5 (12.1) years], mostly male (n = 70, 58%) with low cardiovascular risk by Framingham score [median (interquartile range, IQR), 3 (1–6)] and had moderate to severe skin disease at baseline [median (IQR) Psoriasis Area Severity Index, PASI, 8.6 (5.3–14.0)]. Biologic therapy was associated with a 6% reduction in non-calcified plaque burden (P = 0.005) reduction in necrotic core (P = 0.03), with no effect on fibrous burden (P = 0.71). Decrease in non-calcified plaque burden in the biologic treated group was significant compared with slow plaque progression in non-biologic treated (Δ, −0.07 mm2 vs. 0.06 mm2; P = 0.02) and associated with biologic treatment beyond adjustment for traditional cardiovascular risk factors (β = 0.20, P = 0.02).\nConclusion\nIn this observational study, we demonstrate that biologic therapy in severe psoriasis was associated with favourable modulation of coronary plaque indices by CCTA. These findings highlight the importance of systemic inflammation in coronary artery disease and support the conduct of larger, randomized trials.\n                        \n\nPsoriasis, CCTA, Coronary artery disease, Biologic therapy, Coronary plaque characteristics\n                            1. Introduction\n\nCardiovascular disease remains the leading cause of death, with residual risk due to inflammation being an emerging critical target.1,2 In a recent study of patients with myocardial infarction (MI) and high residual inflammatory risk (high sensitivity C-reactive protein >2 mg/L), canakinumab, a monoclonal antibody targeting interleukin-1β (IL-1β), decreased the rate of non-fatal MI, non-fatal stroke, and cardiovascular death without affecting cholesterol levels.3 Findings from the study support the need to expand our understanding of potential effects of biologic therapies on coronary vasculature.\nPsoriasis is a chronic inflammatory skin disease associated with accelerated atherosclerosis affecting about 3% of the population. Severe psoriasis is associated with early MI risk by over 50%,4 with rates of coronary artery disease being similar to Type 2 diabetes.5 The inflammatory milieu of psoriatic skin harbours cytokines critical to early atherogenesis and plaque rupture, with derangements in pro-inflammatory and pro-atherogenic cytokines, such as IL-1β, interleukin-17 (IL-17), and tumour necrosis factor-α (TNF-α).\nPsoriasis, when severe, is treated with biologic therapy. This provides a reliable model to study inflammatory atherogenesis and the longitudinal impact of modulating specific cytokines on vascular behaviour, while treating the primary skin disease with FDA approved biologic therapies.6 In this context, the aim of this study was to perform coronary artery plaque characterization before and after biological therapy in an open-label, one-year follow up study. We hypothesized that these inflammatory driven phenotypes of coronary plaque, including lipid-rich, non-calcified coronary plaque burden, and lipid-rich necrotic core, would decrease following biological therapy compared with patients not treated with biologic therapy after one-year.\n                            2. Methods\n\n                            2.1 Study design and population\n\nIn a prospective, observational study, 290 participants participating in an ongoing cohort study to understand the association between psoriasis and cardiometabolic disease under the Psoriasis, Atherosclerosis and Cardiometabolic Disease Initiative were recruited from 1 January 2013 through 31 October 2018 with 238 completing one-year follow-up and 121 consecutive patients meeting the inclusion criteria (Supplementary material online, Figure S1). Detailed inclusion and exclusion criteria of the study have been previously reported.7 A study provider confirmed the onset and duration of psoriasis and assessed psoriasis severity using the Psoriasis Area and Severity Index (PASI) score, which combines the severity of lesions and the area affected into a single score, considering erythema, induration, and desquamation within each lesion. Previous psoriasis literature has established that the degree of PASI score response defined as greater than 50% improvement is clinically significant and denotes meaningful improvement.8 For this study, only participants who were naïve to biologic or systemic therapies at baseline were included and followed for one year with clinical and laboratory data as well as serial coronary computed tomography angiography (CCTA). Biologic therapy initiation was performed one day to one month after the initial visit whereby an independent dermatologist started treatment. Treatment agents included TNF-α inhibitors (adalimumab, etanercept), interleukin-12/23 inhibitor (ustekinumab), and interleukin-17 inhibitors (secukinumab, ixekizumab). Participants who elected to not receive biologic therapy at their follow-up visit were used as a referent group and were treated with topical and/or light therapies only. Individuals on systemic therapies or started on statin treatment over the course of the one-year study period were excluded. Study protocols were approved by the institutional review board at the National Institutes of Health and all participants provided written informed consent. The study was in accordance with the Declaration of Helsinki. Strengthening the reporting of observational studies in epidemiology guidelines were followed for reporting the findings.9\n                            2.2 Sample size calculations\n\nModulation of the primary outcome, non-calcified plaque burden, was assessed on a per-artery basis, yielding 363 total arteries in a cohort of 121 study subjects based on prior published methods.10,11 We hypothesized a 15% difference in non-calcified plaque burden with a standard deviation (SD) of 0.5 between treatment groups. Thus, the evaluation of 182 arteries was required for a study with 90% power.\n                            2.3 Coronary computed tomography angiography\n\n                            2.3.1 Acquisition\n\nAll patients underwent CCTA on the same day as blood draw, using the same CT scanner (320-detector row Aquilion ONE ViSION, Toshiba, Japan). Guidelines implemented by the NIH Radiation Exposure Committee were followed. Scans were performed with prospective EKG gating, 100 or 120 kV tube potential, tube current of 100–850 mA adjusted to the patient’s body size, with a gantry rotation time of 275 ms. Images were acquired at a slice thickness of 0.5 mm with a slice increment of 0.25 mm.\n                            2.3.2 Analysis\n\nAll scans were read in a blinded fashion to patient characteristics, visit date, and treatment. Coronary plaque characteristics were analysed across each of the main coronary arteries >2 mm using dedicated software (QAngio CT, Medis; The Netherlands).10,11 Automated longitudinal contouring of the inner lumen and outer wall was performed and results were manually adjusted when clear deviations were present.12 Results of the automated contouring were also reviewed on transverse reconstructed cross-sections of the artery on a section-by-section basis at 0.25-mm increments. Lumen attenuation was adaptively corrected on an individual scan basis using gradient filters and intensity values within the artery. Intra-rater reliability was high, with intra-class correlation coefficient = 0.900, 95% CI (0.903–0.919).\nTo account for variable coronary artery lengths, plaque volume (in cubic millimetres) was divided by the corresponding segment length (in millimetres), yielding a plaque index.9 Total plaque burden was defined as the sum of calcified plaque burden and non-calcified plaque burden. Non-calcified plaque subcomponents were obtained after adaptively correcting for lumen attenuation and depicted based on Hounsfield Units derived by the software.\n                            2.4 Clinical data and laboratory measurements\n\nUpon recruitment of participants, initial contact with investigators involved a comprehensive medical history, physical examination, medication evaluation, and anthropometric measurements. Blood samples were collected after an overnight fast. Samples were analysed for basic chemistry, complete lipid panel, insulin, and high sensitivity C-reactive protein at the NIH Clinical Center. Cholesterol efflux capacity was measured using a validated ex vivo assay of J774 cholesterol-loaded macrophages as previously published.11 Blood inflammatory markers including interferon-γ, TNF-α, and cytokines were quantified using multiplex ELISA assays (Mesoscale Diagnostics, Gaithersburg, MD, USA).\n                            2.5 Statistical analysis\n\nSkewness and kurtosis measures were considered to assess normality. Data were reported as mean with SD for parametric variables, median with interquartile range (IQR) for non-parametric variables and as percentages for categorical variables. Parametric variables were compared between two groups using paired t-test. Non-parametric variables were compared using Wilcoxon signed-rank test and Pearson’s χ2 test was performed for categorical variables between two groups. We conducted Spearman’s rank order correlation coefficient to evaluate the relationship between non-calcified plaque burden and different cardiometabolic risk factors.\nTo understand the change in various coronary parameters over one-year follow up, we used paired t-test for parametric variables, Wilcoxon signed-rank test for non-parametric variables and Pearson’s χ2 test for categorical variables. The change in coronary parameters over one-year was compared between groups using paired t-test. We performed multi-variable linear regression analysis and adjusted for Framingham risk score, body mass index, and statin use. A two-tailed P-value <0.05 was considered statistically significant. Statistical analysis was performed using STATA-12 software (STATA Inc., College Station, TX, USA).\n                            3. Results\n\n                            3.1 Baseline characteristics of study groups\n\nStudy participants were middle-aged [mean (SD) age, 50.4 (12.1) years], mostly male (n = 70, 58%) with low cardiovascular risk by Framingham score [median (IQR), 3 (1–6)] and had moderate to severe skin disease at baseline [median (IQR) PASI, 8.6 (5.3–14.0)] (Table 1). There were no significant differences in demographic characteristics, in baseline medication use or laboratory values between the two groups along with no biologic or systemic therapy use at baseline in either group. \nTable 1\nBaseline and one-year follow-up characteristics of patients with psoriasis\n\n \n\tParameters \tBiologic treated (n = 89)\n \tNon-biologic treated (n = 32)\n \tAt baselinea \n\t \tBaseline \tOne-year \tP-value \tBaseline \tOne-year \tP-value \tP-value \n\tDemographics and medical history \n\t Age (years) \t49.1 ± 12.2 \t50.2 ± 12.2 \t– \t51.2 ± 12.0 \t53.1 ± 12.3 \t– \t0.35 \n\t Males \t50 (56) \t50 (56) \t– \t20 (63) \t20 (63) \t– \t0.65 \n\t Body mass index \t29.9 ± 6.0 \t29.6 ± 6.1 \t0.18 \t29.4 ± 5.6 \t29.0 ± 5.4 \t0.06 \t0.57 \n\t Hypertension \t27 (30) \t26 (29) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.63 \n\t Hyperlipidaemia \t32 (36) \t30 (34) \t0.76 \t14 (44) \t14 (44) \t1.00 \t0.46 \n\t Statin treatment \t25 (28) \t22 (25) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.92 \n\t Type-2 diabetes mellitus \t8 (9) \t6 (7) \t0.16 \t2 (6) \t3 (9) \t0.32 \t0.60 \n\t Current smoker \t9 (10) \t7 (8) \t0.18 \t4 (13) \t4 (13) \t1.00 \t0.59 \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t181.3 ± 33.3 \t181.2 ± 36.0 \t0.49 \t184.4 ± 38.5 \t183.4 ± 41.2 \t0.43 \t0.50 \n\t HDL cholesterol (mg/dL) \t53.8 ± 14.2 \t54.7 ± 16.2 \t0.17 \t53.4 ± 16.2 \t55.8 ± 19.5 \t0.16 \t0.79 \n\t LDL cholesterol (mg/dL) \t105.6 ± 28.0 \t102.4 ± 33.0 \t0.19 \t103.1 ± 28.2 \t98.8 ± 35.9 \t0.25 \t0.51 \n\t Framingham risk score \t3 (1–6) \t2 (1–5) \t0.15 \t3 (2–7) \t4 (1–7) \t0.65 \t0.42 \n\t C-reactive protein \t2.0 (0.8–5.0) \t1.4 (0.7–3.6) \t<0.001 \t2.3 (0.6–4.5) \t1.8 (0.7–3.8) \t0.21 \t0.71 \n\t HOMA-IR \t3.1 (2.0–5.6) \t2.9 (1.9–4.9) \t0.11 \t2.6 (1.6–4.9) \t2.7 (1.8–5.3) \t0.57 \t0.59 \n\tPsoriasis characterization \n\t PASI score \t9.0 (5.6–15.0) \t3.2 (1.8–5.7) \t<0.001 \t8.1 (5.0–12.0) \t7.0 (4.0–9.9) \t0.08 \t0.64 \n\t Disease duration \t23.0 ± 14.4 \t24.0 ± 14.7 \t– \t20.3 ± 14.6 \t21.3 ± 17.1 \t– \t0.48 \n\t Topical therapy \t56 (63) \t39 (44) \t0.03 \t22 (69) \t25 (78) \t0.32 \t0.62 \n\t Light therapy \t16 (18) \t11 (12) \t0.25 \t9 (28) \t10 (31) \t0.66 \t0.08 \n\t Systemic therapy \t0 (0) \t0 (0) \t– \t0 (0) \t0 (0) \t– \t1.00 \n\n\n\tParameters \tBiologic treated (n = 89)\n \tNon-biologic treated (n = 32)\n \tAt baselinea \n\t \tBaseline \tOne-year \tP-value \tBaseline \tOne-year \tP-value \tP-value \n\tDemographics and medical history \n\t Age (years) \t49.1 ± 12.2 \t50.2 ± 12.2 \t– \t51.2 ± 12.0 \t53.1 ± 12.3 \t– \t0.35 \n\t Males \t50 (56) \t50 (56) \t– \t20 (63) \t20 (63) \t– \t0.65 \n\t Body mass index \t29.9 ± 6.0 \t29.6 ± 6.1 \t0.18 \t29.4 ± 5.6 \t29.0 ± 5.4 \t0.06 \t0.57 \n\t Hypertension \t27 (30) \t26 (29) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.63 \n\t Hyperlipidaemia \t32 (36) \t30 (34) \t0.76 \t14 (44) \t14 (44) \t1.00 \t0.46 \n\t Statin treatment \t25 (28) \t22 (25) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.92 \n\t Type-2 diabetes mellitus \t8 (9) \t6 (7) \t0.16 \t2 (6) \t3 (9) \t0.32 \t0.60 \n\t Current smoker \t9 (10) \t7 (8) \t0.18 \t4 (13) \t4 (13) \t1.00 \t0.59 \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t181.3 ± 33.3 \t181.2 ± 36.0 \t0.49 \t184.4 ± 38.5 \t183.4 ± 41.2 \t0.43 \t0.50 \n\t HDL cholesterol (mg/dL) \t53.8 ± 14.2 \t54.7 ± 16.2 \t0.17 \t53.4 ± 16.2 \t55.8 ± 19.5 \t0.16 \t0.79 \n\t LDL cholesterol (mg/dL) \t105.6 ± 28.0 \t102.4 ± 33.0 \t0.19 \t103.1 ± 28.2 \t98.8 ± 35.9 \t0.25 \t0.51 \n\t Framingham risk score \t3 (1–6) \t2 (1–5) \t0.15 \t3 (2–7) \t4 (1–7) \t0.65 \t0.42 \n\t C-reactive protein \t2.0 (0.8–5.0) \t1.4 (0.7–3.6) \t<0.001 \t2.3 (0.6–4.5) \t1.8 (0.7–3.8) \t0.21 \t0.71 \n\t HOMA-IR \t3.1 (2.0–5.6) \t2.9 (1.9–4.9) \t0.11 \t2.6 (1.6–4.9) \t2.7 (1.8–5.3) \t0.57 \t0.59 \n\tPsoriasis characterization \n\t PASI score \t9.0 (5.6–15.0) \t3.2 (1.8–5.7) \t<0.001 \t8.1 (5.0–12.0) \t7.0 (4.0–9.9) \t0.08 \t0.64 \n\t Disease duration \t23.0 ± 14.4 \t24.0 ± 14.7 \t– \t20.3 ± 14.6 \t21.3 ± 17.1 \t– \t0.48 \n\t Topical therapy \t56 (63) \t39 (44) \t0.03 \t22 (69) \t25 (78) \t0.32 \t0.62 \n\t Light therapy \t16 (18) \t11 (12) \t0.25 \t9 (28) \t10 (31) \t0.66 \t0.08 \n\t Systemic therapy \t0 (0) \t0 (0) \t– \t0 (0) \t0 (0) \t– \t1.00 \n\n\nValues are reported as mean ± SD or median (IQR) for continuous data and N (%) for categorical data. Two-tailed P-values less than 0.05 deemed significant (bold values).\n\n\nHOMA-IR, homeostatic model assessment of insulin resistance; PASI, Psoriasis Area and Severity Index.\n\n\na\nComparison between groups at baseline.\n\n\n\n\n\nTable 1\nBaseline and one-year follow-up characteristics of patients with psoriasis\n\n \n\tParameters \tBiologic treated (n = 89)\n \tNon-biologic treated (n = 32)\n \tAt baselinea \n\t \tBaseline \tOne-year \tP-value \tBaseline \tOne-year \tP-value \tP-value \n\tDemographics and medical history \n\t Age (years) \t49.1 ± 12.2 \t50.2 ± 12.2 \t– \t51.2 ± 12.0 \t53.1 ± 12.3 \t– \t0.35 \n\t Males \t50 (56) \t50 (56) \t– \t20 (63) \t20 (63) \t– \t0.65 \n\t Body mass index \t29.9 ± 6.0 \t29.6 ± 6.1 \t0.18 \t29.4 ± 5.6 \t29.0 ± 5.4 \t0.06 \t0.57 \n\t Hypertension \t27 (30) \t26 (29) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.63 \n\t Hyperlipidaemia \t32 (36) \t30 (34) \t0.76 \t14 (44) \t14 (44) \t1.00 \t0.46 \n\t Statin treatment \t25 (28) \t22 (25) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.92 \n\t Type-2 diabetes mellitus \t8 (9) \t6 (7) \t0.16 \t2 (6) \t3 (9) \t0.32 \t0.60 \n\t Current smoker \t9 (10) \t7 (8) \t0.18 \t4 (13) \t4 (13) \t1.00 \t0.59 \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t181.3 ± 33.3 \t181.2 ± 36.0 \t0.49 \t184.4 ± 38.5 \t183.4 ± 41.2 \t0.43 \t0.50 \n\t HDL cholesterol (mg/dL) \t53.8 ± 14.2 \t54.7 ± 16.2 \t0.17 \t53.4 ± 16.2 \t55.8 ± 19.5 \t0.16 \t0.79 \n\t LDL cholesterol (mg/dL) \t105.6 ± 28.0 \t102.4 ± 33.0 \t0.19 \t103.1 ± 28.2 \t98.8 ± 35.9 \t0.25 \t0.51 \n\t Framingham risk score \t3 (1–6) \t2 (1–5) \t0.15 \t3 (2–7) \t4 (1–7) \t0.65 \t0.42 \n\t C-reactive protein \t2.0 (0.8–5.0) \t1.4 (0.7–3.6) \t<0.001 \t2.3 (0.6–4.5) \t1.8 (0.7–3.8) \t0.21 \t0.71 \n\t HOMA-IR \t3.1 (2.0–5.6) \t2.9 (1.9–4.9) \t0.11 \t2.6 (1.6–4.9) \t2.7 (1.8–5.3) \t0.57 \t0.59 \n\tPsoriasis characterization \n\t PASI score \t9.0 (5.6–15.0) \t3.2 (1.8–5.7) \t<0.001 \t8.1 (5.0–12.0) \t7.0 (4.0–9.9) \t0.08 \t0.64 \n\t Disease duration \t23.0 ± 14.4 \t24.0 ± 14.7 \t– \t20.3 ± 14.6 \t21.3 ± 17.1 \t– \t0.48 \n\t Topical therapy \t56 (63) \t39 (44) \t0.03 \t22 (69) \t25 (78) \t0.32 \t0.62 \n\t Light therapy \t16 (18) \t11 (12) \t0.25 \t9 (28) \t10 (31) \t0.66 \t0.08 \n\t Systemic therapy \t0 (0) \t0 (0) \t– \t0 (0) \t0 (0) \t– \t1.00 \n\n\n\tParameters \tBiologic treated (n = 89)\n \tNon-biologic treated (n = 32)\n \tAt baselinea \n\t \tBaseline \tOne-year \tP-value \tBaseline \tOne-year \tP-value \tP-value \n\tDemographics and medical history \n\t Age (years) \t49.1 ± 12.2 \t50.2 ± 12.2 \t– \t51.2 ± 12.0 \t53.1 ± 12.3 \t– \t0.35 \n\t Males \t50 (56) \t50 (56) \t– \t20 (63) \t20 (63) \t– \t0.65 \n\t Body mass index \t29.9 ± 6.0 \t29.6 ± 6.1 \t0.18 \t29.4 ± 5.6 \t29.0 ± 5.4 \t0.06 \t0.57 \n\t Hypertension \t27 (30) \t26 (29) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.63 \n\t Hyperlipidaemia \t32 (36) \t30 (34) \t0.76 \t14 (44) \t14 (44) \t1.00 \t0.46 \n\t Statin treatment \t25 (28) \t22 (25) \t0.71 \t10 (31) \t9 (28) \t0.32 \t0.92 \n\t Type-2 diabetes mellitus \t8 (9) \t6 (7) \t0.16 \t2 (6) \t3 (9) \t0.32 \t0.60 \n\t Current smoker \t9 (10) \t7 (8) \t0.18 \t4 (13) \t4 (13) \t1.00 \t0.59 \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t181.3 ± 33.3 \t181.2 ± 36.0 \t0.49 \t184.4 ± 38.5 \t183.4 ± 41.2 \t0.43 \t0.50 \n\t HDL cholesterol (mg/dL) \t53.8 ± 14.2 \t54.7 ± 16.2 \t0.17 \t53.4 ± 16.2 \t55.8 ± 19.5 \t0.16 \t0.79 \n\t LDL cholesterol (mg/dL) \t105.6 ± 28.0 \t102.4 ± 33.0 \t0.19 \t103.1 ± 28.2 \t98.8 ± 35.9 \t0.25 \t0.51 \n\t Framingham risk score \t3 (1–6) \t2 (1–5) \t0.15 \t3 (2–7) \t4 (1–7) \t0.65 \t0.42 \n\t C-reactive protein \t2.0 (0.8–5.0) \t1.4 (0.7–3.6) \t<0.001 \t2.3 (0.6–4.5) \t1.8 (0.7–3.8) \t0.21 \t0.71 \n\t HOMA-IR \t3.1 (2.0–5.6) \t2.9 (1.9–4.9) \t0.11 \t2.6 (1.6–4.9) \t2.7 (1.8–5.3) \t0.57 \t0.59 \n\tPsoriasis characterization \n\t PASI score \t9.0 (5.6–15.0) \t3.2 (1.8–5.7) \t<0.001 \t8.1 (5.0–12.0) \t7.0 (4.0–9.9) \t0.08 \t0.64 \n\t Disease duration \t23.0 ± 14.4 \t24.0 ± 14.7 \t– \t20.3 ± 14.6 \t21.3 ± 17.1 \t– \t0.48 \n\t Topical therapy \t56 (63) \t39 (44) \t0.03 \t22 (69) \t25 (78) \t0.32 \t0.62 \n\t Light therapy \t16 (18) \t11 (12) \t0.25 \t9 (28) \t10 (31) \t0.66 \t0.08 \n\t Systemic therapy \t0 (0) \t0 (0) \t– \t0 (0) \t0 (0) \t– \t1.00 \n\n\nValues are reported as mean ± SD or median (IQR) for continuous data and N (%) for categorical data. Two-tailed P-values less than 0.05 deemed significant (bold values).\n\n\nHOMA-IR, homeostatic model assessment of insulin resistance; PASI, Psoriasis Area and Severity Index.\n\n\na\nComparison between groups at baseline.\n\n\n\n\n                            3.2 Relationship of non-calcified plaque burden with risk factors\n\nTable 2 demonstrates associations between non-calcified plaque burden and cardiometabolic risk factors. Non-calcified plaque burden was correlated with traditional cardiovascular risk factors, including male gender (β = 0.37; P < 0.001), body mass index, (β = 0.52; P < 0.001), hypertension (β = 0.24; P < 0.001), hyperlipidaemia (β = 0.10; P = 0.02), HDL cholesterol (β = −0.30; P < 0.001), Framingham risk score (β = 0.29; P < 0.001), C-reactive protein (β = 0.11, P = 0.005), and homeostatic model assessment insulin resistance score (HOMA-IR, β = 0.19; P < 0.001). Additionally, non-calcified plaque burden was correlated with skin disease severity as assessed by PASI score (β = 0.20; P < 0.001), which remained significant after adjustment for traditional cardiovascular risk factors and high sensitivity C-reactive protein (hsCRP) (β = 0.13; P < 0.001). \nTable 2\nMultivariable linear regressions for the associations between non-calcified coronary plaque burden and cardiovascular risk factors and psoriasis characterization\n\n \n\tParameters \tNon-calcified plaque burden (mm2) (n = 121) \n\tDemographics and medical history \tβ (P-value) \n\t Age (years) \t0.04 (0.40) \n\t Males \t0.37 (<0.001) \n\t Body mass index \t0.52 (<0.001) \n\t Hypertension \t0.24 (<0.001) \n\t Hyperlipidaemia \t0.10 (0.02) \n\t Type-2 diabetes mellitus \t0.05 (0.19) \n\t Current smoker \t0.10 (0.03) \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t−0.05 (0.45) \n\t HDL cholesterol (mg/dL) \t−0.30 (<0.001) \n\t LDL cholesterol (mg/dL) \t−0.01 (0.72) \n\t Framingham risk score \t0.29 (<0.001) \n\t C-reactive protein \t0.11 (0.005) \n\t HOMA-IR \t0.19 (<0.001) \n\tPsoriasis characterization \n\t PASI score \t0.20 (<0.001) \n\t Disease duration \t0.05 (0.24) \n\n\n\tParameters \tNon-calcified plaque burden (mm2) (n = 121) \n\tDemographics and medical history \tβ (P-value) \n\t Age (years) \t0.04 (0.40) \n\t Males \t0.37 (<0.001) \n\t Body mass index \t0.52 (<0.001) \n\t Hypertension \t0.24 (<0.001) \n\t Hyperlipidaemia \t0.10 (0.02) \n\t Type-2 diabetes mellitus \t0.05 (0.19) \n\t Current smoker \t0.10 (0.03) \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t−0.05 (0.45) \n\t HDL cholesterol (mg/dL) \t−0.30 (<0.001) \n\t LDL cholesterol (mg/dL) \t−0.01 (0.72) \n\t Framingham risk score \t0.29 (<0.001) \n\t C-reactive protein \t0.11 (0.005) \n\t HOMA-IR \t0.19 (<0.001) \n\tPsoriasis characterization \n\t PASI score \t0.20 (<0.001) \n\t Disease duration \t0.05 (0.24) \n\n\nAll data in the table is expressed as standardized β (P-value). Two-tailed P-values less than 0.05 deemed significant (bold values).\n\n\nHOMA-IR, homeostasis model assessment of insulin resistance; PASI, Psoriasis Area and Severity Index.\n\n\n\n\n\nTable 2\nMultivariable linear regressions for the associations between non-calcified coronary plaque burden and cardiovascular risk factors and psoriasis characterization\n\n \n\tParameters \tNon-calcified plaque burden (mm2) (n = 121) \n\tDemographics and medical history \tβ (P-value) \n\t Age (years) \t0.04 (0.40) \n\t Males \t0.37 (<0.001) \n\t Body mass index \t0.52 (<0.001) \n\t Hypertension \t0.24 (<0.001) \n\t Hyperlipidaemia \t0.10 (0.02) \n\t Type-2 diabetes mellitus \t0.05 (0.19) \n\t Current smoker \t0.10 (0.03) \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t−0.05 (0.45) \n\t HDL cholesterol (mg/dL) \t−0.30 (<0.001) \n\t LDL cholesterol (mg/dL) \t−0.01 (0.72) \n\t Framingham risk score \t0.29 (<0.001) \n\t C-reactive protein \t0.11 (0.005) \n\t HOMA-IR \t0.19 (<0.001) \n\tPsoriasis characterization \n\t PASI score \t0.20 (<0.001) \n\t Disease duration \t0.05 (0.24) \n\n\n\tParameters \tNon-calcified plaque burden (mm2) (n = 121) \n\tDemographics and medical history \tβ (P-value) \n\t Age (years) \t0.04 (0.40) \n\t Males \t0.37 (<0.001) \n\t Body mass index \t0.52 (<0.001) \n\t Hypertension \t0.24 (<0.001) \n\t Hyperlipidaemia \t0.10 (0.02) \n\t Type-2 diabetes mellitus \t0.05 (0.19) \n\t Current smoker \t0.10 (0.03) \n\tClinical and laboratory data \n\t Total cholesterol (mg/dL) \t−0.05 (0.45) \n\t HDL cholesterol (mg/dL) \t−0.30 (<0.001) \n\t LDL cholesterol (mg/dL) \t−0.01 (0.72) \n\t Framingham risk score \t0.29 (<0.001) \n\t C-reactive protein \t0.11 (0.005) \n\t HOMA-IR \t0.19 (<0.001) \n\tPsoriasis characterization \n\t PASI score \t0.20 (<0.001) \n\t Disease duration \t0.05 (0.24) \n\n\nAll data in the table is expressed as standardized β (P-value). Two-tailed P-values less than 0.05 deemed significant (bold values).\n\n\nHOMA-IR, homeostasis model assessment of insulin resistance; PASI, Psoriasis Area and Severity Index.\n\n\n\n\n                            3.3 Modulation of coronary plaque characteristic following treatment\n\nAt one-year follow-up (Table 1), we observed a significant improvement in psoriasis by PASI score in the biologic treated group (64% improvement, P < 0.001) and not in the non-biologic treated group [median (IQR), 8.1 (5.0–12.0) vs. 7 (4.0–9.9); P = 0.08]. There were no significant effects on body mass index, lipids, or glucose. A reduction in hsCRP was seen only in the biologic treated group [median (IQR), 2.0 mg/L (0.8–5.0) vs. 1.4 mg/L (0.7–3.6); P < 0.001]. No participants in either group started a new lipid lowering therapy during the study period.\nTable 3 summarizes measures of coronary artery disease burden as determined by CCTA. In those receiving biologic therapy, there was a 5% reduction in total coronary plaque burden [mean (SD), 1.30 mm2 (0.60) vs. 1.24 mm2 (0.60); P = 0.009], primarily driven by a reduction in non-calcified plaque burden [mean (SD), 1.22 mm2 (0.59) vs. 1.15 mm2 (0.60); P = 0.005] (Figure 1A and B). We observed no change in fibrous burden (P = 0.71), and there was a significant reduction in both fibro-fatty burden [mean (SD), 0.22 mm2 (0.19) vs. 0.10 mm2 (0.14); P = 0.004] and necrotic burden [mean (SD), 0.07 mm2 (0.19) vs. 0.03 mm2 (0.09); P = 0.03]. On the contrary, in those not receiving systemic or biologic therapy over one-year, there were no significant changes in total plaque burden [mean (SD), 1.28 mm2 (0.53) vs. 1.31 (0.48); P = 0.22] and non-calcified plaque burden [mean (SD), 1.19 mm2 (0.41) vs. 1.25 (0.10); P = 0.17] with no change in fibrous burden (4% decrease, P = 0.22), a significant increase in fibro-fatty burden (38% increase, P = 0.004) and non-significant increase in necrotic core (33% increase, P = 0.27) (Figure 2A and B). \nTable 3\nCoronary artery parameters by artery at baseline and one-year follow-up\n\n \n\tCoronary characterization \tBiologic treated (n = 267 arteries)\n \tNon-biologic treated (n = 96 arteries)\n \n\t \tBaseline \tOne-year \tChange (%) \tP-value \tBaseline \tOne-year \tChange (%) \tP-value \n\tTotal plaque burden (mm2) \t1.30 ± 0.60 \t1.24 ± 0.60 \t−0.06 (−5) \t0.009 \t1.28 ± 0.53 \t1.31 ± 0.48 \t0.03 (2) \t0.22 \n\tDense-calcified plaque burden (mm2) \t0.064 ± 0.12 \t0.067 ± 0.14 \t0.003 (5) \t0.36 \t0.082 ± 0.17 \t0.084 ± 0.15 \t0.002 (2) \t0.48 \n\tNon-calcified plaque burden (mm2) \t1.22 ± 0.59 \t1.15 ± 0.60 \t−0.07 (−6) \t0.005 \t1.19 ± 0.41 \t1.25 ± 0.41 \t0.06 (5) \t0.17 \n\tPlaque morphology index \n\t Fibrous burden (mm2) \t0.99 ± 0.45 \t0.98 ± 0.51 \t−0.01 (−1) \t0.71 \t0.98 ± 0.32 \t0.94 ± .31 \t−0.04 (−4) \t0.22 \n\t Fibro-fatty burden (mm2) \t0.22 ± 0.19 \t0.10 ± 0.14 \t−0.12 (−55) \t0.004 \t0.16 ± 0.15 \t0.22 ± 0.14 \t0.06 (38) \t0.004 \n\t Necrotic burden (mm2) \t0.07 ± 0.19 \t0.03 ± 0.09 \t−0.04 (−57) \t0.03 \t0.06 ± 0.08 \t0.08 ± 0.22 \t0.02 (33) \t0.27 \n\n\n\tCoronary characterization \tBiologic treated (n = 267 arteries)\n \tNon-biologic treated (n = 96 arteries)\n \n\t \tBaseline \tOne-year \tChange (%) \tP-value \tBaseline \tOne-year \tChange (%) \tP-value \n\tTotal plaque burden (mm2) \t1.30 ± 0.60 \t1.24 ± 0.60 \t−0.06 (−5) \t0.009 \t1.28 ± 0.53 \t1.31 ± 0.48 \t0.03 (2) \t0.22 \n\tDense-calcified plaque burden (mm2) \t0.064 ± 0.12 \t0.067 ± 0.14 \t0.003 (5) \t0.36 \t0.082 ± 0.17 \t0.084 ± 0.15 \t0.002 (2) \t0.48 \n\tNon-calcified plaque burden (mm2) \t1.22 ± 0.59 \t1.15 ± 0.60 \t−0.07 (−6) \t0.005 \t1.19 ± 0.41 \t1.25 ± 0.41 \t0.06 (5) \t0.17 \n\tPlaque morphology index \n\t Fibrous burden (mm2) \t0.99 ± 0.45 \t0.98 ± 0.51 \t−0.01 (−1) \t0.71 \t0.98 ± 0.32 \t0.94 ± .31 \t−0.04 (−4) \t0.22 \n\t Fibro-fatty burden (mm2) \t0.22 ± 0.19 \t0.10 ± 0.14 \t−0.12 (−55) \t0.004 \t0.16 ± 0.15 \t0.22 ± 0.14 \t0.06 (38) \t0.004 \n\t Necrotic burden (mm2) \t0.07 ± 0.19 \t0.03 ± 0.09 \t−0.04 (−57) \t0.03 \t0.06 ± 0.08 \t0.08 ± 0.22 \t0.02 (33) \t0.27 \n\n\nValues are reported as mean ± SD for continuous data. Two-tailed P-values less than 0.05 deemed significant (bold values).\n\n\n\n\n\nTable 3\nCoronary artery parameters by artery at baseline and one-year follow-up\n\n \n\tCoronary characterization \tBiologic treated (n = 267 arteries)\n \tNon-biologic treated (n = 96 arteries)\n \n\t \tBaseline \tOne-year \tChange (%) \tP-value \tBaseline \tOne-year \tChange (%) \tP-value \n\tTotal plaque burden (mm2) \t1.30 ± 0.60 \t1.24 ± 0.60 \t−0.06 (−5) \t0.009 \t1.28 ± 0.53 \t1.31 ± 0.48 \t0.03 (2) \t0.22 \n\tDense-calcified plaque burden (mm2) \t0.064 ± 0.12 \t0.067 ± 0.14 \t0.003 (5) \t0.36 \t0.082 ± 0.17 \t0.084 ± 0.15 \t0.002 (2) \t0.48 \n\tNon-calcified plaque burden (mm2) \t1.22 ± 0.59 \t1.15 ± 0.60 \t−0.07 (−6) \t0.005 \t1.19 ± 0.41 \t1.25 ± 0.41 \t0.06 (5) \t0.17 \n\tPlaque morphology index \n\t Fibrous burden (mm2) \t0.99 ± 0.45 \t0.98 ± 0.51 \t−0.01 (−1) \t0.71 \t0.98 ± 0.32 \t0.94 ± .31 \t−0.04 (−4) \t0.22 \n\t Fibro-fatty burden (mm2) \t0.22 ± 0.19 \t0.10 ± 0.14 \t−0.12 (−55) \t0.004 \t0.16 ± 0.15 \t0.22 ± 0.14 \t0.06 (38) \t0.004 \n\t Necrotic burden (mm2) \t0.07 ± 0.19 \t0.03 ± 0.09 \t−0.04 (−57) \t0.03 \t0.06 ± 0.08 \t0.08 ± 0.22 \t0.02 (33) \t0.27 \n\n\n\tCoronary characterization \tBiologic treated (n = 267 arteries)\n \tNon-biologic treated (n = 96 arteries)\n \n\t \tBaseline \tOne-year \tChange (%) \tP-value \tBaseline \tOne-year \tChange (%) \tP-value \n\tTotal plaque burden (mm2) \t1.30 ± 0.60 \t1.24 ± 0.60 \t−0.06 (−5) \t0.009 \t1.28 ± 0.53 \t1.31 ± 0.48 \t0.03 (2) \t0.22 \n\tDense-calcified plaque burden (mm2) \t0.064 ± 0.12 \t0.067 ± 0.14 \t0.003 (5) \t0.36 \t0.082 ± 0.17 \t0.084 ± 0.15 \t0.002 (2) \t0.48 \n\tNon-calcified plaque burden (mm2) \t1.22 ± 0.59 \t1.15 ± 0.60 \t−0.07 (−6) \t0.005 \t1.19 ± 0.41 \t1.25 ± 0.41 \t0.06 (5) \t0.17 \n\tPlaque morphology index \n\t Fibrous burden (mm2) \t0.99 ± 0.45 \t0.98 ± 0.51 \t−0.01 (−1) \t0.71 \t0.98 ± 0.32 \t0.94 ± .31 \t−0.04 (−4) \t0.22 \n\t Fibro-fatty burden (mm2) \t0.22 ± 0.19 \t0.10 ± 0.14 \t−0.12 (−55) \t0.004 \t0.16 ± 0.15 \t0.22 ± 0.14 \t0.06 (38) \t0.004 \n\t Necrotic burden (mm2) \t0.07 ± 0.19 \t0.03 ± 0.09 \t−0.04 (−57) \t0.03 \t0.06 ± 0.08 \t0.08 ± 0.22 \t0.02 (33) \t0.27 \n\n\nValues are reported as mean ± SD for continuous data. Two-tailed P-values less than 0.05 deemed significant (bold values).\n\n\n\n\n                        \nFigure 1\nView largeDownload slide\n\nChange in coronary plaque burden components over one-year by treatment. (A) Percent change in coronary plaque burden components over one-year by treatment. (B) Change in non-calcified plaque burden over one-year by treatment.\n\n\nFigure 1\nView largeDownload slide\n\nChange in coronary plaque burden components over one-year by treatment. (A) Percent change in coronary plaque burden components over one-year by treatment. (B) Change in non-calcified plaque burden over one-year by treatment.\n\n\n                        \nFigure 2\nView largeDownload slide\n\nLeft anterior descending artery plaque identified before (2A) and after (2B) biologic therapy. (A) (a) Longitudinal planar and (b) curved planar reformat. (c and d) Representative cross-sectional views with colour overlay for plaque subcomponents. Lumen is encircled in yellow, vessel wall in orange with subcomponents in between, including fibrous (dark green), fibro-fatty (light green), necrotic (red), and dense-calcified (white). Non-calcified plaque burden = 1.03 mm2 and total atheroma volume = 99.2 mm3. (B) (a) Longitudinal planar and (b) curved planar reformat. (c and d) Representative cross-sectional views with colour overlay for plaque subcomponents. Lumen is encircled in yellow, vessel wall in orange with subcomponents in between, including fibrous (dark green), fibro-fatty (light green), necrotic (red), and dense-calcified (white). Non-calcified plaque burden = 0.85 mm2 and total atheroma volume = 80.6 mm3.\n\n\nFigure 2\nView largeDownload slide\n\nLeft anterior descending artery plaque identified before (2A) and after (2B) biologic therapy. (A) (a) Longitudinal planar and (b) curved planar reformat. (c and d) Representative cross-sectional views with colour overlay for plaque subcomponents. Lumen is encircled in yellow, vessel wall in orange with subcomponents in between, including fibrous (dark green), fibro-fatty (light green), necrotic (red), and dense-calcified (white). Non-calcified plaque burden = 1.03 mm2 and total atheroma volume = 99.2 mm3. (B) (a) Longitudinal planar and (b) curved planar reformat. (c and d) Representative cross-sectional views with colour overlay for plaque subcomponents. Lumen is encircled in yellow, vessel wall in orange with subcomponents in between, including fibrous (dark green), fibro-fatty (light green), necrotic (red), and dense-calcified (white). Non-calcified plaque burden = 0.85 mm2 and total atheroma volume = 80.6 mm3.\n\n\nWhen comparing change in plaque characteristics between groups over one-year, the decrease in non-calcified plaque burden in the biologic treated group was significant compared with non-biologic treated (Δ, −0.07 mm2 vs. 0.06 mm2; P = 0.03) and associated with biologic therapy even after adjustment for traditional cardiovascular risk factors, including Framingham risk score, body mass index, and statin use (β = 0.20, P = 0.02).\nWe performed an exploratory analysis in the biologic treated group by stratifying by treatment agents (anti-TNF, anti-IL12/23, and anti-IL17). There were no significant differences in demographic characteristics, in baseline medication use, or laboratory values between the three treatment groups (Supplementary material online, Table S1). After one-year of therapy, an improvement in hsCRP was observed in the anti-IL12/23 and anti-IL17 treated groups (P = 0.02 and P = 0.01; respectively). An improvement in HDL cholesterol was observed only in the anti-IL17 treated patients [mean (SD), 54.2 (19.9) vs. 61.2 (28.6); P = 0.03]. At baseline, there were no differences in coronary characteristics between the three groups. After one-year of therapy, we observed the following: a 5% reduction in non-calcified plaque burden on anti-TNF therapy (P = 0.06), a 2% reduction on anti-IL12/23 therapy (P = 0.36), and a 12% reduction on anti-IL17 (P = <0.001) (Table 4, Supplementary material online, Table S2). The reduction in coronary plaque burden observed on anti-IL17 therapy was significantly greater than that observed on anti-IL12/23 and no biologic treatment. Reduction in non-calcified coronary plaque burden on anti-TNF therapy was only significant when compared with non-biologic treated patients (P < 0.01). \nTable 4\nChange in non-calcified coronary plaque burden over one-year between treatment groups\n\n \n\tTreatments \tChange over one-year (mm2) (%) \tP-value \n\tAnti-TNF therapy (n = 48) \t−0.06 (−5) \t– \t \n\t vs. Anti-IL12/23 \t– \t−0.02 (−2) \t0.27 \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.08 \n\t vs. NBT \t– \t0.06 (5) \t0.009 \n\tAnti-IL12/23 therapy (n = 19) \t−0.02 (−2) \t– \t \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.01 \n\t vs. NBT \t– \t0.06 (5) \t0.09 \n\tAnti-IL17 therapy (n = 22) \t−0.15 (−12) \t– \t \n\t vs. NBT \t– \t0.06 (5) \t0.005 \n\n\n\tTreatments \tChange over one-year (mm2) (%) \tP-value \n\tAnti-TNF therapy (n = 48) \t−0.06 (−5) \t– \t \n\t vs. Anti-IL12/23 \t– \t−0.02 (−2) \t0.27 \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.08 \n\t vs. NBT \t– \t0.06 (5) \t0.009 \n\tAnti-IL12/23 therapy (n = 19) \t−0.02 (−2) \t– \t \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.01 \n\t vs. NBT \t– \t0.06 (5) \t0.09 \n\tAnti-IL17 therapy (n = 22) \t−0.15 (−12) \t– \t \n\t vs. NBT \t– \t0.06 (5) \t0.005 \n\n\nValues are reported as Mean (% change) for continuous data. Two-tailed P-values less than 0.05 significant (bold values).\n\n\nIL, interleukin; NBT, non-biologic treated.\n\n\n\n\n\nTable 4\nChange in non-calcified coronary plaque burden over one-year between treatment groups\n\n \n\tTreatments \tChange over one-year (mm2) (%) \tP-value \n\tAnti-TNF therapy (n = 48) \t−0.06 (−5) \t– \t \n\t vs. Anti-IL12/23 \t– \t−0.02 (−2) \t0.27 \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.08 \n\t vs. NBT \t– \t0.06 (5) \t0.009 \n\tAnti-IL12/23 therapy (n = 19) \t−0.02 (−2) \t– \t \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.01 \n\t vs. NBT \t– \t0.06 (5) \t0.09 \n\tAnti-IL17 therapy (n = 22) \t−0.15 (−12) \t– \t \n\t vs. NBT \t– \t0.06 (5) \t0.005 \n\n\n\tTreatments \tChange over one-year (mm2) (%) \tP-value \n\tAnti-TNF therapy (n = 48) \t−0.06 (−5) \t– \t \n\t vs. Anti-IL12/23 \t– \t−0.02 (−2) \t0.27 \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.08 \n\t vs. NBT \t– \t0.06 (5) \t0.009 \n\tAnti-IL12/23 therapy (n = 19) \t−0.02 (−2) \t– \t \n\t vs. Anti-IL17 \t– \t−0.15 (−12) \t0.01 \n\t vs. NBT \t– \t0.06 (5) \t0.09 \n\tAnti-IL17 therapy (n = 22) \t−0.15 (−12) \t– \t \n\t vs. NBT \t– \t0.06 (5) \t0.005 \n\n\nValues are reported as Mean (% change) for continuous data. Two-tailed P-values less than 0.05 significant (bold values).\n\n\nIL, interleukin; NBT, non-biologic treated.\n\n\n\n\nFinally, we explored the modulation of inflammatory blood markers (IFN-γ, TNF-α, IL-6, IL1-β) with treatment of skin disease. PASI score was associated with IFN-γ (β = 0.12; P = 0.003), TNF-alpha (β = 0.08; P = 0.05), and IL-6 (β = 0.10; P = 0.02) at baseline. After one-year of biologic therapy, there were significant reductions in interferon-γ [median (IQR), 10.7 (5.6–28.0) vs. 10.2 (5.2–20.3); P = 0.02], TNF-α [median (IQR), 1.7 (1.0–3.5) vs. 1.3 (0.6–2.5); P = 0.04], and interleukin-6 [median (IQR), 1.4 (0.9–3.0) vs. 1.2 (0.7–2.1); P = 0.01]. These findings were not observed in the non-biologic treated group (Supplementary material online, Table S3).\n                            4. Discussion\n\nHerein, this observational study demonstrated favourable modulation in coronary artery plaque disease indices by CCTA in a consecutive sample of severe psoriasis patients treated with commonly used biological classes of drugs: anti-TNF, anti-IL12/23, and anti-IL17, compared with those not treated with biologic therapy. Despite not knowing the specific progression rate of subclinical atherosclerosis on CCTA in psoriasis, we used those with similar disease patterns choosing to receive topical or light therapy only as our reference. In this referent group, we observed progression of coronary artery disease with conversion of fibrous burden to fibro-fatty burden, suggestive of lipid infiltration within the coronary plaque. In those treated with biological therapy, we found that inflammatory driven phenotypes including lipid-rich plaque and the necrotic core decreased following therapy. Taken together, these data provide preliminary evidence that treatment with biologic modulates coronary artery plaque in psoriasis.\nInflammation is causal in atherosclerosis and still accounts for approximately 20–30% of residual risk for cardiovascular events in the population.13 Those with inflammatory diseases such as rheumatoid arthritis, systemic lupus erythematosus, and psoriasis have a disproportional rate of cardiovascular events compared with age and gender matched counterparts. Therefore, these populations serve as a unique vehicle to understand inflammatory atherogenesis. We recently showed that this increase in MI in psoriasis might be due to early, increased coronary artery disease that is equivocal to individuals who are on average 10 years older with diagnosed hyperlipidaemia.11 Whether these burdens modulate with skin disease treatment has been the topic of intense investigation. Furthermore, when a sample of psoriasis patients was followed for one year after any treatment, a 6% decrease in aortic vascular inflammation was observed6; however, the coronary arteries were not analysed in that study.\nCCTA has long been utilized for characterization of coronary plaque burden beyond X-ray angiography and has been extensively compared with and validated against intravascular ultrasound.14 CCTA provides characterization of not only lumen stenosis and arterial remodelling, but also plaque subcomponents, including calcified, non-calcified, and high-risk features.15 Studies have shown that there is an increase in non-calcified plaque volumes in acute coronary syndrome patients,16 obese diabetics,9 and also undergoes modulation in response to statin therapy.17,18 Recently, when CCTA plaque features are accounted for, patients with widespread non-obstructive coronary artery disease had similar event rates when compared with patients with localized obstructive disease,19 suggesting that plaque characteristics are important in defining accurate cardiovascular risk beyond obstructive stenosis.\nThe use of biologic therapy for psoriasis has rapidly increased over the past decade given its remarkable success in early clearance of psoriatic plaque. First, we observed reduction in non-calcified plaque across all three classes of biologic agents in the study with varying degrees, suggesting that clearance of psoriasis itself is important in the context of vascular disease. Anti-TNF therapy is commonly accepted as the first line biologic agent for the management of psoriasis; however, some of the patients on this treatment do not have adequate response.20 In psoriasis, TNF inhibitors have also been linked to worsening of cardiometabolic risk factors, including weight gain and a shift in apolipoprotein B,21 and recently were shown to not reduce vascular inflammation.22 In that study, however, important inflammatory biomarkers, including TNF-α, interleukin-6, hsCRP, and glycoprotein acetylation, all decreased following anti-TNF therapy. Observational studies have shown that biological therapy, more specifically TNF inhibitors, reduces MI,23 suggesting that longer term observed benefit may relate to coronary plaque modulation over time. The cardiovascular effects of newer, cytokine specific biologic agents have yet to be extensively studied in psoriasis. In a meta-analysis studying the association of major adverse cardiovascular events with the use of anti-IL12/23 agents, the potential of these agents to further increase cardiovascular morbidity could not be excluded.24,25 However, previous literature in animal studies has been conflicting regarding whether IL17 is pro- vs. anti-atherogenic.26 While some studies have suggested the pro-atherogenic effects of IL17,27,28 a recent athero-protective pathway has been proposed through regulation of IFN-γ producing Th1 cells.29 In our present study, we observed the greatest percent reduction of non-calcified plaque burden in patients on anti-IL17 therapy with a reduction in necrotic core suggesting a potential role for IL17 in atherosclerotic pathways. It has been implicated in literature that IL17 is a central mediator in lipoprotein entrapment, leading to vascular stiffness and promoting early atherosclerosis.30 Mouse studies have also suggested that IL17 increases monocyte adhesion to the vascular walls, promoting inflammatory cytokine production and endothelial dysfunction,31 with this phenomenon being normalized by IL17A blockade. Moreover, the potential role of IL17 in linking skin disease and vascular disease in psoriasis was expanded on in another mice study whereby clearance of psoriatic skin manifestations by IL17 blockade was shown to diminish peripheral oxidative stress and vascular dysfunction.32 Taken together, these data provide evidence to support further investigation of IL17 blockade on coronary disease in humans.\nOur study does have important limitations. This was an observational study, and therefore, is subjected to potential for confounders compared with a randomized clinical trial. Moreover, the use of biologic agents was open-label, non-randomized, in a small sample and with a short duration of follow-up. However, this is the largest consecutive sample of psoriasis patients followed over time using CCTA. Furthermore, the biologic treated groups had variability in baseline coronary parameters due to a small sample size. Finally, we have not studied hard, cardiovascular events, but instead used coronary artery plaque indices by CCTA to understand modulation on cardiovascular disease risk.\n                            5. Conclusions\n\nIn conclusion, we demonstrate that treatment of psoriasis with biologic therapy is associated with a reduction of non-calcified coronary plaque and improvement in plaque morphology compared with those not treated with biologic therapy. These findings highlight the potential role of quelling residual inflammation in cardiovascular disease and risk reduction. These findings support the conduct of larger randomized trials of biologic therapy on cardiovascular disease in psoriasis and potentially other inflammatory diseases.\n                            Authors’ contributions\n\nIntegrity of the data: Y.A.E. and N.N.M. had full access to all the data in the study and take responsibility for the integrity of the data and the accuracy of the data analysis. Concept and design: Y.A.E. and N.N.M. conceived the study concept and the study design was by N.N.M. Acquisition, analysis, or interpretation of data: J.R., Y.A.E., M.Y.C. and N.N.M. acquired and analysed the data. Drafting of the manuscript: Y.A.E. drafted the manuscript. Critical revision of the manuscript for important intellectual content: All co-authors provided critical revisions of the manuscript. Statistical analysis: Y.A.E. and A.K.D. performed analyses. Administrative, technical, or material support: N.N.M. provided technical guidance to Y.A.E. and A.K.D. during the study. Study supervision: The study was conducted under the supervision of N.N.M.\n                            Acknowledgements\n\nWe would like to acknowledge and thank the NIH Clinical Center outpatient clinic-7 nurses for their invaluable contribution to the process of patient recruitment.\nConflict of interest: N.N.M. is a full-time US Government Employee and receives research grants to the NHLBI from AbbVie, Janssen, Celgene and Novartis. J.M.G. in the past 12 months has served as a consultant for Coherus (DSMB), Dermira, Janssen Biologics, Merck (DSMB), Novartis Corp, Regeneron, Dr. Reddy’s labs, Sanofi and Pfizer Inc., receiving honoraria; and receives research grants (to the Trustees of the University of Pennsylvania) from Abbvie, Janssen, Novartis Corp, Regeneron, Sanofi, Celgene, and Pfizer Inc.; and received payment for continuing medical education work related to psoriasis that was supported indirectly by Lilly and Abbvie. J.M.G. is a co-patent holder of resiquimod for treatment of cutaneous T cell lymphoma. All other authors declared no conflict of interest.\n                            Funding\n\nThis work was supported by the National Heart, Lung and Blood Institute (NHLBI) Intramural Research Program (HL006193-02). This research was also made possible through the NIH Medical Research Scholars Program, a public-private partnership supported jointly by the NIH and generous contributions to the Foundation for the NIH from the Doris Duke Charitable Foundation (DDCF Grant #2014194), the American Association for Dental Research, the Colgate-Palmolive Company, Genentech, Elsevier, and other private donors.\n                            Footnotes\n\nTime for primary review: 18 days\n\n\n                            References\n\n1\nRidker\n PM\n\n, Rifai\n N\n\n, Pfeffer\n MA\n\n, Sacks\n FM\n\n, Moye\n LA\n\n, Goldman\n S\n\n, Flaker\n GC\n\n, Braunwald\n E.\n\n\n Inflammation, pravastatin, and the risk of coronary events after myocardial infarction in patients with average cholesterol levels. Cholesterol and Recurrent Events (CARE) Investigators\n. Circulation\n  1998\n;98\n:839\n–844\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n2\nRidker\n PM.\n\n\n Clinical application of C-reactive protein for cardiovascular disease detection and prevention\n. Circulation\n  2003\n;107\n:363\n–369\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n3\nRidker\n PM\n\n, Everett\n BM\n\n, Thuren\n T\n\n, MacFadyen\n JG\n\n, Chang\n WH\n\n, Ballantyne\n C\n\n, Fonseca\n F\n\n, Nicolau\n J\n\n, Koenig\n W\n\n, Anker\n SD\n\n, Kastelein\n JJP\n\n, Cornel\n JH\n\n, Pais\n P\n\n, Pella\n D\n\n, Genest\n J\n\n, Cifkova\n R\n\n, Lorenzatti\n A\n\n, Forster\n T\n\n, Kobalava\n Z\n\n, Vida-Simiti\n L\n\n, Flather\n M\n\n, Shimokawa\n H\n\n, Ogawa\n H\n\n, Dellborg\n M\n\n, Rossi\n PRF\n\n, Troquay\n RPT\n\n, Libby\n P\n\n, Glynn\n RJ\n\n\n; CANTOS Trial Group\n. Antiinflammatory therapy with canakinumab for atherosclerotic disease\n. N Engl J Med\n  2017\n;377\n:1119\n–1131\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n4\nGelfand\n JM\n\n, Dommasch\n ED\n\n, Shin\n DB\n\n, Azfar\n RS\n\n, Kurd\n SK\n\n, Wang\n X\n\n, Troxel\n AB.\n\n\n The risk of stroke in patients with psoriasis\n. J Invest Dermatol\n  2009\n;129\n:2411\n–2418\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n5\nMansouri\n B\n\n, Kivelevitch\n D\n\n, Natarajan\n B\n\n, Joshi\n AA\n\n, Ryan\n C\n\n, Benjegerdes\n K\n\n, Schussler\n JM\n\n, Rader\n DJ\n\n, Reilly\n MP\n\n, Menter\n A\n\n, Mehta\n NN.\n\n\n Comparison of coronary artery calcium scores between patients with psoriasis and type 2 diabetes\n. JAMA Dermatol\n  2016\n;152\n:1244\n–1253\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n6\nDey\n AK\n\n, Joshi\n AA\n\n, Chaturvedi\n A\n\n, Lerman\n JB\n\n, Aberra\n TM\n\n, Rodante\n JA\n\n, Teague\n HL\n\n, Harrington\n CL\n\n, Rivers\n JP\n\n, Chung\n JH\n\n, Kabbany\n MT\n\n, Natarajan\n B\n\n, Silverman\n JI\n\n, Ng\n Q\n\n, Sanda\n GE\n\n, Sorokin\n AV\n\n, Baumer\n Y\n\n, Gerson\n E\n\n, Prussick\n RB\n\n, Ehrlich\n A\n\n, Green\n LJ\n\n, Lockshin\n BN\n\n, Ahlman\n MA\n\n, Playford\n MP\n\n, Gelfand\n JM\n\n, Mehta\n NN.\n\n\n Association between skin and aortic vascular inflammation in patients with psoriasis: a case-cohort study using positron emission tomography/computed tomography\n. JAMA Cardiol\n  2017\n;2\n:1013\n–1018\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n7\nHarrington\n CL\n\n, Dey\n AK\n\n, Yunus\n R\n\n, Joshi\n AA\n\n, Mehta\n NN.\n\n\n Psoriasis as a human model of disease to study inflammatory atherogenesis\n. Am J Physiol Heart Circ Physiol\n  2017\n;312\n:H867\n–H873\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n8\nCarlin\n CS\n\n, Feldman\n SR\n\n, Krueger\n JG\n\n, Menter\n A\n\n, Krueger\n GG.\n\n\n A 50% reduction in the Psoriasis Area and Severity Index (PASI 50) is a clinically significant endpoint in the assessment of psoriasis\n. J Am Acad Dermatol\n  2004\n;50\n:859\n–866\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n9\nvon Elm\n E\n\n, Altman\n DG\n\n, Egger\n M\n\n, Pocock\n SJ\n\n, Gøtzsche\n PC\n\n, Vandenbroucke\n JP.\n\n\n The strengthening the reporting of observational studies in epidemiology (strobe) statement: guidelines for reporting observational studies\n. Ann Intern Med\n  2007\n;147\n:573\n–577\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n10\nKwan\n AC\n\n, May\n HT\n\n, Cater\n G\n\n, Sibley\n CT\n\n, Rosen\n BD\n\n, Lima\n JAC\n\n, Rodriguez\n K\n\n, Lappe\n DL\n\n, Muhlestein\n JB\n\n, Anderson\n JL\n\n, Bluemke\n DA.\n\n\n Coronary artery plaque volume and obesity in patients with diabetes: the factor-64 study\n. Radiology\n  2014\n;272\n:690\n–699\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n11\nLerman\n JB\n\n, Joshi\n AA\n\n, Chaturvedi\n A\n\n, Aberra\n TM\n\n, Dey\n AK\n\n, Rodante\n JA\n\n, Salahuddin\n T\n\n, Chung\n JH\n\n, Rana\n A\n\n, Teague\n HL\n\n, Wu\n JJ\n\n, Playford\n MP\n\n, Lockshin\n BA\n\n, Chen\n MY\n\n, Sandfort\n V\n\n, Bluemke\n DA\n\n, Mehta\n NN.\n\n\n Coronary plaque characterization in psoriasis reveals high-risk features that improve after treatment in a prospective observational study\n. Circulation\n  2017\n;136\n:263\n–276\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n12\nSalahuddin\n T\n\n, Natarajan\n B\n\n, Playford\n MP\n\n, Joshi\n AA\n\n, Teague\n H\n\n, Masmoudi\n Y\n\n, Selwaness\n M\n\n, Chen\n MY\n\n, Bluemke\n DA\n\n, Mehta\n NN.\n\n\n Cholesterol efflux capacity in humans with psoriasis is inversely related to non-calcified burden of coronary atherosclerosis\n. Eur Heart J\n  2015\n;36\n:2662\n–2665\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n13\nHarrington\n RA.\n\n\n Targeting inflammation in coronary artery disease\n. N Engl J Med\n  2017\n;377\n:1197\n–1198\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n14\nFischer\n C\n\n, Hulten\n E\n\n, Belur\n P\n\n, Smith\n R\n\n, Voros\n S\n\n, Villines\n TC.\n\n\n Coronary CT angiography versus intravascular ultrasound for estimation of coronary stenosis and atherosclerotic plaque burden: a meta-analysis\n. J Cardiovasc Comput Tomogr\n  2013\n;7\n:256\n–266\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n15\nMotoyama\n S\n\n, Ito\n H\n\n, Sarai\n M\n\n, Kondo\n T\n\n, Kawai\n H\n\n, Nagahara\n Y\n\n, Harigaya\n H\n\n, Kan\n S\n\n, Anno\n H\n\n, Takahashi\n H\n\n, Naruse\n H\n\n, Ishii\n J\n\n, Hecht\n H\n\n, Shaw\n LJ\n\n, Ozaki\n Y\n\n, Narula\n J.\n\n\n Plaque characterization by coronary computed tomography angiography and the likelihood of acute coronary events in mid-term follow-up\n. J Am Coll Cardiol\n  2015\n;66\n:337\n–346\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n16\nDey\n D\n\n, Achenbach\n S\n\n, Schuhbaeck\n A\n\n, Pflederer\n T\n\n, Nakazato\n R\n\n, Slomka\n PJ\n\n, Berman\n DS\n\n, Marwan\n M.\n\n\n Comparison of quantitative atherosclerotic plaque burden from coronary CT angiography in patients with first acute coronary syndrome and stable coronary artery disease\n. J Cardiovasc Comput Tomogr\n  2014\n;8\n:368\n–374\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n17\nSandfort\n V\n\n, Lima\n JA\n\n, Bluemke\n DA.\n\n\n Noninvasive imaging of atherosclerotic plaque progression: status of coronary computed tomography angiography\n. Circ Cardiovasc Imaging\n  2015\n;8\n:e003316\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n18\nLo\n J\n\n, Lu\n MT\n\n, Ihenachor\n EJ\n\n, Wei\n J\n\n, Looby\n SE\n\n, Fitch\n KV\n\n, Oh\n J\n\n, Zimmerman\n CO\n\n, Hwang\n J\n\n, Abbara\n S\n\n, Plutzky\n J\n\n, Robbins\n G\n\n, Tawakol\n A\n\n, Hoffmann\n U\n\n, Grinspoon\n SK.\n\n\n Effects of statin therapy on coronary artery plaque volume and high-risk plaque morphology in HIV-infected patients with subclinical atherosclerosis: a randomised, double-blind, placebo-controlled trial\n. Lancet HIV\n  2015\n;2\n:e52\n–e63\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n19\nBittencourt\n MS\n\n, Hulten\n E\n\n, Ghoshhajra\n B\n\n, O’Leary\n D\n\n, Christman\n MP\n\n, Montana\n P\n\n, Truong\n QA\n\n, Steigner\n M\n\n, Murthy\n VL\n\n, Rybicki\n FJ\n\n, Nasir\n K\n\n, Gowdak\n LHW\n\n, Hainer\n J\n\n, Brady\n TJ\n\n, Di Carli\n MF\n\n, Hoffmann\n U\n\n, Abbara\n S\n\n, Blankstein\n R.\n\n\n Prognostic value of nonobstructive and obstructive coronary artery disease detected by coronary computed tomography angiography to identify cardiovascular events\n. Circ Cardiovasc Imaging\n  2014\n;7\n:282\n–291\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n20\nBoehncke\n WH\n\n, Menter\n A.\n\n\n Burden of disease: psoriasis and psoriatic arthritis\n. Am J Clin Dermatol\n  2013\n;14\n:377\n–388\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n21\nSattar\n N\n\n, Crompton\n P\n\n, Cherry\n L\n\n, Kane\n D\n\n, Lowe\n G\n\n, McInnes\n IB.\n\n\n Effects of tumor necrosis factor blockade on cardiovascular risk factors in psoriatic arthritis: a double-blind, placebo-controlled study\n. Arthritis Rheum\n  2007\n;56\n:831\n–839\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n22\nMehta\n NN\n\n, Shin\n DB\n\n, Joshi\n AA\n\n, Dey\n AK\n\n, Armstrong\n AW\n\n, Duffin\n KC\n\n, Fuxench\n ZC\n\n, Harrington\n CL\n\n, Hubbard\n RA\n\n, Kalb\n RE\n\n, Menter\n A\n\n, Rader\n DJ\n\n, Reilly\n MP\n\n, Simpson\n EL\n\n, Takeshita\n J\n\n, Torigian\n DA\n\n, Werner\n TJ\n\n, Troxel\n AB\n\n, Tyring\n SK\n\n, Vanderbeek\n SB\n\n, Van Voorhees\n AS\n\n, Playford\n MP\n\n, Ahlman\n MA\n\n, Alavi\n A\n\n, Jm\n G.\n\n\n Effect of 2 psoriasis treatments on vascular inflammation and novel inflammatory cardiovascular biomarkers: a randomized placebo-controlled trial\n. Circ Cardiovasc Imaging\n  2018\n;11\n:e007394.\nGoogle Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n23\nWu\n JJ\n\n, Poon\n KY\n\n, Channual\n JC\n\n, Shen\n AY.\n\n\n Association between tumor necrosis factor inhibitor therapy and myocardial infarction risk in patients with psoriasis\n. Arch Dermatol\n  2012\n;148\n:1244\n–1250\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n24\nTzellos\n T\n\n, Kyrgidis\n A\n\n, Trigoni\n A\n\n, Zouboulis\n CC.\n\n\n Association of ustekinumab and briakinumab with major adverse cardiovascular events: an appraisal of meta-analyses and industry sponsored pooled analyses to date\n. Dermatoendocrinol\n  2012\n;4\n:320\n–323\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n25\nReich\n K\n\n, Langley\n RG\n\n, Lebwohl\n M\n\n, Szapary\n P\n\n, Guzzo\n C\n\n, Yeilding\n N\n\n, Li\n S\n\n, Hsu\n MC\n\n, Griffiths\n CE.\n\n\n Cardiovascular safety of ustekinumab in patients with moderate to severe psoriasis: results of integrated analyses of data from phase II and III clinical studies\n. Br J Dermatol\n  2011\n;164\n:862\n–872\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n26\nButcher\n MJ\n\n, Gjurich\n BN\n\n, Phillips\n T\n\n, Galkina\n EV\n\n\n. The IL-17A/IL-17RA axis plays a proatherogenic role via the regulation of aortic myeloid cell recruitment\n. Circ Res\n  2012\n;110\n:675\n–687\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n27\nErbel\n C\n\n, Chen\n L\n\n, Bea\n F\n\n, Wangler\n S\n\n, Celik\n S\n\n, Lasitschka\n F\n\n, Wang\n Y\n\n, Bockler\n D\n\n, Katus\n HA\n\n, Dengler\n TJ.\n\n\n Inhibition of IL-17A attenuates atherosclerotic lesion development in apoE-deficient mice\n. J Immunol\n  2009\n;183\n:8167\n–8175\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n28\nMadhur\n MS\n\n, Funt\n SA\n\n, Li\n L\n\n, Vinh\n A\n\n, Chen\n W\n\n, Lob\n HE\n\n, Iwakura\n Y\n\n, Blinder\n Y\n\n, Rahman\n A\n\n, Quyyumi\n AA\n\n, Harrison\n DG.\n\n\n Role of interleukin 17 in inflammation, atherosclerosis, and vascular function in apolipoprotein e-deficient mice\n. Arterioscler Thromb Vasc Biol\n  2011\n;31\n:1565\n–1572\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n29\nDanzaki\n K\n\n, Matsui\n Y\n\n, Ikesue\n M\n\n, Ohta\n D\n\n, Ito\n K\n\n, Kanayama\n M\n\n, Kurotaki\n D\n\n, Morimoto\n J\n\n, Iwakura\n Y\n\n, Yagita\n H\n\n, Tsutsui\n H\n\n, Uede\n T.\n\n\n Interleukin-17A deficiency accelerates unstable atherosclerotic plaque formation in apolipoprotein E-deficient mice\n. Arterioscler Thromb Vasc Biol\n  2012\n;32\n:273\n–280\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n30\nHuang\n LH\n\n, Zinselmeyer\n BH\n\n, Chang\n CH\n\n, Saunders\n BT\n\n, Elvington\n A\n\n, Baba\n O\n\n, Broekelmann\n TJ\n\n, Qi\n L\n\n, Rueve\n JS\n\n, Swartz\n MA\n\n, Kim\n BS\n\n, Mecham\n RP\n\n, Wiig\n H\n\n, Thomas\n MJ\n\n, Sorci-Thomas\n MG\n\n, Randolph\n GJ.\n\n\n Interleukin-17 drives interstitial entrapment of tissue lipoproteins in experimental psoriasis\n. Cell Metabol\n  2018\n;doi:10.1016/j.cmet.2018.10.006.\n\n\n\n31\nNordlohne\n J\n\n, Helmke\n A\n\n, Ge\n S\n\n, Rong\n S\n\n, Chen\n R\n\n, Waisman\n A\n\n, Haller\n H\n\n, von Vietinghoff\n S.\n\n\n Aggravated atherosclerosis and vascular inflammation with reduced kidney function depend on interleukin-17 receptor A and are normalized by inhibition of interleukin-17A\n. JACC Basic Transl Sci\n  2018\n;3\n:54\n–66\n.Google Scholar\nCrossref\nSearch ADS\n \nPubMed\n \n\n\n\n\n32\nSchuler\n R\n\n, Brand\n A\n\n, Klebow\n S\n\n, Wild\n J\n\n, Protasio Veras\n F\n\n, Ullmann\n E\n\n, Roohani\n S\n\n, Kolbinger\n F\n\n, Kossmann\n S\n\n, Wohn\n C\n\n, Daiber\n A\n\n, Munzel\n T\n\n, Wenzel\n P\n\n, Waisman\n A\n\n, Clausen\n BE\n\n, Karbach\n S.\n\n\n Antagonization of IL-17A attenuates skin inflammation and vascular dysfunction in mouse models of psoriasis\n. J Invest Dermatol\n  2018\n;doi:10.1016/j.jid.2018.09.021.\n\n\n\n\n        \n\n\n\n        \n\n\n        \nPublished by Oxford University Press on behalf of the European Society of Cardiology 2019.\nThis work is written by US Government employees and is in the public domain in the US.\n\n\n\n        \n\n    \n\n\n\n    \n\n    \n            \n        Topic:\n\n        \t\n                    coronary arteriosclerosis\n                \n\t\n                    cardiovascular disease risk factors\n                \n\t\n                    biological therapy\n                \n\t\n                    follow-up\n                \n\t\n                    necrosis\n                \n\t\n                    psoriasis\n                \n\t\n                    skin disorders\n                \n\t\n                    coronary plaque\n                \n\t\n                    ct angiography of coronary arteries\n                \n\n\n    \n\n\n    \n\n    \n        \n        \n            Issue Section:\n\n                RAPID COMMUNICATION\n        \n\n\n\n    \n\n    \n        \n\n    \n\n\n\n                        \n\n                        \n                            Download all figures\n                        \n\n                        \n\n                            \n            \n        \t\n            \n                Supplementary data\n            \n\n        \n\nSupplementary data\n\n        Supplementary Data\n - docx file\n\n\n    \n\n    \n        \n    \n\n\n                         \n                                \n        \n\n\n    \n\n    \n        \n    \n\n\n                        \n\n                    \n\n                   \n                \n \n\n                     \n\n\n            \n\n        \n \n\n        \n                \n        \n\n\n    \n\n\n\n    \n\n \n\n    \n\n \n\n    \n\n    \n        \n\n\n\n\n\n    \n        \n            \n                2\n                Views\n            \n\n\n            \n                \n0                \n                Citations\n            \n\n    \n            \n    \n            \n    \n\n         \n\n    \n\n\n            \n\n        \n\n\n            \n                View Metrics\n            \n\n    \n\n        \n            \n                ×\n            \n\n        \n\n\n\n    \n\n    \n        \n    \n        Email alerts\n\n                \n                    New issue alert\n                \n\n                \n                    Advance article alerts\n                \n\n                \n                    Article activity alert\n                \n\n                    \n                Receive exclusive offers and updates from Oxford Academic\n            \n\n        \n            \n\n            Close\n            \n                \n            \n        \n\n    \n\n\n    \n\n    \n        \n\n\n    \n\n    \n        \n    \n\n    \n            Related articles in\n\n    \n        \t\n                    Google Scholar\n                \n\n\n    \n\n\n    \n\n    \n        Related articles in PubMed\n\n\n        \n            \n                    Rapid spread of mannan to the immune system, skin and joints within six hours after local exposure.\n\n                \n            \n\n        \n\n        \n            \n                    How should we treat heavily calcified coronary artery disease in contemporary practice? From atherectomy to intravascular lithotripsy.\n\n                \n            \n\n        \n\n        \n            \n                    Appearance of lentigines in psoriasis patient treated with guselkumab.\n\n                \n            \n\n        \n\n        \n            \n                    Connexin 26 and 43 play a role in regulating proinflammatory events in the epidermis.\n\n                \n            \n\n        \n\n\n\n\n    \n\n    \n        Citing articles via\n\n\n            \n            Google Scholar\n        \n\n            \n            CrossRef\n        \n\n\n\n    \n\n    \n            \t\n                Latest\n            \n\t\n                Most Read\n            \n\t\n                Most Cited\n            \n\n\n        \n\n\n\n\n\n\n    \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n        \n            \n\n                       \n                        \n\n\n\n                        \n                           \n                                                              \n                                   T Cell Checkpoint Regulators in the Heart\n                               \n\n                                                                                             \n                                                                                  \n                                            \n                                       \n \n                               \n\n\n\n                           \n\n                    \n\n                       \n                        \n\n\n\n                        \n                           \n                                                              \n                                   Epidermal growth factor-like repeats of SCUBE1 derived from platelets are critical for thrombus formation\n                               \n\n                                                                                             \n                                                                                  \n                                            \n                                       \n \n                               \n\n\n\n                           \n\n                    \n\n                       \n                        \n\n\n\n                        \n                           \n                                                              \n                                   Coronary artery plaque characteristics and treatment with biologic therapy in severe psoriasis: results from a prospective observational study\n                               \n\n                                                                                             \n                                                                                  \n                                            \n                                       \n \n                               \n\n\n\n                           \n\n                    \n\n                       \n                        \n\n\n\n                        \n                           \n                                                              \n                                   Common risk factors for heart failure and cancer\n                               \n\n                                                                                             \n                                                                                  \n                                            \n                                       \n \n                               \n\n\n\n                           \n\n                    \n\n                       \n                        \n\n\n\n                        \n                           \n                                                              \n                                   Cardiac Sodium-Glucose Co-Transporter 1 (SGLT1) is a Novel Mediator of Ischemia/Reperfusion Injury\n                               \n\n                                                                                             \n                                                                                  \n                                            \n                                       \n \n                               \n\n\n\n                           \n\n                    \n\n            \n\n        \n\n\n\n\n        \n        \n        \n        \n        \n\n    \n\n\n    \n\n\n\n\n    \n\n\n\n    \n        \n\n\n    \n\n\n\n    \n\n\n        \n \n    \n\n    \n\n                \n\n            \n        \n    \n\n    \n\n        \n    \n    \n\n        \n        \n    \n        \n\n\n    \n\n\n\n    \n\n\n\n\n\n    \n        \n\n                \n\n                    \t\n                                About Cardiovascular Research\n                            \n\t\n                                Editorial Board\n                            \n\t\n                                Author Guidelines\n                            \n\t\n                                Facebook\n                            \n\t\n                                Twitter\n                            \n\n\t\n                                YouTube\n                            \n\t\n                                LinkedIn\n                            \n\t\n                                Purchase\n                            \n\t\n                                Recommend to your Library\n                            \n\t\n                                Advertising and Corporate Services\n                            \n\n\t\n                                Journals Career Network\n                            \n\n\n\n\n                \n\n\n            \n                \n            \n                \n            \n            \n\n\n            \n                \tOnline ISSN 1755-3245\n\tPrint ISSN 0008-6363\n\tCopyright © 2019 European Society of Cardiology\n\n\n            \n\n\n\n        \n\n    \n\n\n    \n\n\n    \n        \n                \n        \n\n\n\t\n    About Us\n    \n\t\n    Contact Us\n    \n\t\n    Careers\n    \n\t\n    Help\n    \n\t\n    Access & Purchase\n\t\n    Rights & Permissions\n    \n\t\n    Open Access\n    \n\n\n\n\n\nConnect\n\n\t\n    Join Our Mailing List\n    \n\t\n    OUPblog\n    \n\t\n    Twitter\n    \n\t\n    Facebook\n    \n\t\n    YouTube\n    \n\t\n    Tumblr\n    \n\n\n\n\n\nResources\n\n\tAuthors\n\tLibrarians\n\tSocieties\n\tSponsors & Advertisers\n\tPress & Media\n\tAgents\n\n\n\n\n\nExplore\n\n\tShop OUP Academic\n\tOxford Dictionaries\n\tOxford Index\n\tEpigeum\n\tOUP Worldwide\n\tUniversity of Oxford\n\n\n\n\n\nOxford University Press is a department of the University of Oxford. It furthers the University's objective of excellence in research, scholarship, and education by publishing worldwide\n\n\n\n\n\n\n\n\n\tCopyright © 2019 Oxford University Press\n\tCookie Policy\n\tPrivacy Policy\n\tLegal Notice\n\tSite Map\n\tAccessibility\n\tGet Adobe Reader\n\n\n\n\n\n\n\n    \n    \n    \n    \n\n\n        \n\n    \n\n    \n        \n    \n\n\n\n        \n        \n            \n\n            Close\n        \n\n        \n            \n                This Feature Is Available To Subscribers Only\n\n                Sign In or Create an Account\n\n            \n\n            Close\n        \n\n        \n\n        \n            This PDF is available to Subscribers Only\n\n            View Article Abstract & Purchase Options\n            \n                For full access to this pdf, sign in to an existing account, or purchase an annual subscription.\n\n            \n\n            Close\n        \n\n        \n        \n \n    \n\n\n\n\n\n\n\n\n    \n    \n    \n     \n \n\n    \n    \n    \n    \n       \n    \n\n    \n"))
#normalized_tags, document_tags = dictionary_matcher(test_text)


#tagged_document_text = highlight_keyword(test_text, 'psoriasis')
#tagged_document_text = highlight_tags(tagged_document_text, document_tags)       
                                                                                                                      
#solr_results['title'][-1] == solr_results['title'][-2]
        
        
#test_text = "\n\n\n\n\n\n\n\n30770430.xml\n\n\n\n\n\n\n\n\n\n\n30770430\n\n2019\n04\n16\n\n\n\n1526-632X\n\n92\n10\n\n2019\nMar\n05\n\n\nNeurology\n\nThe prevalence of MS in the United States: A population-based estimate using health claims data.\n\ne1029-e1040\n\n10.1212/WNL.0000000000007035\n\nTo generate a national multiple sclerosis (MS) prevalence estimate for the United States by applying a validated algorithm to multiple administrative health claims (AHC) datasets.\nA validated algorithm was applied to private, military, and public AHC datasets to identify adult cases of MS between 2008 and 2010. In each dataset, we determined the 3-year cumulative prevalence overall and stratified by age, sex, and census region. We applied insurance-specific and stratum-specific estimates to the 2010 US Census data and pooled the findings to calculate the 2010 prevalence of MS in the United States cumulated over 3 years. We also estimated the 2010 prevalence cumulated over 10 years using 2 models and extrapolated our estimate to 2017.\nThe estimated 2010 prevalence of MS in the US adult population cumulated over 10 years was 309.2 per 100,000 (95% confidence interval [CI] 308.1-310.1), representing 727,344 cases. During the same time period, the MS prevalence was 450.1 per 100,000 (95% CI 448.1-451.6) for women and 159.7 (95% CI 158.7-160.6) for men (female:male ratio 2.8). The estimated 2010 prevalence of MS was highest in the 55- to 64-year age group. A US north-south decreasing prevalence gradient was identified. The estimated MS prevalence is also presented for 2017.\nThe estimated US national MS prevalence for 2010 is the highest reported to date and provides evidence that the north-south gradient persists. Our rigorous algorithm-based approach to estimating prevalence is efficient and has the potential to be used for other chronic neurologic conditions.\nCopyright © 2019 The Author(s). Published by Wolters Kluwer Health, Inc. on behalf of the American Academy of Neurology.\n\n\n\nWallin\nMitchell T\nMT\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY. mitchell.wallin@va.gov.\n\n\n\nCulpepper\nWilliam J\nWJ\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nCampbell\nJonathan D\nJD\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nNelson\nLorene M\nLM\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nLanger-Gould\nAnnette\nA\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nMarrie\nRuth Ann\nRA\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nCutter\nGary R\nGR\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nKaye\nWendy E\nWE\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nWagner\nLaurie\nL\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nTremlett\nHelen\nH\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nBuka\nStephen L\nSL\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nDilokthornsakul\nPiyameth\nP\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nTopol\nBarbara\nB\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nChen\nLie H\nLH\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nLaRocca\nNicholas G\nNG\n\nFrom the Department of Veterans Affairs Multiple Sclerosis Center of Excellence (M.T.W., W.J.C.); Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Maryland (W.J.C.), Baltimore; University of Colorado (J.D.C., P.D.), Aurora; Stanford University School of Medicine (L.M.N., B.T.), CA; Southern California Permanente Medical Group (A.L.-G., L.H.C.), Pasadena; Departments of Internal Medicine and Community Health Sciences (R.A.M.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; University of Alabama at Birmingham (G.R.C.); McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver, Canada; Brown University (S.L.B.), Providence, RI; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nUS Multiple Sclerosis Prevalence Workgroup\n\n\neng\n\nJournal Article\n\n\n2019\n02\n15\n\n\n\nUnited States\nNeurology\n0401060\n0028-3878\n\n\n\n\n\n2018\n02\n24\n\n\n2018\n08\n17\n\n\n2019\n2\n17\n6\n0\n\n\n2019\n2\n17\n6\n0\n\n\n2019\n2\n17\n6\n0\n\n\nppublish\n\n30770430\nWNL.0000000000007035\n10.1212/WNL.0000000000007035\nPMC6442006\n\n\n\n"
#test_text = "\n\n\n\n\n\n\n\n30770432.xml\n\n\n\n\n\n\n\n\n\n\n30770432\n\n2019\n04\n16\n\n\n\n1526-632X\n\n92\n10\n\n2019\nMar\n05\n\n\nNeurology\n\nValidation of an algorithm for identifying MS cases in administrative health claims datasets.\n\ne1016-e1028\n\n10.1212/WNL.0000000000007043\n\nTo develop a valid algorithm for identifying multiple sclerosis (MS) cases in administrative health claims (AHC) datasets.\nWe used 4 AHC datasets from the Veterans Administration (VA), Kaiser Permanente Southern California (KPSC), Manitoba (Canada), and Saskatchewan (Canada). In the VA, KPSC, and Manitoba, we tested the performance of candidate algorithms based on inpatient, outpatient, and disease-modifying therapy (DMT) claims compared to medical records review using sensitivity, specificity, positive and negative predictive values, and interrater reliability (Youden J statistic) both overall and stratified by sex and age. In Saskatchewan, we tested the algorithms in a cohort randomly selected from the general population.\nThe preferred algorithm required ≥3 MS-related claims from any combination of inpatient, outpatient, or DMT claims within a 1-year time period; a 2-year time period provided little gain in performance. Algorithms including DMT claims performed better than those that did not. Sensitivity (86.6%-96.0%), specificity (66.7%-99.0%), positive predictive value (95.4%-99.0%), and interrater reliability (Youden J = 0.60-0.92) were generally stable across datasets and across strata. Some variation in performance in the stratified analyses was observed but largely reflected changes in the composition of the strata. In Saskatchewan, the preferred algorithm had a sensitivity of 96%, specificity of 99%, positive predictive value of 99%, and negative predictive value of 96%.\nThe performance of each algorithm was remarkably consistent across datasets. The preferred algorithm required ≥3 MS-related claims from any combination of inpatient, outpatient, or DMT use within 1 year. We recommend this algorithm as the standard AHC case definition for MS.\nCopyright © 2019 The Author(s). Published by Wolters Kluwer Health, Inc. on behalf of the American Academy of Neurology.\n\n\n\nCulpepper\nWilliam J\nWJ\nhttp://orcid.org/0000-0002-8520-7400\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY. William.Culpepper@va.gov.\n\n\n\nMarrie\nRuth Ann\nRA\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nLanger-Gould\nAnnette\nA\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nWallin\nMitchell T\nMT\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nCampbell\nJonathan D\nJD\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nNelson\nLorene M\nLM\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nKaye\nWendy E\nWE\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nWagner\nLaurie\nL\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nTremlett\nHelen\nH\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nChen\nLie H\nLH\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nLeung\nStella\nS\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nEvans\nCharity\nC\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nYao\nShenzhen\nS\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nLaRocca\nNicholas G\nNG\n\nFrom the Department of Veterans Affairs Post Deployment Health Services (W.J.C., M.T.W.), Multiple Sclerosis Center of Excellence; University of Maryland (W.J.C.), Baltimore; Departments of Internal Medicine and Community Health Sciences (R.A.M., S.L.), Max Rady College of Medicine, Rady Faculty of Health Sciences, University of Manitoba, Winnipeg, Canada; Neurology Department (A.L.-G., L.H.C.), Kaiser Permanente Southern California, Los Angeles; Georgetown University School of Medicine (M.T.W.), Washington, DC; University of Colorado (J.C.), Denver; Stanford University School of Medicine (L.M.N.), CA; McKing Consulting Corp (W.E.K., L.W.), Atlanta, GA; Faculty of Medicine (Neurology) and Centre for Brain Health (H.T.), University of British Columbia, Vancouver; College of Pharmacy and Nutrition (C.E.), University of Saskatchewan; Health Quality Council (Saskatchewan) (S.Y.), Saskatoon, Canada; and National Multiple Sclerosis Society (N.G.L.), New York, NY.\n\n\n\nUnited States Multiple Sclerosis Prevalence Workgroup (MSPWG)\n\n\neng\n\nJournal Article\n\n\n2019\n02\n15\n\n\n\nUnited States\nNeurology\n0401060\n0028-3878\n\n\n\n\n\n2018\n07\n20\n\n\n2018\n11\n24\n\n\n2019\n2\n17\n6\n0\n\n\n2019\n2\n17\n6\n0\n\n\n2019\n2\n17\n6\n0\n\n\nppublish\n\n30770432\nWNL.0000000000007043\n10.1212/WNL.0000000000007043\nPMC6442008\n\n\n\n"
#test_text = "\n\n\n\n\n\n\n\n30978652.xml\n\n\n\n\n\n\n\n\n\n\n30978652\n\n2019\n04\n16\n\n\n\n2211-0356\n\n31\n\n2019\nApr\n04\n\n\nMult Scler Relat Disord\n\nThe association between dietary sugar intake and neuromyelitis optica spectrum disorder: A case-control study.\n\n112-117\n\nS2211-0348(19)30155-5\n10.1016/j.msard.2019.03.028\n\nNeuromyelitis optica spectrum disorder (NMOSD) is an uncommon autoimmune disease of the central nerves system (CNS) by inflammatory nature. The effects of high dietary sugar intake on inflammation and dysbiosis have been received more attention in recent years. The aim of the present study was to investigate the association between various types of dietary sugar intake and NMOSD odds and clinical features.\nThe current case-control study was conducted among 70 patients with definite NMOSD diagnosis based on 2015 international consensus criteria and 164 hospital-based controls. Demographic and anthropometric information in all participants and disease characteristics just in case group were obtained. Dietary data during the past year of study attendance was collected by a validated 168-item food frequency questionnaire. Participants were stratified into 3 tertiles according to each type of sugar intake and the third tertile considered as reference in multivariate regression models. The correlation between dietary sugar and disease features were analyzed using Pearson correlation test.\nThe mean ± SD of total sugar intake increased from 80.73 ± 17.71 to 208.71 ± 57.93 g/day across tertiles of total sugar intake. In fully adjusted model, lower intake of sugar was associates with decreased odds of NMOSD in the first tertile vs third tertile by ORs of: 0.02(CI:0.00-0.08; p-for-trend:0.00), 0.02(CI:0.00-0.10; p-for-trend:0.00), 0.23(CI:0.08-0.61; p-for-trend:0.00), 0.19(CI:0.06-0.58; p-for-trend:0.00) and 0.16(CI:0.05-0.51; p-for-trend:0.00) for glucose, fructose, galactose, lactose and sucrose, respectively. The odds of NMOSD had a 1.72-fold (CI: 1.43-2.03; p-for-trend:0.00) significant raise per every 10 g increase for total sugar intake. There was no significant correlation between various types of dietary sugar intakes and relapse rate or patients' disability.\nThe present study proposes a possible direct association between high intake of various sugar types and odds of suffering from NMOSD. More investigations are needed to prove this results.\nCopyright © 2019. Published by Elsevier B.V.\n\n\n\nRezaeimanesh\nNasim\nN\n\nMultiple Sclerosis Research Center, Neuroscience Institute, Tehran University of Medical Sciences, Tehran, Iran; Department of Clinical Nutrition and Dietetics, Faculty of Nutrition and Food Technology, National Nutrition and Food Technology Research Institute, Shahid Beheshti University of Medical Sciences, Tehran, Iran.\n\n\n\nRazeghi Jahromi\nSoodeh\nS\n\nMultiple Sclerosis Research Center, Neuroscience Institute, Tehran University of Medical Sciences, Tehran, Iran; Department of Clinical Nutrition and Dietetics, Faculty of Nutrition and Food Technology, National Nutrition and Food Technology Research Institute, Shahid Beheshti University of Medical Sciences, Tehran, Iran.\n\n\n\nGhorbani\nZeinab\nZ\n\nMultiple Sclerosis Research Center, Neuroscience Institute, Tehran University of Medical Sciences, Tehran, Iran; School of Nutritional Sciences and Dietetics, Tehran University of Medical Sciences (TUMS), Tehran, Iran.\n\n\n\nBeladi Moghadam\nNahid\nN\n\nDepartment of Neurology, Shahid Beheshti University of Medical Sciences, Tehran, Iran.\n\n\n\nHekmatdoost\nAzita\nA\n\nDepartment of Clinical Nutrition and Dietetics, Faculty of Nutrition and Food Technology, National Nutrition and Food Technology Research Institute, Shahid Beheshti University of Medical Sciences, Tehran, Iran.\n\n\n\nNaser Moghadasi\nAbdorreza\nA\n\nMultiple Sclerosis Research Center, Neuroscience Institute, Tehran University of Medical Sciences, Tehran, Iran.\n\n\n\nAzimi\nAmir Reza\nAR\n\nMultiple Sclerosis Research Center, Neuroscience Institute, Tehran University of Medical Sciences, Tehran, Iran.\n\n\n\nSahraian\nMohammad Ali\nMA\n\nMultiple Sclerosis Research Center, Neuroscience Institute, Tehran University of Medical Sciences, Tehran, Iran. Electronic address: Sahraian1350@yahoo.com.\n\n\n\neng\n\nJournal Article\n\n\n2019\n04\n04\n\n\n\nNetherlands\nMult Scler Relat Disord\n101580247\n2211-0348\n\n\nCase–control\nDiet\nNeuromyelitis optica spectrum disorder\nSugar\n\n\n\n\n\n2018\n12\n05\n\n\n2019\n02\n04\n\n\n2019\n03\n31\n\n\n2019\n4\n13\n6\n0\n\n\n2019\n4\n13\n6\n0\n\n\n2019\n4\n13\n6\n0\n\n\naheadofprint\n\n30978652\nS2211-0348(19)30155-5\n10.1016/j.msard.2019.03.028\n\n\n\n"


#test_text_ls = test_text.split('\n')
#test_text_ls = list(set(test_text.split('\n')))


#test_journal = test_text_ls[37]
#test_title = test_text_ls[39]