import email
import imaplib
import smtplib
import datetime
import email.mime.multipart
import config_email
import requests
import numpy as np

import time
import base64

import nltk
import string

import re
import pandas as pd

from pandas import DataFrame
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.dialects.mysql import INTEGER
import MySQLdb
from collections import defaultdict

from tkinter import *           # Import the Tkinter library

import pickle

from bs4 import BeautifulSoup

from email.header import decode_header

from google import google
from google.modules.utils import _get_search_url, get_html, get_pdf, get_pdf_summary
from google.modules.standard_search import _get_link

from selenium import webdriver                        
from time import sleep    

import MySQLdb as my

from time import mktime
import datetime
from datetime import date

import pickle

path2 = '//ROIAWS1CRSG01/roivant-compres-copy/computationalresearch/SC Working Directory/database_working_table/'
path1 = '//ROIAWS1CRSG01/roivant-compres-copy/computationalresearch/DataBase/data_tables_backup/ome_product/'
path3 = '//ROIAWS1CRSG01/roivant-compres-copy/computationalresearch/DataBase/data_tables_backup/ome_product/email/'
path4 = '//ROIAWS1CRSG01/roivant-compres-copy/computationalresearch/emails/'
timestamp = date.today().strftime("%Y-%m-%d")

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

#email alert
e_alert = DataFrame(columns = ['table_name','script_name','description','timestamp'])

class Outlook():
    def __init__(self):
        mydate = datetime.datetime.now()-datetime.timedelta(1)
        self.today = mydate.strftime("%d-%b-%Y")
        
        # self.imap = imaplib.IMAP4_SSL('imap-mail.outlook.com')
        # self.smtp = smtplib.SMTP('smtp-mail.outlook.com')

    def login(self, username, password):
        self.username = username
        self.password = password
        count = 0
        while True:
            count+=1
            if count>100:
                break
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
        count=0
        while True:
            try:
                self.smtp = smtplib.SMTP(config_email.smtp_server, config_email.smtp_port)
                self.smtp.ehlo()
                self.smtp.starttls()
                self.smtp.login(self.username, self.password)
                self.smtp.sendmail(self.username, recipient, content)
                print("   email replied")
            except Exception as e:
                print("   Sending email...")
                print('error ', e)
                time.sleep(2)
                count+=1
                if count > 30: #waited more than 1min
                    break
                continue
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
    
import os
    


#path='R:/Business Development/Computational Research/emails/streetaccount/'
#path='//rs-ny-nas/Roivant Sciences/Business Development/Computational Research/emails/streetaccount/'
#path_ipd='//rs-ny-nas/Roivant Sciences/Business Development/Computational Research/emails/ipd/'
#path_evercore='//rs-ny-nas/Roivant Sciences/Business Development/Computational Research/emails/evercore/'
path_dict = 'C:/email_download/'
#path_dict = 'U:/Yoann/Coding/Python/outlook/'




timestamp = date.today().strftime("%Y-%m-%d")



#ipd_drug_check_ls = [] #list of drug name that did not match and should be manually checked
#count_drug_name_found = 0
#    
##load dictionary
#with open (path_dict+'dict_ipdAlias_OmeName', 'rb') as fp:
#    dict_ipdAlias_OmeName = pickle.load(fp)
#
#ipd_drug_ls = []
#for key in dict_ipdAlias_OmeName:
#    ipd_drug_ls.append(key.lower())
#    
#ipd_drug_ls = set(ipd_drug_ls)
#ipd_drug_ls = list(ipd_drug_ls)

path_password='//ROIAWS1CRSG01/roivant-compres-copy/computationalresearch/emails/compres_password.txt'
password = open(path_password, encoding='utf-8').read()


mail = Outlook()
mail.login('comp.res@roivant.com',password)
mail.inbox()


#import quopri

#proxy_ip = 'http://198.24.172.140:3128'  
#proxy = {
#        "http": proxy_ip,
#    }    

d_update = {}
d_new={}
#save all unread mails
unread_mail_id_ls = mail.unreadIds()
total_email_read = 0 
for i,mail_id in enumerate(unread_mail_id_ls):
#    mail_id = b'23646'
#    if i>2:
#        break
    #mail_id = unread_mail_id_ls[0]
    
    msg = mail.getEmail(mail_id)
    print(mail_id, mail.mailfrom())
    #REMOVE IN PRODUCTION
#    msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
#    mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')

#    msg = mail.getEmail(mail_id)
#    email_text = msg.get_payload()
#    
#    sender = mail.mailfrom()
    
    #save all Bill's email
    
