# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 14:51:43 2019

@author: julia.gray
"""
try:
    import MySQLdb
except:
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

import get_documents

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

def table_string_results(results, username):
    table_string = ''
    summary_table_string = ''
    try:
        """Format dictionary of results as html string"""
        summary_table_head = '<table style="border:2px solid #000000;border-collapse:collapse;"><thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title </th></thead>'
        summary_table_body ='<tbody>'
        
        
        table_head = '<table style="border:2px solid #000000"><thead><th style="border-bottom:2px solid #000000;max-width:150px">Keyword (count)</th><th style="border-bottom:2px solid #000000;max-width:400px">Document Type | Title | Tagged Sentence</th></thead>'
        table_body ='<tbody>'
        color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                                 'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
        
        border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                                 'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
        
        
        table_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
        table_summary_strings = {'press_release':[], 'clinical_trials':[], 'pubmed_abstract':[], 'pubmed_article':[], 'newswire':[], 'pr_newswire':[], 'streetaccount':[], 'google_news':[], 'SEC_filing':[]}
        
        for row_index in range(0, len(results['keyword'])):
            row_string, summary_row_string = get_row_string(results['keyword'][row_index], len(results['keyword_count'][row_index]), results['document_type'][row_index], results['path'][row_index], results['title'][row_index], results['shorter_sentences'][row_index], results['normalized_tags_ordered'][row_index], results['normalized_tags'][row_index], username)
            #print(row_string, '---- row string with fixed shorter_sentences list')
            if results['document_type'][row_index] in table_strings.keys(): #determine if source is in table_strings dictionary
                table_strings[results['document_type'][row_index]].append(row_string)
                table_summary_strings[results['document_type'][row_index]].append(summary_row_string)
            else:# if source does not exist in originally curated table strings dictionary add that source to the dictionary as a key then add text content
                table_strings[str(results['document_type'][row_index])] = []#add key
                table_summary_strings[str(results['document_type'][row_index])] = []#add key
                table_strings[results['document_type'][row_index]].append(row_string)#add content
                table_summary_strings[results['document_type'][row_index]].append(summary_row_string)#add content
                
        for key in ['press_release','clinical_trials','pubmed_abstract','pubmed_article', 'streetaccount', 'newswire', 'pr_newswire', 'google_news', 'SEC_filing']:
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
    except Exception as e:
        error_string =     '%s | error in table_string_results %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    return table_string, summary_table_string

def get_row_string(keyword, keyword_count, document_type, path, title, text, tags_ordered, tags, username):

    try:
        color_dictionary = {'company_OME_txt_ss':'237, 249, 213', 'drug_OME_txt_ss':'217, 244, 255', 'indication_MeSH_txt_ss':'213, 241, 238', 'indication_OME_txt_ss':'213, 241, 238', 'indication_OME2_txt_ss':'213, 241, 238', 'indication_MeSH_orpha_txt_ss':'213, 241, 238', 'indication_MeSH_suppl_txt_ss':'213, 241, 238',
                                 'indication_Treato_txt_ss':'213, 241, 238', 'target_ChemBL_txt_ss':'249, 204, 230', 'target_OME_txt_ss':'249, 204, 230', 'target_MeSH_txt_ss':'249, 204, 230'}
        
        border_color_dictionary = {'company_OME_txt_ss':'166, 226, 45', 'drug_OME_txt_ss':'67, 198, 252', 'indication_MeSH_txt_ss':'47, 187, 171', 'indication_OME_txt_ss':'47, 187, 171', 'indication_OME2_txt_ss':'47, 187, 171', 'indication_MeSH_orpha_txt_ss':'47, 187, 171', 'indication_MeSH_suppl_txt_ss':'47, 187, 171',
                                 'indication_Treato_txt_ss':'47, 187, 171', 'target_ChemBL_txt_ss':'224, 0, 132', 'target_OME_txt_ss':'224, 0, 132', 'target_MeSH_txt_ss':'224, 0, 132'}
        

        row_string = '<tr>'
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px">' + keyword + " (" + str(keyword_count) + ")" + '</td>')
        row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a href="' +path.replace(" ", "%20").replace('ome_alert_document', 'curate_ome_alert_document_v2').replace('<user_name>', username) + '">' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a><br><br>' + text[:1000] + '<br><br>') # CS added character limit, currently testing improvements
        
        summary_row_string = '<tr>'
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:150px">' + keyword + " (" + str(keyword_count) + ")" + '</td>')
        summary_row_string += ('<td style="border-bottom:1px solid #000000;max-width:300px"><b>' + document_type.replace('_',' ').title() + '</b> | <a href="' +path.replace(" ", "%20").replace('ome_alert_document', 'curate_ome_alert_document_v2').replace('<user_name>', username) + '">' + str(title.encode('ascii','ignore').decode('utf-8')).strip("b\'").strip("\'").replace("\\", "").replace("\'", "").replace("xe2x80x99", "").replace("xc2xae", "").replace("``", "").replace("//", "").replace("’", '"').strip('"') + '</a>')
        
                    
        #row_string += ('<td style="border-bottom:1px solid #000000;max-width:400px">' + text + "<br><br>")
        for i in tags_ordered[:5]:
            #print(i)
            #print(results['normalized_tags'][row_index][i]['result']['type'][0])
            
            if len(tags[i]['matchtext']) > 0:
                span_string = '<span style="background-color: rgb(' + color_dictionary[tags[i]['type'][0]] + '); padding:0px; margin:0px; line-height: 1; border-radius: 0.25em; border: 1px solid; border-color: rgb(' + border_color_dictionary[tags[i]['type'][0]] + ');">' + i + ' : ' + str(len(tags[i]['matchtext'])) + '</span>  '
                row_string += span_string
        row_string += ('</td></tr>')
        summary_row_string += ('</td></tr>')
        #print(row_string, '---- this is the row string')
        
    except Exception as e:
        error_string = '%s | error in get_row_string %s'%(e, str(datetime.datetime.now()))
        logging.error(error_string)
        
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
    
def send_ome_alerts_of_user(user):
    try:
        """Get OME alerts of user (firstname.lastname) - execute SOLR search and send results as email"""
        
        #user = 'julia.gray'
        
        user_alerts, user_alert_ids = get_documents.get_ome_alerts_of_user(user)
        
        from_date = datetime.date.today() - datetime.timedelta(days=1)
        #from_date = datetime.date(2019,2,3)
        to_date = datetime.date.today()
        #to_date = datetime.date(2019,3,25)
        
        
        mail = 'not_initialized'
        
        for i in range(0, len(user_alert_ids)):
            if (user_alerts['email'][i] == 'yes'): #and (user_alerts['alert_type'][i] in ['standard', 'standard_title']):
                try:
                    search_params_list, keyword_title = get_documents.get_search_params_list(str(user_alert_ids[i]))
                    #print(search_params_list,'----- this is the search params list')
                    ome_alert_results, url_query = get_documents.get_ome_alert_results(search_params_list, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')
                    if len(ome_alert_results['path']) > 0:
                        email_address = user + '@roivant.com'
                        #email_address = 'julia.gray@roivant.com'
                        email_subject = 'OME alert: ' + keyword_title + ' (' + str(to_date) + ')'
                        table_string, summary_table_string = table_string_results(ome_alert_results, user)
                        email_string = "<html><head></head><body><h4>Summary (" + str(len(ome_alert_results['keyword'])) + " results)</h4>" + summary_table_string + "<br><br><h4>Documents</h4>" + table_string + "</body></html>"
                        #email_string = "<html><head></head><body><h4>Testing email</h4></body></html>"
                        print(email_address)
                        print(email_subject)
                        #print(email_string)
                        
                        
                    
                        if mail != 'not_initialized':
                            mail.sendEmail(email_address, email_subject, email_string)
                        else:
                            mail = Outlook()
                            mail.login('comp.res@roivant.com','Roivant$cr0819!')
                            mail.inbox()
                            mail.sendEmail(email_address, email_subject, email_string)
                            #print(undefined_variable)
                    else:
                        print('empty email')
                except: 
                    id_failure = 'OME Alert failure at {}'.format(user_alert_ids[i])
                    error_string = '%s | error in send_ome_alerts_of_user() %s' %(id_failure, str(datetime.datetime.now()))
                    logging.error(error_string)
                    continue
    except Exception as e:
        error_string = '%s | error in send_ome_alerts_of_user() %s', (e, str(datetime.datetime.now()))
        logging.error(error_string)
    
    return user_alert_ids

def send_ome_alerts():
    try:
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
    
    except Exception as e:
        error_string = '%s | error in send_ome_alerts %s' %(e, str(datetime.datetime.now()))
        logging.error(error_string)
        
    
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
#print('email_sent')


# DEBUGGING FUNCTIONS --------------
#from_date = datetime.date(2019,2,3)
#from_date = datetime.date.today() - datetime.timedelta(days=1)
#to_date = datetime.date(2019,3,25)
#to_date = datetime.date.today()


#test_search_params, test_alert_title = get_documents.get_search_params_list('39')
#test_url = construct_solr_search_url(test_search_terms, from_date=from_date)

#test_search_params = [{'alert_title':'TEST - SCA - all sources', 'keyphrase1':'blood', 'search_type':'standard', 'source_select':'PubMed_abstracts, PMC_text', 'filter_type':'' ,'journal_select':'', 'author_select': 'Zheng_L', 'institution_select':'shengjing hospital', 'filter_leeway':'70', 'keyword':'blood'}]
#ome_alert_results, url_query = get_documents.get_ome_alert_results(test_search_params, from_date=from_date, to_date=to_date, tags='tagged_entities_for_email')

#------------------------------------

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
#mail.login('comp.res@roivant.com','Roivant$cr0218!')
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
