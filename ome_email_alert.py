
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 14:51:43 2019

@author: julia.gray
"""
import mysql.connector as MySQLdb
import datetime
import email
import imaplib
import smtplib
import email.mime.multipart
import config_email
import base64
import re
from nltk import tokenize
import logging
import pandas as pd
import numpy as np

import get_documents
from google.modules.utils import get_html
import time

###############################################################################
"""Be sure to add log file path or remove log + try statements prior to running"""
logging.basicConfig(filename = 'email_send_error_log.log')
###############################################################################

def start_db():
    try:
        db = MySQLdb.connect(host="10.115.1.196",    
                        user="julia",         
                         passwd="Roivant1",  
                         db="ome_star_schema")
    except Exception as e:
        error_string = '%s | error in start_db %s' %(e, str(datetime.datetime.now()))
        logging.error(error_string)
    return db

def start_headlines_db():
    headlines_db = MySQLdb.connect(host = '10.115.1.25',
                                   user = 'yoann',
                                   passwd = 'Roivant1',
                                   db = 'nlp_oss')
    return headlines_db
#CS sentence splitting for future use on sentence cap
def split_into_sentences(text):
    alphabets= "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
   
    return sentences

def table_string_results_internal(results, username, sumitovant_list, link_exclusion):
    table_string = ''
    summary_table_string = ''
    #try:
    """Format dictionary of results as html string"""
    summary_table_head = '<table style="border:2px solid #000000;border-collapse:collapse;"><thead><th style="border-bottom:2px solid #000000;max-width:500px">' + 'Relevant? - IM' + '</th></thead>'
    summary_table_head += '<thead><th style="border-bottom:2px solid #000000;max-width:400px">' + 'LDA Class - YMR' + '</th></thead>'
    summary_table_head += '<thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title </th></thead>'
    summary_table_head += '<thead><th style="border-bottom:2px solid #000000;max-width:150px">Correct?</th><th style="border-bottom:2px solid #000000;max-width:400px">Wrong? </th></thead>'
    summary_table_body ='<tbody>'
    
    
    table_head = '<table style="border:2px solid #000000"><thead><th style="border-bottom:2px solid #000000;max-width:400px">' + 'Relevant? - IM' + '</th></thead>'
    table_head += '<thead><th style="border-bottom:2px solid #000000;max-width:400px">' + 'LDA Class - YMR' + '</th></thead>'
    table_head += '<thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title | Tagged Sentence</th></thead>'
    table_head += '<thead><th style="border-bottom:2px solid #000000;max-width:150px">Correct?</th><th style="border-bottom:2px solid #000000;max-width:400px">Wrong? </th></thead>'
    table_body ='<tbody>'
    
    color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                             'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
    
    border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                             'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
    
    
    table_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'GBD_email': [], 'Cortellis': [], 'IPD':[], 'fda_guidance':[], 'FDA_Medical_reviews':[], 'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
    table_summary_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'GBD_email': [], 'Cortellis': [], 'IPD':[], 'fda_guidance':[], 'FDA_Medical_reviews':[] ,'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
    
    for row_index in range(0, len(results['path'])):
        # row_string, summary_row_string = get_row_string_internal(results['keyword'][row_index], len(results['keyword_count'][row_index]), 
        #                                     results['document_type'][row_index], results['path'][row_index], results['title'][row_index],
        #                                     results['shorter_sentences'][row_index], results['normalized_tags_ordered'][row_index],
        #                                     results['normalized_tags'][row_index],results['Relevant_Check'][row_index],
        #                                     results['LDA_class'][row_index],results['correct_button_list'][row_index],
        #                                     results['wrong_button_list'][row_index] ,username)
        row_string, summary_row_string = get_row_string_internal(results['keyword'][row_index], len(results['keyword_count'][row_index]),
                                            results['full_keyword_list'][row_index], results['document_type'][row_index],
                                            results['path'][row_index], results['title'][row_index],
                                            results['tagged_shorter_sentences'][row_index], results['normalized_tags_ordered'][row_index],
                                            results['normalized_tags'][row_index],results['Relevant_Check'][row_index],
                                            results['LDA_class'][row_index],results['correct_button_list'][row_index],
                                            results['wrong_button_list'][row_index] ,username, link_exclusion)
        #print(row_string, '---- row string with fixed shorter_sentences list')
        if results['document_type'][row_index] in table_strings.keys(): #determine if source is in table_strings dictionary
            table_strings[results['document_type'][row_index]].append(row_string)
            table_summary_strings[results['document_type'][row_index]].append(summary_row_string)
        
        else:# if source does not exist in originally curated table strings dictionary add that source to the dictionary as a key then add text content
            table_strings[str(results['document_type'][row_index])] = []#add key
            table_summary_strings[str(results['document_type'][row_index])] = []#add key
            table_strings[results['document_type'][row_index]].append(row_string)#add content
            table_summary_strings[results['document_type'][row_index]].append(summary_row_string)#add content
    
    #print(table_strings,'-----doc type to appropriate row string')
    
    if username not in sumitovant_list:
        for key in table_strings.keys():
            if len(table_strings[key]) > 0: 
                ### Removed table rebolding to accommodate new sections for new sections of table
                
                #bolder line break between document types 
                #table_strings[key][-1] = table_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">')#.replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">') 
                #table_summary_strings[key][-1] = table_summary_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">')#.replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">')
                
                table_body += ''.join(table_strings[key])
                #print(table_body, '----- this is the table body')
                summary_table_body += ''.join(table_summary_strings[key])
            
                
            #table_string = table_head + str(table_body.encode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("xe2x80x93", "").replace("xe2x80x94", "").replace("xc2xa9", "").replace("xc2xa0", "").replace("xc2xab", "").replace("xe2x80x9c", "").replace("xe2x80x9d", "").replace("xc2xbb", "").replace("xc3x97", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</tbody>' + '</table>'
            
            
            table_string = table_head + table_body + '</tbody>' + '</table>'
            summary_table_string = summary_table_head + summary_table_body + '</tbody>' + '</table>'
            #table_body.replace('\u201c', '').replace('\u201d', '').replace('\xae', '').replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').replace('\xc2', '').replace('\u2013', '').strip('"') 
    #    except Exception as e:
    #        error_string =     '%s | error in table_string_results %s'%(e, str(datetime.datetime.now()))
    #        logging.error(error_string)
    else:
        for key in table_strings.keys():
            if len(table_strings[key]) > 0: 
                ### Removed table rebolding to accommodate new sections for new sections of table
                
                #bolder line break between document types 
                #table_strings[key][-1] = table_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">')#.replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">') 
                #table_summary_strings[key][-1] = table_summary_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">')#.replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">')
                
                table_body += ''.join(table_strings[key])
                #print(table_body, '----- this is the table body')
                summary_table_body += ''.join(table_summary_strings[key])
            
                
            #table_string = table_head + str(table_body.encode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("xe2x80x93", "").replace("xe2x80x94", "").replace("xc2xa9", "").replace("xc2xa0", "").replace("xc2xab", "").replace("xe2x80x9c", "").replace("xe2x80x9d", "").replace("xc2xbb", "").replace("xc3x97", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</tbody>' + '</table>'
            
            
            table_string = table_head + table_body + '</tbody>' + '</table>'
            summary_table_string = summary_table_head + summary_table_body + '</tbody>' + '</table>'
            #table_body.replace('\u201c', '').replace('\u201d', '').replace('\xae', '').replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').replace('\xc2', '').replace('\u2013', '').strip('"') 
    #    except Exception as e:
    #        error_string =     '%s | error in table_string_results %s'%(e, str(datetime.datetime.now()))
    #        logging.error(error_string)
    
    #print(table_string,'---- this is the table string')
    
    return table_string, summary_table_string

def get_row_string_internal(keyword, keyword_count, full_keyword_list, document_type, path, title, text, tags_ordered, tags,
                             relevant_check, lda_class, correct_button, wrong_button,  username, link_exclusion):
    #print(relevant_check ,'----- this is the relevant check')
    #try:
    color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                             'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
    
    border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                             'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
    
    ##Table row string formatting
    row_string = '<tr>'
    if 'Relevant' in relevant_check:
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(51, 204, 51)"><b>' + relevant_check + '</b></td>')
    elif "NR" in relevant_check:      
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(230, 46, 0)"><b>' + relevant_check + '</b></td>')
    else:
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px">  </td>')
    
    ##Inserting LDA classifier results
    if lda_class == 'relevant':
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(51, 204, 51)"><b>' + lda_class + '</b></td>')
    elif lda_class == 'not relevant':      
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(230, 46, 0)"><b>' + lda_class + '</b></td>')
    elif lda_class == 'None':
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b> </b></td>')
    elif lda_class == 'Not Evaluated':
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b> </b></td>')
    elif lda_class == '':
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b> </b></td>')
    else:
        row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b>' + lda_class +  '</b></td>')

    #Format new one liner for all keywords  rather than previous single keyword
    full_kw_string = ''
    for pos, kw_tuple in enumerate(full_keyword_list):
        if pos != len(full_keyword_list)-1: #if statement necessary to ensure proper pipe placement
            full_kw_string +=  kw_tuple[0]  + ' (' +str( kw_tuple[1]) +')' + ' || '
        else:
            full_kw_string +=  kw_tuple[0]  + ' (' +str( kw_tuple[1]) +')'
    
    #row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px">' + keyword + " (" + str(keyword_count) + ")" + '</td>')
    row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><u>' + full_kw_string + '</u></td>')
    
    #Exclude redirect links based on document type exclusion
    if document_type not in link_exclusion:
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a href="' +path.replace(" ", "%20").replace('ome_alert_document', 'curate_ome_alert_document_v2').replace('<user_name>', username) + '">' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a><br><br>' + text[:1000]  +'<br><br>') # CS added character limit, currently testing improvements
    else:
        #row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a>' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a><br><br>' + text[:1000]  +'<br><br>') # CS added character limit, currently testing improvements
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b>' + '<br><br>' + text[:1000] + '<br><br>') # CS added character limit, currently testing improvements
    
    ##Summary row string formatting
    summary_row_string = '<tr>'
    if 'Relevant' in relevant_check:
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:150px;background-color: rgb(51, 204, 51)"><b>' + relevant_check + '</b></td>')
    elif "NR" in relevant_check:      
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(230, 46, 0)"><b>' + relevant_check + '</b></td>')
    else:
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"> </td>')
    
    
    ##LDA classifier 
    if lda_class == 'relevant':
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(51, 204, 51)"><b>' + lda_class + '</b></td>')
    elif lda_class == 'not relevant':      
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px;background-color: rgb(230, 46, 0)"><b>' + lda_class + '</b></td>')
    elif lda_class == 'None':
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b> </b></td>')
    elif lda_class == 'Not Evaluated':
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b> </b></td>')
    elif lda_class == '':
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b> </b></td>')
    else:
        summary_row_string += ('<td style="border-right:1px solid #000000;border-bottom:1px solid #000000;max-width:300px"><b>' + lda_class +  '</b></td>')

    #Use previously formatted one liner for all keywords rather than previous single keyword one use
    #summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px">' + keyword + " (" + str(keyword_count) + ")" + '</td>')
    summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><u>' + full_kw_string + '</u></td>')
    
    #Exclude redirect links based on document type exclusion
    if document_type not in link_exclusion:
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a href="' +path.replace(" ", "%20").replace('ome_alert_document', 'curate_ome_alert_document_v2').replace('<user_name>', username) + '">' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') +'</a>')
    else:
        #summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a>' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') +'</a>')
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b>')
    
    ## Add in annotation option. If statement controls appearance of linked correct or wrong statement
    if correct_button != '':
        summary_row_string += ('<td style="border-bottom:1px solid #000000; border-right: 1px solid #000000; border-left: 1px solid #000000; max-width:150px"><a href =' + str(correct_button) + '>' + 'Correct' + '</a></td>')
    else:
        summary_row_string += ('<td style="border-bottom:1px solid #000000; border-right: 1px solid #000000; border-left: 1px solid #000000; max-width:150px"><a href =' + '>' + '' + '</a></td>')
    
    if wrong_button != '':
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><a href =' + str(wrong_button) + '>' + 'Wrong' + '</a></td>')
    else:
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><a href =' + '' + '>' + '' + '</a></td>')
    
    #row_string += ('<td style="border-bottom:1px solid #000000;max-width:400px">' + text + "<br><br>")
    for i in tags_ordered[:10]:
        #print(i)
        #print(results['normalized_tags'][row_index][i]['result']['type'][0])
        
        if len(tags[i]['matchtext']) > 0:
            span_string = '<span style="background-color: rgb(' + color_dictionary[tags[i]['type'][0]] + '); padding:0px; margin:0px; line-height: 1; border-radius: 0.25em; border: 1px solid; border-color: rgb(' + border_color_dictionary[tags[i]['type'][0]] + ');">' + i + ' : ' + str(len(tags[i]['matchtext'])) + '</span>  '
            row_string += span_string
    
    ##Add in the Correct vs Wrong annotation
    
    if correct_button != '':
        row_string += ('<td style="border-bottom:1px solid #000000; border-right: 1px solid #000000; border-left: 1px solid #000000; max-width:150px"><a href =' + str(correct_button) + '>' + 'Correct' + '</a></td>')
    else:
        row_string += ('<td style="border-bottom:1px solid #000000; border-right: 1px solid #000000; border-left: 1px solid #000000; max-width:150px"><a href =' + '>' + '' + '</a></td>')
    
    if wrong_button != '':
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><a href =' + str(wrong_button) + '>' + 'Wrong' + '</a></td>')
    else:
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><a href =' + '' + '>' + '' + '</a></td>')

    row_string += ('</td></tr>')

    summary_row_string += ('</td></tr>')
    #print(row_string, '---- this is the row string')
    
    #except Exception as e:
    #    error_string = '%s | error in get_row_string %s'%(e, str(datetime.datetime.now()))
    #    logging.error(error_string)
    
    #print(row_string, '--- this is the row string')
    
    return row_string, summary_row_string

def table_string_results(results, username,sumitovant_list, link_exclusion):
    table_string = ''
    summary_table_string = ''
    """Format dictionary of results as html string"""
    summary_table_head = '<table style="border:2px solid #000000;border-collapse:collapse;"><thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title </th></thead>'
    summary_table_body ='<tbody>'
    
    
    table_head = '<table style="border:2px solid #000000"><thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title | Tagged Sentence</th></thead>'
    table_body ='<tbody>'
    color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                             'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
    
    border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                             'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
    
    
    table_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'GBD_email': [], 'Cortellis': [], 'IPD':[], 'fda_guidance':[], 'FDA_Medical_reviews':[], 'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
    table_summary_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'GBD_email': [], 'Cortellis': [], 'IPD':[], 'fda_guidance':[], 'FDA_Medical_reviews':[] ,'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
    
    for row_index in range(0, len(results['path'])):
        row_string, summary_row_string = get_row_string(results['keyword'][row_index], len(results['keyword_count'][row_index]),results['full_keyword_list'][row_index] ,results['document_type'][row_index], results['path'][row_index], results['title'][row_index], results['tagged_shorter_sentences'][row_index], results['normalized_tags_ordered'][row_index], results['normalized_tags'][row_index], username, link_exclusion)
        #print(row_string, '---- row string with fixed shorter_sentences list')
        if results['document_type'][row_index] in table_strings.keys(): #determine if source is in table_strings dictionary
            table_strings[results['document_type'][row_index]].append(row_string)
            table_summary_strings[results['document_type'][row_index]].append(summary_row_string)
        else:# if source does not exist in originally curated table strings dictionary add that source to the dictionary as a key then add text content
            table_strings[str(results['document_type'][row_index])] = []#add key
            table_summary_strings[str(results['document_type'][row_index])] = []#add key
            table_strings[results['document_type'][row_index]].append(row_string)#add content
            table_summary_strings[results['document_type'][row_index]].append(summary_row_string)#add content
    
    #setting up document keys
    
    if username not in sumitovant_list:
        for key in table_strings.keys():
            if len(table_strings[key]) > 0: 
                #bolder line break between document types  
                table_strings[key][-1] = table_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">').replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">') 
                table_summary_strings[key][-1] = table_summary_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">').replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">')
                
                table_body += ''.join(table_strings[key])
                #print(table_body, '----- this is the table body')
                summary_table_body += ''.join(table_summary_strings[key])
    else:
        for key in table_strings.keys():
            if len(table_strings[key]) > 0: 
                #bolder line break between document types  
                table_strings[key][-1] = table_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">').replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">') 
                table_summary_strings[key][-1] = table_summary_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">').replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">')
                
                table_body += ''.join(table_strings[key])
                #print(table_body, '----- this is the table body')
                summary_table_body += ''.join(table_summary_strings[key])
    
        
    #table_string = table_head + str(table_body.encode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("xe2x80x93", "").replace("xe2x80x94", "").replace("xc2xa9", "").replace("xc2xa0", "").replace("xc2xab", "").replace("xe2x80x9c", "").replace("xe2x80x9d", "").replace("xc2xbb", "").replace("xc3x97", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</tbody>' + '</table>'
    
    
    table_string = table_head + table_body + '</tbody>' + '</table>'
    summary_table_string = summary_table_head + summary_table_body + '</tbody>' + '</table>'
    #table_body.replace('\u201c', '').replace('\u201d', '').replace('\xae', '').replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').replace('\xc2', '').replace('\u2013', '').strip('"') 
    
    return table_string, summary_table_string

def get_row_string(keyword, keyword_count, full_keyword_list ,document_type, path, title, text, tags_ordered, tags, username, link_exclusion):

    color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                             'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
    
    border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                             'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
    
    #Format new one liner for all keywords  rather than previous single keyword
    full_kw_string = ''
    for pos, kw_tuple in enumerate(full_keyword_list):
        if pos != len(full_keyword_list)-1: #if statement necessary to ensure proper pipe placement
            full_kw_string +=  kw_tuple[0]  + ' (' +str( kw_tuple[1]) +')' + ' || '
        else:
            full_kw_string +=  kw_tuple[0]  + ' (' +str( kw_tuple[1]) +')'

    row_string = '<tr>'
    row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px"><u>' + full_kw_string + '</u></td>')
    
    if document_type not in link_exclusion:
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a href="' +path.replace(" ", "%20").replace('ome_alert_document', 'curate_ome_alert_document_v2').replace('<user_name>', username) + '">' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a><br><br>' + text[:1000] + '<br><br>') # CS added character limit, currently testing improvements
    else:
        #row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a>' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a><br><br>' + text[:1000] + '<br><br>') # CS added character limit, currently testing improvements
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b>' + '<br><br>' + text[:1000] + '<br><br>') # CS added character limit, currently testing improvements
    
    summary_row_string = '<tr>'
    summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px">' + keyword + " (" + str(keyword_count) + ")" + '</td>')
    
    #exclude redirect link based on document type
    if document_type not in link_exclusion:
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a href="' +path.replace(" ", "%20").replace('ome_alert_document', 'curate_ome_alert_document_v2').replace('<user_name>', username) + '">' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a>')
    else:
        #summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a>' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a>')
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> ')#
                
    #row_string += ('<td style="border-bottom:1px solid #000000;max-width:400px">' + text + "<br><br>")
    for i in tags_ordered[:10]:
        #print(i)
        #print(results['normalized_tags'][row_index][i]['result']['type'][0])
        
        if len(tags[i]['matchtext']) > 0:
            span_string = '<span style="background-color: rgb(' + color_dictionary[tags[i]['type'][0]] + '); padding:0px; margin:0px; line-height: 1; border-radius: 0.25em; border: 1px solid; border-color: rgb(' + border_color_dictionary[tags[i]['type'][0]] + ');">' + i + ' : ' + str(len(tags[i]['matchtext'])) + '</span>  '
            row_string += span_string
    row_string += ('</td></tr>')
    summary_row_string += ('</td></tr>')
    #print(row_string, '---- this is the row string')
    

    
    return row_string, summary_row_string


class Outlook():
    def __init__(self):
        mydate = datetime.datetime.now()-datetime.timedelta(1)
        self.today = mydate.strftime("%d-%b-%Y")
        
        # self.imap = imaplib.IMAP4_SSL('imap-mail.outlook.com')
        # self.smtp = smtplib.SMTP('smtp-mail.outlook.com')

    def login(self, username, password):
        self.username = username
        self.password = password
        while True:
            try:
                self.imap = imaplib.IMAP4_SSL(config_email.imap_server,config_email.imap_port)
                r, d = self.imap.login(username, password)
                assert r == 'OK', 'login failed'
                print(" > Sign as ", d)
                
            except:
                print(" > Sign In ...")
                continue
            # self.imap.logout()
            break

    def sendEmailMIME(self, recipient, subject, message):
        msg = email.mime.multipart.MIMEMultipart()
        msg['to'] = recipient
        msg['from'] = self.username
        msg['subject'] = subject
        msg.add_header('reply-to', self.username)
        # headers = "\r\n".join(["from: " + "sms@kitaklik.com","subject: " + subject,"to: " + recipient,"mime-version: 1.0","content-type: text/html"])
        # content = headers + "\r\n\r\n" + message
        try:
            self.smtp = smtplib.SMTP(config_email.smtp_server, config_email.smtp_port)
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.username, self.password)
            self.smtp.sendmail(msg['from'], [msg['to']], msg.as_string())
            print("   email replied")
        except smtplib.SMTPException:
            print("Error: unable to send email")

    def sendEmail(self, recipient, subject, message):
        headers = "\r\n".join([
            "from: " + self.username,
            "subject: " + subject,
            "to: " + recipient,
            "mime-version: 1.0",
            "content-type: text/html"
        ])
        content = headers + "\r\n\r\n" + message
        while True:
            try:
                self.smtp = smtplib.SMTP(config_email.smtp_server, config_email.smtp_port)
                self.smtp.ehlo()
                self.smtp.starttls()
                self.smtp.login(self.username, self.password)
                self.smtp.sendmail(self.username, recipient, content)
                print("   email replied")
            except Exception as exception:
                print(exception)
                print("   Sending email...")
                #continue
            break

    def list(self):
        # self.login()
        return self.imap.list()

    def select(self, str):
        return self.imap.select(str)

    def inbox(self):
        return self.imap.select("Inbox")

    def junk(self):
        return self.imap.select("Junk")

    def logout(self):
        return self.imap.logout()

    def today(self):
        mydate = datetime.datetime.now()
        return mydate.strftime("%d-%b-%Y")

    def unreadIdsToday(self):
        r, d = self.imap.search(None, '(SINCE "'+self.today+'")', 'UNSEEN')
        list = d[0].split(' ')
        return list

    def getIdswithWord(self, ids, word):
        stack = []
        for id in ids:
            self.getEmail(id)
            if word in self.mailbody().lower():
                stack.append(id)
        return stack

    def unreadIds(self):
        r, d = self.imap.search(None, "UNSEEN")
        list = d[0].split(b' ')
        return list

    def hasUnread(self):
        list = self.unreadIds()
        return list != ['']

    def readIdsToday(self):
        r, d = self.imap.search(None, '(SINCE "'+self.today+'")', 'SEEN')
        list = d[0].split(' ')
        return list

    def allIds(self):
        r, d = self.imap.search(None, "ALL")
        list = d[0].split(' ')
        return list

    def readIds(self):
        r, d = self.imap.search(None, "SEEN")
        list = d[0].split(' ')
        return list

    def getEmail(self, id):
        r, d = self.imap.fetch(id, "(RFC822)")
        #self.raw_email = d[0][1].decode('ascii')
        self.raw_email = d[0][1].decode('ascii')
        self.email_message = email.message_from_string(self.raw_email)
        #self.imap.put_PeekMode(False)
        return self.email_message

    def unread(self):
        list = self.unreadIds()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def read(self):
        list = self.readIds()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def readToday(self):
        list = self.readIdsToday()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def unreadToday(self):
        list = self.unreadIdsToday()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def readOnly(self, folder):
        return self.imap.select(folder, readonly=True)

    def writeEnable(self, folder):
        return self.imap.select(folder, readonly=False)

    def rawRead(self):
        list = self.readIds()
        latest_id = list[-1]
        r, d = self.imap.fetch(latest_id, "(RFC822)")
        self.raw_email = d[0][1]
        return self.raw_email

    def mailbody(self):
        if self.email_message.is_multipart():
            for payload in self.email_message.get_payload():
                # if payload.is_multipart(): ...
                body = (
                    payload.get_payload()
                    .split(self.email_message['from'])[0]
                    .split('\r\n\r\n2015')[0]
                )
                return body
        else:
            body = (
                self.email_message.get_payload()
                .split(self.email_message['from'])[0]
                .split('\r\n\r\n2015')[0]
            )
            return body

    def mailsubject(self):
        return self.email_message['Subject']

    def mailfrom(self):
        return self.email_message['from']

    def mailto(self):
        return self.email_message['to']

    def mailreturnpath(self):
        return self.email_message['Return-Path']

    def mailreplyto(self):
        return self.email_message['Reply-To']

    def mailall(self):
        return self.email_message

    def mailbodydecoded(self):
        return base64.urlsafe_b64decode(self.mailbody())

def headlines_check(ome_alert_results, user):
    #print('entering headlines check')
    doc_id_list = ome_alert_results['document_id']
    #print(doc_id_list,'---- these are the doc ids to search there is a problem here')

    ome_alert_results['Relevant_Check'] = []
    ome_alert_results['correct_button_list'] = []
    ome_alert_results['wrong_button_list'] = []
    for solr_doc_id in doc_id_list:
        try:
            #print(solr_doc_id,'--- this is the solr_doc_id')
            headlines_query = '''SELECT * 
            FROM nlp_oss.ome_headlines_results_solr
            WHERE solr_doc_id = "{}"'''.format(solr_doc_id)
            
            
            db = start_headlines_db()
            cur = db.cursor()
            cur.execute(headlines_query)
            headlines_df = cur.fetchall()
            headlines_df = pd.DataFrame(headlines_df, columns = ['id','text','ome_headlines_scores','solr_doc_id','solr_instance_ip','solr_doc_modified_dt','ome_headlines_version','processed_dt'])
            if len(headlines_df) > 0:
                #print(headlines_df.columns,'---- this is the headlines_df')
                try:
                    headlines_score = headlines_df['ome_headlines_scores'].values[0]
                except Exception as e:
                    print(e)
                    headlines_score = 0
            
                #print(headlines_score,'---- this is the headlines score')
                
                if headlines_score > .50:
                    round_score = np.round(headlines_score*100)
                    ome_alert_results['Relevant_Check'].append('Relevant ({}%)'.format(str(round_score)))
                else:
                    round_score = np.round(headlines_score*100)
                    ome_alert_results['Relevant_Check'].append('NR ({}%)'.format(str(round_score)))
                
                correct_button = 'http://52.23.161.54/annotate/%s/%s/correct'%(str(user),str(headlines_df['id'].values[0]))
                wrong_button = 'http://52.23.161.54/annotate/%s/%s/wrong'%(str(user),str(headlines_df['id'].values[0]))

                ome_alert_results['correct_button_list'].append(correct_button)
                ome_alert_results['wrong_button_list'].append(wrong_button)

                #print(correct_button, '---- this the correct button')
                #print(wrong_button, '----- this is the wrong button')
            else:
                #print(solr_doc_id, '--- not found in sql table automatic zero')
                ome_alert_results['Relevant_Check'].append('No Eval')
                
                correct_button = ''
                wrong_button = ''
                
                ome_alert_results['correct_button_list'].append(correct_button)
                ome_alert_results['wrong_button_list'].append(wrong_button)
        except:
            ome_alert_results['Relevant_Check'].append('No Eval')
            
            correct_button = ''
            wrong_button = ''

            ome_alert_results['correct_button_list'].append(correct_button)
            ome_alert_results['wrong_button_list'].append(wrong_button)

    return ome_alert_results

def source_filter(results):
    
    doc_ids = results['document_id']
    
    doc_lists = ['Cortellis','cortellis']#,'clinical_trials']
    
    doc_types = results['document_type']
    #print('we are in source filter')
    
    elems_to_rm = []
    #print(type(doc_types), '--- these are the doc types')
    for pos, i in enumerate(doc_ids):
        #print(i, '--- these are the doc types')
        #print(type(i))
        cond1 = (len([x for x in doc_lists if x in i]) > 0) and ("Drug_Status_Changes_alert" in i) and ("full_email" in i) #generic cortellis filter but we don't want the non drug status changes alerts in the ome alert now
        cond2 = ("clinical_trials" in doc_types[pos])
        #cond2 = "Drug_Status_Changes_alert" in i # we don't want the non drug status changes alerts in the ome alert now
        #cond3 = "full_email" in i  #We only want the non full htmls from the new improved cortellis parsing
        
        #print(cond1a, '--- is it a cortellis document')
        #print(cond2, 'condition2 ')
        #print(cond3, 'condition3')
        
        #print(cond1, '---- did all conditions pass?')
        
        if cond1 == True or cond2 == True: #and cond3 == True:
            #print(i, '--- conditional allows this')
            elems_to_rm.append(pos)
    
    elems_to_rm = sorted(elems_to_rm, reverse = True)
    
    for key in results.keys():
        section = results[key]
        for d in elems_to_rm:
            #print(d, '--- element to remove')
            del section[d]
        
    return results 
    
    #print(results, '---- the results in source fitler')

    
def send_ome_alerts_of_user(user):
    #try:
    """Get OME alerts of user (firstname.lastname) - execute SOLR search and send results as email"""
    
    internal_users = ['julia.gray','bill.mcmahon','cody.schiffer',
                      'isabel.metzger','yoann.randriamihaja', 'samuel.croset', 
                      'houston.warren', 'rajat.chandra','carson.tao']
    #internal_users = ['']    
    
    sumitovant_list = ['julia.gray','bill.mcmahon','cody.schiffer',
                      'isabel.metzger','yoann.randriamihaja', 'samuel.croset', 
                      'houston.warren', 'rajat.chandra', 'natasha.zalzinyak','justin.dimartino','sam.azoulay','carson.tao']

    #sumitovant_list = internal_users + 

    user_alerts, user_alert_ids = get_documents.get_ome_alerts_of_user(user)
    time.sleep(10)
    
    from_date = datetime.date.today() - datetime.timedelta(days=1)
    #from_date = datetime.date(2019,2,3)
    to_date = datetime.date.today()
    #to_date = datetime.date(2019,3,25)
    
    #link_exclusion_ls = ['Cortellis','cortellis', 'Adis','evaluate_email', 'GBD_email']
    
    sub_services = ['Adis Insight','Cortellis','GBD_email','Evaluate News']
    
    link_exclusion_ls = ['Cortellis','cortellis', 'Adis Insight','Evaluate News', 'GBD_email']

    mail = 'not_initialized'
    
    for i in range(0, len(user_alert_ids)):
        if (user_alerts['email'][i] == 'yes'): #and (user_alerts['alert_type'][i] in ['standard', 'standard_title']):
            try:
                search_params_list, keyword_title, search_list = get_documents.get_search_params_list(str(user_alert_ids[i]))
                #print(search_params_list,'----- this is the search params list')
                #ome_alert_results, url_query = get_documents.get_ome_alert_results(search_params_list, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')
                
                ome_alert_results, url_query = get_documents.get_ome_alert_results(search_params_list, search_list, sub_services ,from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')
                
                #print(ome_alert_results.keys(), '---- these are the ome alerts results')
                #print(np.array(ome_alert_results['keyword']), '---- keyword per document found')
                if user in internal_users:
                    ome_alert_results = headlines_check(ome_alert_results, user)
                #print(ome_alert_results.keys(),'---- this is post ome_alert_results')
                
                #Apply cortellis filters to all ome alerts
                ome_alert_results = source_filter(ome_alert_results)
                
                
                if len(ome_alert_results['path']) > 0:
                    if user in sumitovant_list:
                        email_address = user + '@sumitovant.com'
                        #source_filter(ome_alert_results)
                    else:
                        email_address = user + '@roivant.com'
                    #email_address = 'julia.gray@roivant.com'
                    email_subject = 'OME alert: ' + keyword_title + ' (' + str(to_date) + ')'
                    if user in internal_users:
                        table_string, summary_table_string = table_string_results_internal(ome_alert_results, user, sumitovant_list, link_exclusion_ls)
                    else:
                        table_string, summary_table_string = table_string_results(ome_alert_results, user, sumitovant_list, link_exclusion_ls)
                    email_string = "<html><head></head><body><h4>Summary (" + str(len(ome_alert_results['keyword'])) + " results)</h4>" + summary_table_string + "<br><br><h4>Documents</h4>" + table_string + "</body></html>"
                    #email_string = "<html><head></head><body><h4>Testing email</h4></body></html>"
                    print(email_address)
                    print(email_subject)
                    #print(email_string)
                    
                    
                
                    if mail != 'not_initialized':
                        mail.sendEmail(email_address, email_subject, email_string)
                    else:
                        mail = Outlook()
                        mail.login('comp.res@sumitovant.com','Sumitovant$cr0220')
                        #mail.login('comp.res@roivant.com','Roivant$cr0220!')
                        mail.inbox()
                        mail.sendEmail(email_address, email_subject, email_string)
                        #print(undefined_variable)
                else:
                    print(ome_alert_results['keyword'],'---- keywords in empty email')
                    print('empty email')
            except Exception as e:
                id_failure = 'OME Alert failure at {}'.format(user_alert_ids[i])
                print(id_failure,'---- failure at id')
                print(e)
                #error_string = '%s | error in send_ome_alerts_of_user() %s' %(id_failure, str(datetime.datetime.now()))
                #logging.error(error_string)
                continue
#    except Exception as e:
#        error_string = '%s | error in send_ome_alerts_of_user() %s', (e, str(datetime.datetime.now()))
#        logging.error(error_string)
    
    return user_alert_ids

def send_ome_alerts():
    #try:
    """Loop through all users who have OME alerts set with emails"""
    
    query = """SELECT DISTINCT `user` FROM ome_star_schema.ome_alerts
        WHERE email_alert = 'yes'"""
    user_list = []
    db = start_db()
    cur = db.cursor()
    cur.execute(query)
    
    for row in cur.fetchall():
        user_list.append(row[0].replace('ROIVANT\\', ''))
    
    #print(user_list)
    
    for u in user_list:
        ome_alerts = send_ome_alerts_of_user(u)
            
    
#    except Exception as e:
#        error_string = '%s | error in send_ome_alerts %s' %(e, str(datetime.datetime.now()))
#        logging.error(error_string)
        

def send_completion_notification(user):
    """Send alert completion notification"""
        
    solr_test = 'http://10.115.1.195:8983/solr/opensemanticsearch/select?fl=id&q=*&rows=1'
    #solr_test = 'http://10.115.1.195:8983/so/opensemanticsearch/sele?fl=id&q=*&rows=1'
    
    html_test = get_html(solr_test)
    
    if html_test != None:
        html_test_result = True
    else:
        html_test_result = False
    
    if html_test_result == True:
        from_date = datetime.date.today() - datetime.timedelta(days=1)
        email_address = user + '@sumitovant.com'
        email_subject = 'OME Alerts Completion ' + ' (' + str(from_date) + ')'
        email_string = "<html><head></head><body><h4></h4>" + 'Indexing complete from date in subject line' + "</body></html>"
    else:
        from_date = datetime.date.today() - datetime.timedelta(days=1)
        email_address = user + '@sumitovant.com'
        email_subject = 'OME Alerts Failure ' + ' (' + str(from_date) + ')'
        email_string = "<html><head></head><body><h4></h4>" + 'Solr is down' + "</body></html>"

    #email_string = "<html><head></head><body><h4>Testing email</h4></body></html>"
    print(email_address)
    print(email_subject)
    #print(email_string)
                    
                    
                
    mail = Outlook()
    #mail.login('comp.res@roivant.com','Roivant$cr0220!')
    mail.login('comp.res@sumitovant.com','Sumitovant$cr0220')
    mail.inbox()
    mail.sendEmail(email_address, email_subject, email_string)
    #print(undefined_variable)

    return 1+1

def send_successful_search(user):
    """Send alert completion notification"""
        
    solr_test = 'http://10.115.1.195:8983/solr/opensemanticsearch/select?fl=id&q=*&rows=1'
    #solr_test = 'http://10.115.1.195:8983/solr/opensemanticsearch/sele?fl=id&q=*&rows=1'
    
    html_test = get_html(solr_test)

    if html_test != None:
        html_test_result = True
    else:
        html_test_result = False
    
    if html_test_result == True:
        from_date = datetime.date.today() - datetime.timedelta(days=1)
        email_address = user + '@roivant.com'
        email_subject = 'Search Completion ' + ' (' + str(from_date) + ')'
        email_string = "<html><head></head><body><h4></h4>" + 'All Searches Complete - those searches returned are those with results' + "</body></html>"
    else:
        from_date = datetime.date.today() - datetime.timedelta(days=1)
        email_address = user + '@roivant.com'
        email_subject = 'Search Failure ' + ' (' + str(from_date) + ')'
        email_string = "<html><head></head><body><h4></h4>" + 'Computational Research is investigating the problem. If you have further questions, please reach out to cody.schiffer@sumitovant.com' + "</body></html>"
    #email_string = "<html><head></head><body><h4>Testing email</h4></body></html>"
    print(email_address)
    print(email_subject)
    #print(email_string)
                    
                    
                
    mail = Outlook()
    #mail.login('comp.res@roivant.com','Roivant$cr0220!')
    mail.login('comp.res@sumitovant.com','Sumitovant$cr0220')
    mail.inbox()
    mail.sendEmail(email_address, email_subject, email_string)
    #print(undefined_variable)

    return 1+1

#yoanns_alerts = send_ome_alerts_of_user('yoann.randriamihaja')
#bills_alert_ids = send_ome_alerts_of_user('bill.mcmahon')
#julias_alert_ids = send_ome_alerts_of_user('julia.gray')
#codys_alert_ids = send_ome_alerts_of_user('cody.schiffer')
#ryans_alert_ids = send_ome_alerts_of_user('ryan.costa')
#daniels_alert_ids = send_ome_alerts_of_user('daniel.kwon')
#archits_alert_ids = send_ome_alerts_of_user('archit.sheth-shah')
#emirs_alert_ids = send_ome_alerts_of_user('emir.haskovic')
#anythonys_alert_ids = send_ome_alerts_of_user('anthony.bogachev')
send_ome_alerts()
time.sleep(120)
codys_alert_completion = send_completion_notification('cody.schiffer')
codys_search_completion = send_successful_search('cody.schiffer')
time.sleep(120)
yoanns_alert_completion = send_completion_notification('yoann.randriamihaja')
time.sleep(120)
aymans_search_completion = send_successful_search('ayman.mohammad')
time.sleep(120)
andrews_search_completion = send_successful_search('andrew.bogorad')

# #print('done')
#print('second debug')

# #DEBUGGING FUNCTIONS --------------
# from_date = datetime.date(2020,8,10)
# #from_date = datetime.date.today() - datetime.timedelta(days=1)
# to_date = datetime.date(2020,8,10)
# #to_date = datetime.date.today()
# #internal_users = ['cody.schiffer']
# internal_users = ['']
# user = 'cody.schiffer'
# sumitovant_list = ['julia.gray','bill.mcmahon','cody.schiffer',
#                       'isabel.metzger','yoann.randriamihaja', 'samuel.croset', 
#                       'houston.warren', 'rajat.chandra', 'natasha.zalzinyak','justin.dimartino','sam.azoulay','carson.tao']

# email_address = 'cody.schiffer@sumitovant.com'
# email_subject = "DEBUGDEBUGDEBUGDEBUG"
# #email_subject = 'Sample Newsletter content PAH {}'.format(from_date)


# sub_services = ['Adis Insight','Cortellis','GBD_email','Evaluate News']

# test_search_params, test_alert_title, search_list = get_documents.get_search_params_list('485')
# #print(test_search_params,'---- these are the test params')


# ##test_url = get_documents.construct_solr_search_url(test_search_params, from_date=from_date)
# #ome_alert_results = source_filter(ome_alert_results)

# # ##test_search_params = [{'search_type': 'standard', 'keyphrase1': 'Trace amine associated receptor 1', 'keyword': 'Trace amine associated receptor 1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}, {'search_type': 'standard', 'keyphrase1': 'Trace amine-associated receptor 1', 'keyword': 'Trace amine-associated receptor 1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}, {'search_type': 'standard', 'keyphrase1': 'TaR-1', 'keyword': 'TaR-1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}, {'search_type': 'standard', 'keyphrase1': 'Trace amine receptor 1', 'keyword': 'Trace amine receptor 1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}, {'search_type': 'standard', 'keyphrase1': 'TAAR1', 'keyword': 'TAAR1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}, {'search_type': 'standard', 'keyphrase1': 'Taar-1', 'keyword': 'Taar-1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}, {'search_type': 'standard', 'keyphrase1': 'TAR-1', 'keyword': 'TAR-1', 'source_select': 'all', 'alert_title': 'TAAR1_Sunovion_OME_Alert', 'filter_type': 'or', 'journal_select': '', 'author_select': '', 'institution_select': '', 'filter_leeway': 70}]
# ome_alert_results, url_query = get_documents.get_ome_alert_results(test_search_params, search_list, sub_services ,from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')

# #Source filtering
# ome_alert_results = source_filter(ome_alert_results)

# link_exclusion_ls = ['Cortellis','cortellis', 'Adis Insight','Evaluate News', 'GBD_email']


# ##
# ##Internal users
# ##if user in internal_users:

# ome_alert_results = headlines_check(ome_alert_results, user)
# table_string_internal, summary_table_string_internal = table_string_results_internal(ome_alert_results, user, sumitovant_list, link_exclusion_ls)

# # #print(ome_alert_results)

# email_string_internal = "<html><head></head><body><h4>Summary (" + str(len(ome_alert_results['keyword'])) + " results)</h4>" + summary_table_string_internal + "<br><br><h4>Documents</h4>" + table_string_internal + "</body></html>"

# mail = Outlook()
# mail.login('comp.res@sumitovant.com','Sumitovant$cr0220')
# #mail.login('comp.res@roivant.com','Roivant$cr0220!')
# mail.inbox()
# mail.sendEmail(email_address, email_subject, email_string_internal)
 


####
##Non-internal

##else:
# table_string, summary_table_string = table_string_results(ome_alert_results, user, sumitovant_list,link_exclusion_ls)

# email_string = "<html><head></head><body><h4>Summary (" + str(len(ome_alert_results['keyword'])) + " results)</h4>" + summary_table_string + "<br><br><h4>Documents</h4>" + table_string + "</body></html>"

# mail = Outlook()
# mail.login('comp.res@sumitovant.com','Sumitovant$cr0220')
# #mail.login('comp.res@roivant.com','Roivant$cr0220!')
# mail.inbox()
# mail.sendEmail(email_address, email_subject, email_string)

# #------------------------------------

#julias_alerts, julias_alert_ids = get_documents.get_ome_alerts_of_user('julia.gray')
#clean_keyword_list, keyword_title = get_documents.get_keyword_list_from_ome_alert_id('97')
#clean_keyword_list = [['TNF-A'],['jak/stat'], ['alpha-synuclein'],['JAK'],['JAK-STAT'],['fail']]
#ome_alert_results, url_query = get_documents.get_ome_alert_results(clean_keyword_list, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')

#search_params_list, keyword_title = get_documents.get_search_params_list('39')
#url_query = get_documents.construct_solr_search_url(search_params_list[0], from_date, to_date)
#solr_results = get_documents.get_solr_results(search_params_list[0]['keyword'], url_query, tags='tagged_entities_for_email', from_date=from_date, to_date=to_date)


#pickle.dump(ome_alert_results, open('R:/Business Development/Computational Research/OME alerts/Clinical Trial Results/2019_documents_tagged.p', 'wb'))


#with open ('R:/Business Development/Computational Research/OME alerts/Clinical Trial Results/2019_documents_untagged.p', 'rb') as fp:
#    ome_alert_results_dict = pickle.load(fp)
    

#table_string, summary_string = table_string_results(ome_alert_results)
#table_string_results()
#email_address = 'cody.schiffer@roivant.com'
#email_subject = 'Testing OME alerts --- journal_select'
#email_string = ("<html><head></head><body>" + table_string + "</body></html>")
#email_string = "<html><head></head><body><h4>Summary (" + str(len(ome_alert_results['keyword'])) + " results)</h4>" + summary_string + "<br><br><h4>Documents</h4>" + table_string + "</body></html>"
####                    
####
#mail = Outlook()
#mail.login('comp.res@roivant.com','Roivant$cr0220!')
#mail.inbox()
#mail.sendEmail(email_address, email_subject, email_string)
##
#

#test_text = ome_alert_results['document_text'][2]
#print(test_text)
###############################################################################

         ################Table String Debuging#################

###############################################################################
#table_string = ''
#summary_table_string = ''
#
#"""Format dictionary of results as html string"""
#summary_table_head = '<table style="border:2px solid #000000;border-collapse:collapse;"><thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title </th></thead>'
#summary_table_body ='<tbody>'
#
#
#table_head = '<table style="border:2px solid #000000"><thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title | Tagged Sentence</th></thead>'
#table_body ='<tbody>'
#color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
#                         'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
#
#border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
#                         'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
#
#
#table_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
#table_summary_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
#
#for row_index in range(0, len(ome_alert_results['keyword'])):
#    row_string, summary_row_string = get_row_string(ome_alert_results['keyword'][row_index], len(ome_alert_results['keyword_count'][row_index]), ome_alert_results['document_type'][row_index], ome_alert_results['path'][row_index], ome_alert_results['title'][row_index], ome_alert_results['shorter_sentences'][row_index], ome_alert_results['normalized_tags_ordered'][row_index], ome_alert_results['normalized_tags'][row_index])
#    #print(row_string , '----- this is the row string')
#    #print(summary_row_string,  '------- this is the summary row string')
#    if ome_alert_results['document_type'][row_index] in table_strings:
#        table_strings[ome_alert_results['document_type'][row_index]].append(row_string)
#        #print(table_strings, '---- this is the table string')
#        table_summary_strings[ome_alert_results['document_type'][row_index]].append(summary_row_string)
#    else:# if source does not exist in originally curated table strings dictionary add that source to the dictionary as a key then add text content
#        table_strings[str(ome_alert_results['document_type'][row_index])] = []#add key
#        table_summary_strings[str(ome_alert_results['document_type'][row_index])] = []#add key
#        table_strings[ome_alert_results['document_type'][row_index]].append(row_string)#add content
#        table_summary_strings[ome_alert_results['document_type'][row_index]].append(summary_row_string)#add content
#        
#for key in table_strings.keys():#adjust to have dynamically defined key list
#    if len(table_strings[key]) > 0: 
#                  #bolder line break between document types  
#        table_strings[key][-1] = table_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">').replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">') 
#        table_summary_strings[key][-1] = table_summary_strings[key][-1].replace('<td style="border-bottom:1px solid #000000;max-width:150px">','<td style="border-bottom:2px solid #000000;max-width:150px">').replace('<td style="border-bottom:1px solid #000000;max-width:300px">', '<td style="border-bottom:2px solid #000000;max-width:300px">')
#        
#        table_body += ''.join(table_strings[key])
#        #print(table_body, '----- this is the table body')
#        summary_table_body += ''.join(table_summary_strings[key])
#
#    
##table_string = table_head + str(table_body.encode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("xe2x80x93", "").replace("xe2x80x94", "").replace("xc2xa9", "").replace("xc2xa0", "").replace("xc2xab", "").replace("xe2x80x9c", "").replace("xe2x80x9d", "").replace("xc2xbb", "").replace("xc3x97", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</tbody>' + '</table>'
#
#
#table_string = table_head + table_body + '</tbody>' + '</table>'
#summary_table_string = summary_table_head + summary_table_body + '</tbody>' + '</table>'
#table_body.replace('\u201c', '').replace('\u201d', '').replace('\xae', '').replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').replace('\xc2', '').replace('\u2013', '').strip('"') 