#    if "fda@go.fda.gov" in mail.mailfrom():
#       print('fda mail found') 
#       break 
#       if not os.path.exists(path4 +'FDA_email/'+timestamp+'/'):
#                os.makedirs(path4 +'FDA_email/'+timestamp+'/')
#       for part in msg.walk():
#            # each part is a either non-multipart, or another multipart message
#            # that contains further parts... Message is organized like a tree
#            if part.get_content_type() == 'text/html':
#            #print(part.get_payload()[:100])                
#                    soup = BeautifulSoup(part.get_payload(decode=True),'html.parser')   
#            link_l= soup.find_all('a',href = True)
#            for link in link_l:
#                url = link['href']
#                response = requests.get(url,verify=False)
##                r_url = url
#                if response.history:
#                    #print("Request was redirected")
#                    mime_link = response.history[-1]
#                else:
#                    continue
                
                
                
    if mail.mailfrom() == 'Bill McMahon <bill.mcmahon@roivant.com>':
        email_text = msg.get_payload()
        if 'GlobalData' in email_text:
            try:
                
                if not os.path.exists(path4 +'GBD_email/'+timestamp+'/'):
                    os.makedirs(path4 +'GBD_email/'+timestamp+'/')
                
                for part in msg.walk():
                    # each part is a either non-multipart, or another multipart message
                    # that contains further parts... Message is organized like a tree
                    if part.get_content_type() == 'text/html':
                    #print(part.get_payload()[:100])
    
                    
                        soup = BeautifulSoup(part.get_payload(decode=True),'html.parser')
                        with open(path4 +'GBD_email/'+timestamp+'/'+'GlobalData_'+mail_id.decode('ascii')+'_'+timestamp+'.html', 'w', encoding='utf-8') as f:  
            
                            f.write(str(soup))
                            f.close()
                            break
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','GlobalData email detected and saved','timestamp']
                e_alert = e_alert.reset_index(drop=True)
                
            except:
                print('cannot download email to the file')
                msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
                mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','GlobalData email detected but cannot save, marked to unread','timestamp']
                e_alert = e_alert.reset_index(drop=True)
                
                    
          
               
        
        elif 'Cortellis Regulatory Intelligence Weekly Alert' in mail.mailsubject():
            
            try:
        
                if not os.path.exists(path4+'cortellis/Reg_Intelligence/' +timestamp+'/'):
                    os.makedirs(path4+'cortellis/Reg_Intelligence/' +timestamp+'/')
                
                for part in  msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        # print part.as_string()
                        continue
                    if part.get('Content-Disposition') is None:
                        # print part.as_string()
                        continue
                    fileName = part.get_filename().replace('\r\n','')
        
                    if bool(fileName):
                        filePath = os.path.join(path4+'cortellis/Reg_Intelligence/' +timestamp+'/', fileName)
                        if not os.path.isfile(filePath) :
                            print(fileName)
                            fp = open(filePath, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                            
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','Cortellis Regulatory Intelligence email detected and saved','timestamp']
                e_alert = e_alert.reset_index(drop=True)
                            
            except:
                print('cannot download email to the file')
                msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
                mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','Cortellis Regulatory Intelligence email detected but cannot save, marked to unread','timestamp']
                e_alert = e_alert.reset_index(drop=True)
                                
        elif 'Portlet Results' in mail.mailsubject():
            
            try:
        
                if not os.path.exists(path4+'cortellis/Portlet_Results/' +timestamp+'/'):
                    os.makedirs(path4+'cortellis/Portlet_Results/' +timestamp+'/')
                
                for part in msg.walk():
                    # each part is a either non-multipart, or another multipart message
                    # that contains further parts... Message is organized like a tree
                    if part.get_content_type() == 'text/html':
                    #print(part.get_payload()[:100])
    
    
                        soup = BeautifulSoup(part.get_payload(decode=True),'html.parser')
                        with open(path4+'cortellis/Portlet_Results/' +timestamp+'/'+mail_id.decode('ascii')+'_'+timestamp+'.html', 'w', encoding='utf-8') as f:  
                            f.write(str(soup))
                            f.close()
                        break
                        
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','Portlet Results email detected and saved','timestamp']
                e_alert = e_alert.reset_index(drop=True)
                
            except:
                print('cannot download email to the file')
                msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
                mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')        
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','Portlet Results email detected but cannot save, marked to unread','timestamp']
                e_alert = e_alert.reset_index(drop=True)        
                                
        elif 'AdComm Advance' in mail.mailsubject():
            
            try:
        
                if not os.path.exists(path4+'cortellis/AdComm_Advance/' +timestamp+'/'):
                    os.makedirs(path4+'cortellis/AdComm_Advance/' +timestamp+'/')
                
                for part in  msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        # print part.as_string()
                        continue
                    if part.get('Content-Disposition') is None:
                        # print part.as_string()
                        continue
                    fileName = part.get_filename().replace('\r\n','')
        
                    if bool(fileName):
                        filePath = os.path.join(path4+'cortellis/AdComm_Advance/' +timestamp+'/', fileName)
                        if not os.path.isfile(filePath) :
                            print(fileName)
                            fp = open(filePath, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()   
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','AdComm Advance email detected and saved','timestamp']
                e_alert = e_alert.reset_index(drop=True)           
            except:
                print('cannot download email to the file')
                msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
                mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','AdComm Advance email detected but cannot save, marked to unread','timestamp']
                e_alert = e_alert.reset_index(drop=True)   
                            
                        
        #Cortellis Drug Updates
        elif 'Drug Status Changes alert' in mail.mailsubject():
            try:
                if not os.path.exists(path4+'cortellis/Drug_Status_Changes_alert/' +timestamp+'/'):
                    os.makedirs(path4+'cortellis/Drug_Status_Changes_alert/' +timestamp+'/')
                
                print('Reading mail...: ', mail_id)
                
                        #save the email
        
                
                
                total_email_read +=1
                
                
        
            
        #        print(email_text)
        #        msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
        #        mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
        #        break
                
                for part in msg.walk():
                    #print(part.get_content_type())
                    if part.get_content_type() == 'text/html':
                        try:
                            #print(part.get_payload()[:100])
                            soup = BeautifulSoup(part.get_payload(decode=True),'html.parser')
                            with open(path4+'cortellis/Drug_Status_Changes_alert/' +timestamp+'/Drug_Status_Changes_alert_'+mail_id.decode('ascii')+'_'+timestamp+'.html', 'w', encoding='utf-8') as f:
                                f.write(str(soup))
                                f.close()
                            aaa = str(soup)
                        except:
                            msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
                            mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
                            
                        break
                        
        #        if 'No reports were new to your results set in this time period' in aaa:
        #            continue
        #        else:
        #            break
                
                table = soup.find('table')
                tables = table.findAll('table')
                
                
                date_str=msg.get('date')[5:16].strip()
                t = time.strptime(date_str, '%d %b %Y')
                mail_date = datetime.datetime.fromtimestamp(mktime(t)).strftime("%Y-%m-%d")
                
                
                for t in tables:
                    if 'Drug Status Changes' in str(t) or 'SINCE LAST ALERT' in str(t)  or 'View in Cortellis' in str(t) :
                        continue
                    
                    
                    elif 'Event Type' not in str(t):
                        link = t.find('a',href = True)
                        if link == None:
                            continue
                        else:
                            drug = link.text
                            url = link['href']
                            response = requests.get(url,verify=False)
                            r_url = url
                            if response.history:
                                #print("Request was redirected")
                                for resp in response.history:
                    #                print(resp.status_code)
                    #                print(resp.url)
                                    if 'www.cortellis.com' in resp.url:
                                        r_url = resp.url
                                        break
                            else:
                                continue
                            d = []
                            trs = t.findAll('tr')
                            for tr in trs:
                                td = tr.findAll('td')
                                row = [tr.text for tr in td]
                                d.append(row[-1])
                            d_new[drug] = {}
                            d_new[drug]['info'] = d
                            d_new[drug]['link'] = r_url
                            d_new[drug]['mail_date'] = mail_date
                            try:
                                d_new[drug]['id']  = int(r_url.split('/')[-1])
                            except:
                                continue
                    
                    
                    else:
                        d = []
                        trs = t.findAll('tr')
                        for tr in trs:
                            td = tr.findAll('td')
                            row = [tr.text for tr in td]
                            if len(row) ==3:
        #                        try:
        #                            date =  time.strptime(row[0], '%d-%b-%Y')
        #                            row[0] = datetime.datetime.fromtimestamp(mktime(date)).strftime("%Y-%m-%d")
        #                        except:
        #                            continue
                                d.append(row)
                        
        
                        link = t.find('a',href = True)
                        drug = link.text
                        url = link['href']
                        r_url = url
                        response = requests.get(url,verify=False)
                        if response.history:
        #                    print("Request was redirected")
                            for resp in response.history:
                #                print(resp.status_code)
                #                print(resp.url)
                                if 'www.cortellis.com' in resp.url:
                                    r_url = resp.url
                                    break
                        else:
                            continue
                        data = DataFrame(d[1:], columns = d[0])
                        d_update[drug] = {}
                        d_update[drug]['link'] = r_url
                        d_update[drug]['df'] = data
                        d_update[drug]['mail_date'] = mail_date
                        try:
                            d_update[drug]['id']  = int(r_url.split('/')[-1])
                        except:
                            continue
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','Drug Status Changes alert detected, processed and saved','timestamp']
                e_alert = e_alert.reset_index(drop=True)  
            except:
                print('cannot download email to the file')
                msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
                mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
                e_alert.loc[-1]  = ['','cortellis_emial_etl.py','Drug Status Changes alert detected but cannot save/process, marked back to unread','timestamp']
                e_alert = e_alert.reset_index(drop=True)     
        #mark unread if not saved
        else:
            msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
            mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')
    #mark unread if not Bill's email            
    else:
        msg_uid = mail.imap.fetch(mail_id.decode('ascii'), 'UID')[1][0].decode('ascii').split()[2].strip('()')
        mail.imap.uid('STORE', msg_uid , '-FLAGS', '(\Seen)')

#return count of durg update emails
print('total email read: ',total_email_read)    
 


#np.save(path2+'d_new'+timestamp+'.npy', d_new)   





pickle_out = open(path3+'d_new'+timestamp+'.pkl',"wb")
pickle.dump(d_new, pickle_out)
pickle_out.close()

pickle_out = open(path3+'d_update'+timestamp+'.pkl',"wb")
pickle.dump(d_update, pickle_out)
pickle_out.close()
#

#pickle_in = open(path3+'d_new'+timestamp+'.pkl',"rb")
#d_new = pickle.load(pickle_in)
#pickle_in.close()
#
#pickle_in = open(path3+'d_update'+timestamp+'.pkl',"rb")
#d_update = pickle.load(pickle_in)
#pickle_in.close()

##########################################################################
#if pickle file not available but email saved, use the code below
###########################################################################

##change file name with the current date and email id saved
#email_saved_path = path4+'cortellis/Drug_Status_Changes_alert/' +timestamp+'/Drug_Status_Changes_alert_'+'44677_2019-09-16.html'
#import codecs
#f=codecs.open(email_saved_path, 'r')
#soup = BeautifulSoup(f,'html.parser')
#                           
#
#table = soup.find('table')
#tables = table.findAll('table')
#
#
#date_str=msg.get('date')[5:16].strip()
#t = time.strptime(date_str, '%d %b %Y')
#mail_date = datetime.datetime.fromtimestamp(mktime(t)).strftime("%Y-%m-%d")
#
#
#for t in tables:
#    if 'Drug Status Changes' in str(t) or 'SINCE LAST ALERT' in str(t)  or 'View in Cortellis' in str(t) :
#        continue
#    
#    
#    elif 'Event Type' not in str(t):
#        link = t.find('a',href = True)
#        if link == None:
#            continue
#        else:
#            drug = link.text
#            url = link['href']
#            response = requests.get(url,verify=False)
#            r_url = url
#            if response.history:
#                #print("Request was redirected")
#                for resp in response.history:
#    #                print(resp.status_code)
#    #                print(resp.url)
#                    if 'www.cortellis.com' in resp.url:
#                        r_url = resp.url
#                        break
#            else:
#                continue
#            d = []
#            trs = t.findAll('tr')
#            for tr in trs:
#                td = tr.findAll('td')
#                row = [tr.text for tr in td]
#                d.append(row[-1])
#            d_new[drug] = {}
#            d_new[drug]['info'] = d
#            d_new[drug]['link'] = r_url
#            d_new[drug]['mail_date'] = mail_date
#            try:
#                d_new[drug]['id']  = int(r_url.split('/')[-1])
#            except:
#                continue
#    
#    
#    else:
#        d = []
#        trs = t.findAll('tr')
#        for tr in trs:
#            td = tr.findAll('td')
#            row = [tr.text for tr in td]
#            if len(row) ==3:
##                        try:
##                            date =  time.strptime(row[0], '%d-%b-%Y')
##                            row[0] = datetime.datetime.fromtimestamp(mktime(date)).strftime("%Y-%m-%d")
##                        except:
##                            continue
#                d.append(row)
#        
#
#        link = t.find('a',href = True)
#        drug = link.text
#        url = link['href']
#        r_url = url
#        response = requests.get(url,verify=False)
#        if response.history:
##                    print("Request was redirected")
#            for resp in response.history:
##                print(resp.status_code)
##                print(resp.url)
#                if 'www.cortellis.com' in resp.url:
#                    r_url = resp.url
#                    break
#        else:
#            continue
#        data = DataFrame(d[1:], columns = d[0])
#        d_update[drug] = {}
#        d_update[drug]['link'] = r_url
#        d_update[drug]['df'] = data
#        d_update[drug]['mail_date'] = mail_date
#        try:
#            d_update[drug]['id']  = int(r_url.split('/')[-1])
#        except:
#            continue
#                        
                        
    
def db_conn(schemaname):
    host = '10.115.1.196'
    db_name = schemaname
    username = 'sicong'
    password = 'Roivant1'
    conn=my.connect(user=username, password=password ,
                                  host=host,
                                  database=db_name)
    
    
    #create engine to output file
    enginename = "mysql+mysqldb://sicong:Roivant1@10.115.1.196/"+schemaname+"?charset=utf8"
    engine = create_engine(enginename,encoding='utf-8')
    
    return conn, engine


#connect to db
schema_name = 'ome_star_schema'
conn, engine = db_conn(schema_name)
cur = conn.cursor()


sqlstring1 = """
SELECT * FROM ome_star_schema.ome_product_aliases 
"""
cur.execute(sqlstring1)
colnames = [desc[0] for desc in cur.description]
d_ome_names_raw = cur.fetchall()
product_mysql = DataFrame(data = list(d_ome_names_raw), columns = colnames)


sqlstring1 = """
SELECT * FROM ome_star_schema.product_company 
"""
cur.execute(sqlstring1)
colnames = [desc[0] for desc in cur.description]
d_ome_names_raw = cur.fetchall()
company_mysql = DataFrame(data = list(d_ome_names_raw), columns = colnames)


sqlstring1 = """
SELECT * FROM ome_star_schema.product_status_history 
"""
cur.execute(sqlstring1)
colnames = [desc[0] for desc in cur.description]
d_ome_names_raw = cur.fetchall()
status_mysql = DataFrame(data = list(d_ome_names_raw), columns = colnames)


sqlstring1 = """
SELECT * FROM ome_star_schema.product_highest_status
"""
cur.execute(sqlstring1)
colnames = [desc[0] for desc in cur.description]
d_ome_names_raw = cur.fetchall()
highest_status_mysql = DataFrame(data = list(d_ome_names_raw), columns = colnames)


sqlstring1 = """
SELECT * from ome_company_aliases 

"""
cur.execute(sqlstring1)
colnames = [desc[0] for desc in cur.description]
d_ome_names_raw = cur.fetchall()
ome_company = DataFrame(data = list(d_ome_names_raw), columns = colnames)



conn.close()


product_mysql.to_csv(path1+'ome_product_aliases'+timestamp+'.csv')
company_mysql.to_csv(path1+'product_company'+timestamp+'.csv')
status_mysql.to_csv(path1+'product_status_history'+timestamp+'.csv')
highest_status_mysql.to_csv(path1+'product_highest_status'+timestamp+'.csv')

#ome_company_dictionary
d_company= {}


for i,row in ome_company.iterrows():
    d_company[row['alias'].lower()] = row['ome_company_id']



product_mysql['Drug Id'] = ''
for i,row in product_mysql.iterrows():
    try:
        product_mysql.at[i,'Drug Id']= int(row['source'].replace('cortellis - ',''))
    except:
        continue
    
company_mysql['Drug Id'] = ''
for i,row in company_mysql.iterrows():
    try:
        company_mysql.at[i,'Drug Id']= int(row['source'].replace('cortellis - ',''))    
    except:
        continue

d_id = {}
for i,row in product_mysql.iterrows():
    if row['Drug Id']!='':
        did = row['Drug Id']
        pid = row['OME_Product_id']
        d_id[did] = pid
    

#seperate status, company and drug naame update
df_update_drug = DataFrame(columns = ['Drug Id','product_name','date'])    
  
df_update_highest_status = DataFrame(columns = ['Drug Id','status','date'])
df_update_status = DataFrame(columns = ['Drug Id','status','territory','company','indication','date'])


    
#df_update = DataFrame(columns = ['Drug Id','product_name','active_company','inactive_company','date'])
for x in d_update.keys():
    if 'DELETED' not in x:
        try:
            df = d_update[x]['df']
            id = d_update[x]['id']
        
        
            for i,row in df.iterrows():
                date =  time.strptime(row['Date'], '%d-%b-%Y')
                date = datetime.datetime.fromtimestamp(mktime(date)).strftime("%Y-%m-%d")
                if row['Event Type'] == 'Drug name changed':
                    new_name = row['Description'].split(' to ')[1]
                    temp = DataFrame([[id,new_name,date]], columns =['Drug Id','product_name','date'])
                    df_update_drug = df_update_drug.append(temp)
                    
                elif row['Event Type'] == 'Highest status change':
                    status = row['Description'].split(' to ')[1]
                    temp = DataFrame([[id,status,date]], columns =['Drug Id','status','date'])
                    df_update_highest_status = df_update_highest_status.append(temp)
                    
                elif row['Event Type'] == 'Development status: company/indication/territory trio added'  or row['Event Type'] =='Development status: company/indication/territory trio status change':
                    try:
                        trio = row['Description'].split(' to ')[1].split(',')
                    except:
                        trio = row['Description'].split(',')
                    status = trio[0].strip()
                    t = trio[1].strip()
                    c = trio[2].replace('[','').replace(']','').strip()
                    ind = trio[3].strip()
                    d = trio[4].strip()
                    try:
                        d=  time.strptime(d, '%d-%b-%y')
                        d = datetime.datetime.fromtimestamp(mktime(d)).strftime("%Y-%m-%d")
                    except:
                        continue
                    temp = DataFrame([[id,status,t,c,ind,d]], columns =['Drug Id','status','territory','company','indication','date'])
                    df_update_status = df_update_status.append(temp)
        except:
            continue


df_update_status = df_update_status.sort_values('date')

                
df_update_drug.drop_duplicates(inplace = True)
df_update_drug.reset_index(drop = True, inplace = True)

df_update_status.drop_duplicates(inplace = True)
df_update_status.reset_index(drop = True, inplace = True)

df_update_highest_status.drop_duplicates(inplace = True)
df_update_highest_status.reset_index(drop = True, inplace = True)





#df_update.to_csv(path2+'cortellis_email_update_'+timestamp+'.csv')
        
df_new = DataFrame(columns = ['Drug Id','product_name','company','date'])   
df_new_status = DataFrame(columns = ['Drug Id','status','company','indication','date'])                                 
for x in d_new.keys():
    info = d_new[x]['info']
    id = d_new[x]['id']
    date = d_new[x]['mail_date']
    info = info[1:]
    c_list = []
    for i in info:
        c = i.split(' by ')[1].split(' for ')[0].strip()
        c_list.append(c)
    for i in info:
        s = i.split(' by ')[0].strip()
        sc = i.split(' by ')[1].split(' for ')[0].strip()
        ind = i.split(' for ')[1].strip()
        temp = DataFrame([[id,s,sc,ind,date]], columns = ['Drug Id','status','company','indication','date'])
        df_new_status = df_new_status.append(temp)
    c_list = set(c_list)
    c_list = list(c_list)
    temp = DataFrame([[id,x,c_list,date]], columns = ['Drug Id','product_name','company','date'])
    df_new = df_new.append(temp)


df_new_status.drop_duplicates(inplace = True)



#
#df_update_drug.to_csv(path2+'cortellis_email_new_'+timestamp+'.csv')

#df_new.drop_duplicates(inplace = True)
df_new.reset_index(drop = True, inplace = True)

df_new['name'] =''
df_new['primary'] = ''
df_new['other'] = ''
for i,row in df_new.iterrows():
    p_name = row['product_name'].replace('\r\n','')
    c_list = row['company'].copy()
    if '(' in p_name:
        name = p_name.split('(')[0].strip()

        if ',' in p_name.split(')')[-1]:
            c = p_name.split(')')[-1].split(', ')[1].split('/')[0].strip()
            for x in c_list:
                if c.lower() in x.lower(): 
                    pc = x
                    break
                else: pc = c_list[0]
        else:
            pc = c_list[0]
    elif  ',' in p_name:
        c = p_name.split(',')[1].split('/')[0].strip()
        for x in c_list:
                if c.lower() in x.lower(): 
                    pc = x
                    break
                else: pc = c_list[0]
        name = p_name.split(',')[0]
    else:
        name = p_name
        pc = c_list[0]

    c_list.remove(pc)
    
    df_new.at[i,'name'] = name
    df_new.at[i,'primary'] =pc
    df_new.at[i,'other'] ='; '.join(c_list)
    
    
#####################################################################
#####################################################################
#add new info to product tables in the databae
#####################################################################
#####################################################################
    
    
#assign ome product id
df_new['exist'] = ''
df_new['source'] = ''

for i,row in df_new.iterrows():
    if row['Drug Id'] not in d_id.keys():
        df_new.at[i,'source'] = 'cortellis - '+str(row['Drug Id'])
    else:
        df_new.at[i,'exist']= d_id[row['Drug Id']]
        
df_new = df_new[df_new['source']!='']    
df_new.reset_index(drop = True,inplace = True)
    
num_p = max(product_mysql['OME_Product_id'])    
df_new.reset_index(drop = True, inplace = True)
df_new.index += num_p+1
df_new.reset_index(inplace = True)

df_new.columns = ['OME_Product_id','Drug Id', 'product_name', 'company', 'date', 'name', 'primary', 'other', 'exist', 'source']
d_new_id ={}
for i,row in df_new.iterrows():
    d_new_id[row['Drug Id']]=row['OME_Product_id']
    
#ome product aliases
    


product_aliases_new = df_new.loc[:,['OME_Product_id','Drug Id', 'name', 'source']].copy()


product_aliases_new['Aliases'] = product_aliases_new ['name'] 

product_aliases_new['updated_at'] = timestamp

product_aliases_new.reset_index(drop = True, inplace = True)

        
del product_aliases_new['Drug Id']

product_aliases_new.columns = ['OME_Product_id','Product_Name','source', 'Aliases', 'updated_at']

product_aliases_new.reset_index(drop = True, inplace = True)

num_id = max(product_mysql['ome_product_aliases_id'])
product_aliases_new.index+=num_id+1


#product_status_history

df_new_status['source'] = ''
df_new_status['territory'] = ''
df_new_status['OME_Product_id'] = ''

df_new_status.reset_index(drop = True, inplace = True)

for i,row in df_new_status.iterrows():
    if row['Drug Id'] not in d_id.keys():
        df_new_status.at[i,'source'] = 'cortellis - '+str(row['Drug Id'])
        df_new_status.at[i,'OME_Product_id'] = d_new_id[row['Drug Id']]
  
df_new_status =   df_new_status[df_new_status['source']!=''] 
  
product_status_history_new = df_new_status.loc[:,['OME_Product_id', 'company', 'territory','status','indication', 'date', 'source']].copy()
  
product_status_history_new['updated_at'] = timestamp

numrow = max(status_mysql['product_status_history_id'])
product_status_history_new.index +=1

#product_highest_status
product_highest_status_new = df_new_status.loc[:,['OME_Product_id', 'status', 'date', 'source']].copy().sort_values('date')
product_highest_status_new  = product_highest_status_new.drop_duplicates('OME_Product_id','last')

num_id = max(highest_status_mysql['product_highest_status_id'])

product_highest_status_new.reset_index(drop = True, inplace = True)
product_highest_status_new.index += num_id+1
#product_company_new

product_company_new   = df_new.loc[:,['OME_Product_id','name', 'primary', 'other', 'source']].copy()

  
product_company_new.columns =   ['OME_Product_id','Product_Name', 'primary_company', 'other_companies', 'source']
 
product_company_new['updated_at'] = timestamp


product_company_new['primary_ome_company_id'] = ''
product_company_new['other_ome_company_id'] = ''
not_found = []



for i,row in product_company_new.iterrows():
    p = row['primary_company']
    
    try:
        product_company_new.at[i,'primary_ome_company_id'] = d_company[p.lower().strip()]
    except:
        not_found.append(p)
        continue
    
for i,row in product_company_new.iterrows():  
    if row['other_companies']!='':
        o = row['other_companies'].split('; ')
        ol = []
        for c in o:
            try:
                ol.append(d_company[c.lower().strip()])
            except:
                not_found.append(c)
                continue
        ol = set(ol)
        ol = list(ol)
  
        
        product_company_new.at[i,'other_ome_company_id'] = ol









#####################################################################
#####################################################################
# update product tables in the databae
#####################################################################
#####################################################################


#######ome product aliases #####################################
df_update_drug['Product_Name'] = ''


for i,row in df_update_drug.iterrows():
    p_name = row['product_name'].replace('\r\n','')
    if '(' in p_name:
        name = p_name.split('(')[0].strip()

    elif  ',' in p_name:
        
        name = p_name.split(',')[0]
    else:
        name = p_name
    
    df_update_drug.at[i,'Product_Name'] = name
    
    
df_update_drug.sort_values('date',inplace = True)
df_update_drug.reset_index(drop = True, inplace = True)


df_update_drug['OME_Product_id'] =''
df_update_drug['source'] =''
df_update_drug['update_name'] =''
df_update_drug['add_alias'] =''


for i,row in df_update_drug.iterrows():
    df_update_drug.at[i,'source'] = 'cortellis - '+str(row['Drug Id'])
    
    if row['Drug Id'] in d_id.keys():
        df_update_drug.at[i,'OME_Product_id'] = d_id[row['Drug Id']]
        temp = product_mysql[product_mysql['OME_Product_id']==d_id[row['Drug Id']]]
        p_name = row['Product_Name']
        
        if p_name != temp['Product_Name'].tolist()[0]:
            df_update_drug.at[i,'update_name'] = 'Y'
        if p_name not in temp['Aliases'].tolist():
            df_update_drug.at[i,'add_alias'] = 'Y'
    
    elif row['Drug Id'] in d_new_id.keys():
        df_update_drug.at[i,'OME_Product_id'] = d_new_id[row['Drug Id']]
        temp = product_aliases_new[product_aliases_new['OME_Product_id']==d_new_id[row['Drug Id']]]
        p_name = row['Product_Name']
        
        if p_name != temp['Product_Name'].tolist()[0]:
            df_update_drug.at[i,'update_name'] = 'Y'
        if p_name not in temp['Aliases'].tolist():
            df_update_drug.at[i,'add_alias'] = 'Y'

#add new drug to product_aliases_new
new_drug_from_update = df_update_drug[df_update_drug['OME_Product_id']=='']
new_drug_from_update.drop_duplicates('Drug Id')
new_drug_from_update.reset_index(drop = True, inplace = True)

d_new_new = {}

try:
    ome_id_num = max(product_aliases_new['OME_Product_id'])
except:
    ome_id_num = max(product_mysql['OME_Product_id'])
    
for i,row in new_drug_from_update.iterrows():
    ome_id_num +=1
    new_drug_from_update.at[i,'OME_Product_id'] =ome_id_num
    d_new_new[row['Drug Id']] = ome_id_num

new_drug_from_update =new_drug_from_update.loc[:,['OME_Product_id', 'Product_Name', 'source']]

new_drug_from_update['Aliases'] =new_drug_from_update ['Product_Name']
new_drug_from_update['updated_at'] = timestamp


product_aliases_new = product_aliases_new.append(new_drug_from_update)  


# add new alias to product_aliases_new
new_alias_from_update = df_update_drug[df_update_drug['add_alias']=='Y']
new_alias_from_update.drop_duplicates('Drug Id')
new_alias_from_update.reset_index(drop = True, inplace = True)

new_alias_from_update =  new_alias_from_update.loc[:,['OME_Product_id', 'Product_Name', 'source']]
new_alias_from_update['Aliases'] =new_alias_from_update ['Product_Name']
new_alias_from_update['updated_at'] = timestamp

product_aliases_new = product_aliases_new.append(new_alias_from_update) 


############## product_company #################################

df_update_company = DataFrame(columns = ['Drug Id','primary_company','other_companies','date'])  


drug_id = df_update_status['Drug Id'].drop_duplicates().tolist()

for x in drug_id:
    temp = df_update_status[df_update_status['Drug Id']==x]
    if 'US' in temp['territory'].tolist():
        temp = temp[temp['territory'] =='US']
    c = temp['company'].tolist()[-1]
    d = temp['date'].tolist()[-1]
    oc = temp['company'].tolist()
    oc = set(oc)
    oc = list(oc)
    oc.remove(c)
#    oc = ('; ').join(oc)
    cc = DataFrame([[x,c,oc,d]], columns =['Drug Id','primary_company','other_companies','date'])
    df_update_company= df_update_company.append(cc)
    

#df_update_company.drop_duplicates(inplace = True)
df_update_company.reset_index(drop = True, inplace = True)

df_update_company['OME_Product_id'] =''
df_update_company['update'] =''
df_update_company['new'] =''
df_update_company['pc'] =''
df_update_company['oc'] =''

for i,row in df_update_company.iterrows():

    di = row['Drug Id']
    date = datetime.datetime.strptime(row['date'], "%Y-%m-%d").date()
    #case 1: drug in database
    if di in d_id.keys():
        df_update_company.at[i,'OME_Product_id'] = d_id[di]
        temp = company_mysql[company_mysql['OME_Product_id'] == d_id[di]]
        #check if status updated after the last update in our database
        if date>= temp['updated_at'].tolist()[-1]:
            #check if primary matches
            #only if type = cortellis
            db_pc = temp['primary_company'].tolist()[-1]
            if row['primary_company'] != db_pc:
                df_update_company.at[i,'update'] =  'Y'
                df_update_company.at[i,'pc'] = row['primary_company']
                #check if all other companies in database
                db_oc = temp['other_companies'].tolist()[-1].split('; ')
                new_oc = db_oc
                if row['primary_company'] in new_oc:
                    new_oc.remove(row['primary_company'])

                new_oc.append(db_pc)
     
                if row['other_companies']!= []:
                    for c in row['other_companies']:
                        if c not in new_oc:
                            new_oc.append(c)
                if '' in new_oc:
                    new_oc.remove('')
                df_update_company.at[i,'oc'] = new_oc
            else:
                db_oc = temp['other_companies'].tolist()[0].split('; ')
                new_oc = db_oc
                if row['other_companies']!= []:
                    for c in row['other_companies']:
                        if c not in db_oc:
                            df_update_company.at[i,'update'] =  'Y'
                            new_oc.append(c)
                if row['update'] == 'Y':
                    df_update_company.at[i,'pc'] = row['primary_company']
                    if '' in new_oc:
                        new_oc.remove('')
                    df_update_company.at[i,'oc'] = new_oc
                    
    #case 2: drug in new drug                
    elif di in d_new_id.keys():
        df_update_company.at[i,'OME_Product_id'] = d_new_id[di]
        temp = product_company_new[product_company_new['OME_Product_id'] == d_new_id[di]]
        if row['date']>= temp['updated_at'].tolist()[-1]:
            #check if primary matches
            db_pc = temp['primary_company'].tolist()[0]
            if row['primary_company'] != db_pc:
                df_update_company.at[i,'update'] =  'Y'
                df_update_company.at[i,'pc'] = row['primary_company']
                #check if all other companies in database
                db_oc = temp['other_companies'].tolist()[0].split('; ')
                if row['primary_company'] in new_oc:
                    db_oc.remove(row['primary_company'])
                
                new_oc = db_oc
                new_oc.append(db_pc)
                if row['other_companies']!= []:
                    for c in row['other_companies']:
                        if c not in new_oc:

                            new_oc.append(c)
                if '' in new_oc:
                    new_oc.remove('')

                df_update_company.at[i,'oc'] = new_oc
            else:
                db_oc = temp['other_companies'].tolist()[0].split('; ')
                new_oc = db_oc
                if row['other_companies']!= []:
                    for c in row['other_companies']:
                        if c not in db_oc:
                            df_update_company.at[i,'update'] =  'Y'
                            new_oc.append(c)
                if row['update'] == 'Y':
                    df_update_company.at[i,'pc'] = row['primary_company']
                    if '' in new_oc:
                        new_oc.remove('')
                    df_update_company.at[i,'oc'] = new_oc
#    case 3: drug in status only                
    elif di in d_new_new.keys():
        df_update_company.at[i,'OME_Product_id'] = d_new_new[di]
        df_update_company.at[i,'new'] =  'Y'
        
df_update_company['primary_ome_company_id'] = ''
df_update_company['other_ome_company_id'] = ''



for i,row in df_update_company.iterrows():
    p = row['pc']
    
    try:
        df_update_company.at[i,'primary_ome_company_id'] = d_company[p.lower().strip()]
    except:
        not_found.append(p)
        continue
    
for i,row in  df_update_company.iterrows():  
    if row['oc']!='':
        o = row['oc']
        ol = []
        for c in o:
            try:
                ol.append(d_company[c.lower().strip()])
            except:
                not_found.append(c)
                continue
        ol = set(ol)
        ol = list(ol)
  
        
        df_update_company.at[i,'other_ome_company_id'] = ol        
        
        
#check new during etl
df_update_company_new = df_update_company[df_update_company['new']=='Y'].copy()
for i,row in df_update_company_new.iterrows():
    oc = row['other_companies']
    oc_str = ('; ').join(oc)
    df_update_company_new.at[i,'other_companies'] = oc_str
    df_update_company_new.at[i,'source'] = 'cortellis - '+str(row['Drug Id'])
    
df_update_company_new = df_update_company_new.loc[:,['OME_Product_id','primary_company', 'other_companies','source']]



df_update_company_new['primary_ome_company_id'] = ''
df_update_company_new['other_ome_company_id'] = ''



for i,row in df_update_company_new.iterrows():
    p = row['primary_company']
    
    try:
        df_update_company_new.at[i,'primary_ome_company_id'] = d_company[p.lower().strip()]
    except:
        not_found.append(p)
        continue
    
for i,row in  df_update_company_new.iterrows():  
    if row['other_companies']!='':
        o = row['other_companies']
        ol = []
        for c in o:
            try:
                ol.append(d_company[c.lower().strip()])
            except:
                not_found.append(c)
                continue
        ol = set(ol)
        ol = list(ol)
  
        
        df_update_company_new.at[i,'other_ome_company_id'] = ol



#####apply primary company select, if smart/fda/ct, keep original primary company
#dictionary for primary company type in smart/fda/ct, save primary company        
d_primary_company = {}     
for i,row in company_mysql.iterrows():
    if row['primary_company_type'] in ('FDA','CT','SMART'):
        pcid = row['primary_ome_company_id']
        d_primary_company[row['OME_Product_id']] = pcid    

#dictionary of company_id -> company name
d_cid = {}
for i,row in ome_company.iterrows():
    d_cid[row['ome_company_id']] = row['ome_company']



for i,row in df_update_company.iterrows():
    if row['update'] == 'Y' and row['pc']!= row['primary_company']:
        if row['other_ome_company_id']!='':
           c_list = row['other_ome_company_id'].copy()
           c_list = c_list.append(row['primary_ome_company_id'])
        else:
           c_list = [row['primary_ome_company_id']]
    
        if row['OME_Product_id'] in d_primary_company:
            oldp = d_primary_company[row['OME_Product_id']]
            df_update_company.at[i,'primary_ome_company_id'] = oldp
            df_update_company.at[i,'pc'] = d_cid[oldp]
            c_list.remove(oldp)
            
            if len(c_list)>0:
                c_list = set(c_list)
                c_list = list(c_list)
        
                c_name_list = [d_cid[x] for x in c_list]
                #do not change order here, int in d_id, c_list then set to string
                c_list = [str(x) for x in  c_list]
                df_update_company.at[i,'other_ome_company_id'] = c_list
                df_update_company.at[i,'oc'] = c_name_list
            
                
 
################new companies to dictionary##############################
        

not_found = set(not_found)
not_found = list(not_found)

if '' in not_found:
    not_found.remove('')




new_company = pd.DataFrame(not_found, columns=['ome_company'])
new_company['alias'] = new_company['ome_company']

new_company['ticker'] = np.nan
new_company['source'] = 'Cortellis - ETL'
new_company['updated_at'] = timestamp

num_ome = max(ome_company['ome_company_id'])
num_a = max(ome_company['ome_company_aliases_id'])

new_company.index += num_ome+1
new_company.reset_index(inplace = True)

new_company.index += num_a+1
new_company.reset_index(inplace = True)


new_company.columns = ['ome_company_aliases_id', 'ome_company_id', 'ome_company', 'alias', 'ticker', 'source','updated_at']


for i,row in new_company.iterrows():
    d_company[row['alias'].lower()] = row['ome_company_id']
    
#add new ome id
for i,row in df_update_company.iterrows():
    p = row['pc']
    
    try:
        df_update_company.at[i,'primary_ome_company_id'] = d_company[p.lower().strip()]
    except:
        not_found.append(p)
        continue
    
for i,row in  df_update_company.iterrows():  
    if row['oc']!='':
        o = row['oc']
        ol = []
        for c in o:
            try:
                ol.append(d_company[c.lower().strip()])
            except:
                not_found.append(c)
                continue
        ol = set(ol)
        ol = list(ol)
  
        
        df_update_company.at[i,'other_ome_company_id'] = '; '.join( str(x) for x in ol)  
        

for i,row in df_update_company.iterrows():
    oc = row['oc']
    oc = ('; ').join(oc)
    df_update_company.at[i,'oc'] =oc


for i,row in product_company_new.iterrows():
    p = row['primary_company']
    
    try:
        product_company_new.at[i,'primary_ome_company_id'] = d_company[p.lower().strip()]
    except:
        not_found.append(p)
        continue
    
for i,row in product_company_new.iterrows():  
    if row['other_companies']!='':
        o = row['other_companies'].split('; ')
        ol = []
        for c in o:
            try:
                ol.append(d_company[c.lower().strip()])
            except:
                not_found.append(c)
                continue
        ol = set(ol)
        ol = list(ol)
  
        
        product_company_new.at[i,'other_ome_company_id'] = '; '.join( str(x) for x in ol)


product_company_new['primary_company_type'] ='Cortellis'


################ product_status_history ##############################


status_compare = status_mysql.loc[:,['OME_Product_id', 'company', 'territory', 'status', 'indication', 'date']].copy()
status_compare['date'] = status_compare['date'].astype(str)
status_compare['OME_Product_id'] = status_compare['OME_Product_id'].astype(int)

df_update_status['OME_Product_id'] = ''
df_update_status['source'] = ''

for i,row in df_update_status.iterrows():
    di = row['Drug Id']
    df_update_status.at[i,'source'] = 'cortellis - '+str(row['Drug Id'])
    if di in d_id.keys():
        df_update_status.at[i,'OME_Product_id'] = d_id[di]
    elif di in d_new_id.keys():
        df_update_status.at[i,'OME_Product_id'] = d_new_id[di]

df_update_status = df_update_status[df_update_status['OME_Product_id']!='']
df_update_status['OME_Product_id'] = df_update_status['OME_Product_id'].astype(int)


del df_update_status['Drug Id']

df_update_status_new = pd.merge(df_update_status,status_compare,indicator=True, how='left').query('_merge=="left_only"').drop('_merge', axis=1)
df_update_status_new['updated_at'] = timestamp

#add to product_status_history_new
product_status_history_new = product_status_history_new.append(df_update_status_new)


###############################product_highest_status#########################
df_update_highest_status['OME_Product_id'] =''
df_update_highest_status['update'] =''
for i,row in df_update_highest_status.iterrows():
    di = row['Drug Id']
    if di in d_id.keys():
        df_update_highest_status.at[i,'OME_Product_id'] = d_id[di]
        temp = highest_status_mysql[highest_status_mysql['OME_Product_id']==d_id[di]]
        date = datetime.datetime.strptime(row['date'], "%Y-%m-%d").date()
        if date>= temp['updated_at'].tolist()[-1]:
           df_update_highest_status.at[i,'update'] = 'Y'
    
    elif di in d_new_id.keys():
        df_update_highest_status.at[i,'OME_Product_id'] = d_new_id[di]
        temp = product_highest_status_new[product_highest_status_new['OME_Product_id']==d_new_id[di]]
        date = datetime.datetime.strptime(row['date'], "%Y-%m-%d").date()
        if date>= datetime.datetime.strptime(temp['date'].tolist()[-1], "%Y-%m-%d").date():
           df_update_highest_status.at[i,'update'] = 'Y'
    

###############################################################################
#                       update in db
###############################################################################

#email alert
e_alert = DataFrame(columns = ['table_name','script_name','description','timestamp'])
################################### append new ##################################

#create metadata info
meta_updates = DataFrame(columns = ['table_name','script_name','description','local_file','updated_at'])

#connect to db
schema_name = 'ome_star_schema'
conn, engine = db_conn(schema_name)
cur = conn.cursor()

#company aliases
new_company.to_sql('ome_company_aliases', engine, if_exists='append',index = False)
meta_updates.loc[-1] = ['ome_company_aliases','cortellis_email_etl.py','append new','',timestamp]
meta_updates = meta_updates.reset_index(drop=True)


#product_aliases
product_aliases_new.reset_index(drop = True, inplace = True)

num_id = max(product_mysql['ome_product_aliases_id'])
product_aliases_new.index+=num_id+1


try:
    product_aliases_new.to_sql("ome_product_aliases", engine, if_exists='append',index_label = "ome_product_aliases_id")
    
    meta_updates.loc[-1] = ['ome_product_aliases','cortellis_email_etl.py','append new',path1+'ome_product_aliases'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['ome_product_aliases','cortellis_email_etl.py','successfully added new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)

except:
    print('fail to append product_aliases_new')
    e_alert.loc[-1]  = ['ome_product_aliases','cortellis_email_etl.py','cannot add new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)


#product_company

num_id = max(company_mysql['product_company_id'])

product_company_new['other_ome_company_id'] =  product_company_new['other_ome_company_id'].astype(str)
    
product_company_new.reset_index(drop = True, inplace = True)
product_company_new.index += num_id+1

try:
    product_company_new.to_sql("product_company", engine, if_exists='append',index_label = "product_company_id")
    
    meta_updates.loc[-1] = ['product_company','cortellis_email_etl.py','append new',path1+'product_company'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['product_company','cortellis_email_etl.py','successfully added new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)
    
except:
    print('fail to append product_company_new')
    e_alert.loc[-1]  = ['product_company','cortellis_email_etl.py','cannot add new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)

#product_highest_status_new


num_id = max(highest_status_mysql['product_highest_status_id'])

product_highest_status_new.reset_index(drop = True, inplace = True)
product_highest_status_new.index += num_id+1
product_highest_status_new.columns = ['OME_Product_id', 'highest_status', 'date', 'source']
product_highest_status_new = product_highest_status_new.loc[:,['OME_Product_id', 'highest_status']]
product_highest_status_new['updated_at'] = timestamp

try:
    product_highest_status_new.to_sql("product_highest_status", engine, if_exists='append',index_label = "product_highest_status_id")
      
    meta_updates.loc[-1] = ['product_highest_status','cortellis_email_etl.py','append new',path1+'product_highest_status'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['product_highest_status','cortellis_email_etl.py','successfully added new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)
    
except:
    print('fail to append product_highest_status_new')
    e_alert.loc[-1]  = ['product_highest_status','cortellis_email_etl.py','cannot add new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)


numrow = max(status_mysql['product_status_history_id'])
product_status_history_new.reset_index(drop = True, inplace = True)
product_status_history_new.index +=1


try:
    product_status_history_new.to_sql("product_status_history", engine, if_exists='append',index_label = "product_status_history_id")
    
    meta_updates.loc[-1] = ['product_status_history','cortellis_email_etl.py','append new',path1+'product_status_history'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['product_status_history','cortellis_email_etl.py','successfully added new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)

except:
    print('fail to append product_status_history_new')
    e_alert.loc[-1]  = ['product_status_history','cortellis_email_etl.py','cannot add new rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)

################################ update row by row ####################################

#product_aliases
try:    
    for i,row in df_update_drug.iterrows():
        if row['update_name'] == 'Y':
            id = row['OME_Product_id']
            name = row['Product_Name']
            sql = """ update `ome_product_aliases` set Product_Name = "%s", updated_at = '%s' where ome_product_id = %s """
            cur.execute(sql%(name , timestamp,id))
            conn.commit() 
            
    
    meta_updates.loc[-1] = ['ome_product_aliases','cortellis_email_etl.py','update rows',path1+'ome_product_aliases'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['ome_product_aliases','cortellis_email_etl.py','successfully updated rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)
except:
    print('fail to update product_aliases')
    e_alert.loc[-1]  = ['ome_product_aliases','cortellis_email_etl.py','cannot update rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)

#product_company
    

try:
    for i,row in df_update_company.iterrows():
        if row['update'] == 'Y':
            id = row['OME_Product_id']
            pc = row['pc']
            oc = row['oc']
            pcid = row['primary_ome_company_id']
            ocid = str(row['other_ome_company_id'])
            sql = """ update `product_company`
                set primary_company = "%s", other_companies = "%s",primary_ome_company_id = '%s',
                other_ome_company_id = '%s',updated_at = '%s'
                where ome_product_id = %s """
            cur.execute(sql%(pc,oc ,pcid,ocid ,timestamp,id))
            conn.commit() 
            
            
    meta_updates.loc[-1] = ['product_company','cortellis_email_etl.py','update rows',path1+'product_company'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['product_company','cortellis_email_etl.py','successfully updated rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)
except:
    print('fail to update product_company')        
    e_alert.loc[-1]  = ['product_company','cortellis_email_etl.py','cannot update rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)
#product_highest_status
    

    
try:        
    for i,row in df_update_highest_status.iterrows():
        if row['update'] == 'Y':
            id = row['OME_Product_id']
            s = row['status']
            sql = """ update `product_highest_status`
                set `highest_status` = "%s",updated_at = '%s'
                where ome_product_id = %s """
            cur.execute(sql%(s , timestamp,id))
            conn.commit() 
    
    meta_updates.loc[-1] = ['product_highest_status','cortellis_email_etl.py','update rows',path1+'product_highest_status'+timestamp+'.csv',timestamp]
    meta_updates = meta_updates.reset_index(drop=True)
    e_alert.loc[-1]  = ['product_highest_status','cortellis_email_etl.py','successfully updated rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)
except:
    print('fail to update product_highest_status')  
    e_alert.loc[-1]  = ['product_highest_status','cortellis_email_etl.py','cannot update rows','timestamp']
    e_alert = e_alert.reset_index(drop=True)                    
    

### update matadata info
#get row number for the studies in mysql
sql="""select count(*) from `metadata_info`"""
cur.execute(sql)
num_row = int(cur.fetchall()[0][0])
#assign index to studies_existing to match ct.gov_studies_id col
meta_updates.index += num_row +1
meta_updates.to_sql("metadata_info", engine, if_exists='append',index_label='metadata_info_id')

conn.close()





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
				print("   email sent")
			except Exception as exception:
				print(exception)
				print("   Sending email...")
				continue
			break


	def logout(self):
		return self.imap.logout()




#list of recipients
r = ['julia.gray@roivant.com', 'yoann.randriamihaja@roivant.com'] 
#convert df to html
html_table = e_alert.to_html()

#    table_string = "<table><thead><th>Heading</th></thead><tbody><tr><td>CELL</td></tr></tbody></table>"

mail = Outlook()
path_password='//ROIAWS1CRSG01/roivant-compres-copy/computationalresearch/emails/compres_password.txt'
password = open(path_password, encoding='utf-8').read()
mail.login('comp.res@roivant.com',password)

for name in r:
    email_address = name
    email_subject = 'ETL status - Cortellis Email ETL'
    email_string = ("<html><head></head><body>" +html_table)
    

    #mail.inbox()
    mail.sendEmail(email_address, email_subject, email_string)


        	
mail.logout()


