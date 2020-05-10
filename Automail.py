import bios
import time
import imapclient
import yagmail
import smtplib
import email.message
from datetime import date
from Automail import *
from plugins import *

# ---------------------------------------------------------------------------
class Automail:
  def __init__(self):
    self.debug = False
    self.myConfFile = ''
    self.myImapCli = None
    self.mySmtpCli = None
    self.myConf = {}

  # ---------------------------------------------------------------------------
  def load_conf_file(self,conf_file):
  # ---------------------------------------------------------------------------
    self.myConfFile = conf_file
    self.myConf = self.load_config(conf_file)

  # ---------------------------------------------------------------------------
  def set_debug(self,debug):
  # ---------------------------------------------------------------------------
    self.debug = debug

  # ---------------------------------------------------------------------------
  def imap_connect(self):
  # ---------------------------------------------------------------------------
    """
    Initialize IMAP connection
    """
    print("IMAP: Initializing ... ")
    self.myImapCli = imapclient.IMAPClient(self.myConf['imap']['server_domain'])
    c = self.myImapCli.login(self.myConf['imap']['server_user'], self.myConf['imap']['server_pass'])
    self.myImapCli.select_folder(self.myConf['imap']['server_folder_inbox'], readonly=True)
    print("IMAP: Done")

  # ---------------------------------------------------------------------------
  def disconnect(self):
  # ---------------------------------------------------------------------------
    self.myImapCli.logout()
    self.mySmtpCli.quit()

  # ---------------------------------------------------------------------------
  def smtp_connect(self):
  # ---------------------------------------------------------------------------
    """
    Initialize SMTP connection
    """
    print("SMTP: Initializing ...")
    self.mySmtpCli = smtplib.SMTP(self.myConf['smtp']['server_host'], self.myConf['smtp']['server_port'])
    self.mySmtpCli.ehlo()
    c = self.mySmtpCli.starttls()[0]  # The returned status code
    if c is not 220:
        raise Exception('STMP: Starting tls failed: ' + str(c))
    c = self.mySmtpCli.login(self.myConf['smtp']['server_user'], self.myConf['smtp']['server_pass'])[0]
    if c is not 235:
        raise Exception('SMTP: login failed: ' + str(c))
    print("SMTP: Done. ")

  # ---------------------------------------------------------------------------
  def get_msg_unread(self):
  # ---------------------------------------------------------------------------
    """
    Fetch unread emails
    """
    msgIds = self.myImapCli.search(['UNSEEN'])
    if not msgIds:
        return None
    else:
        print("Found %s unreads" % len(msgIds))
        return self.myImapCli.fetch(msgIds, ['BODY[]', 'FLAGS'])


  # ---------------------------------------------------------------------------
  def get_msg_test(self,fromDate):
  # ---------------------------------------------------------------------------
    """
    Fetch unread emails
    """
    # msgIds = myImapCli.search(['SUBJECT','#TEST','SINCE',date(2020,04,26)])
    msgIds = self.myImapCli.search(['SINCE',fromDate])
    if not msgIds:
        return None
    else:
        print("Found %s test messages" % len(msgIds))
        return self.myImapCli.fetch(msgIds, ['BODY[]', 'FLAGS'])

  # ---------------------------------------------------------------------------
  def send_msg(self, fromSender, receivers, subject, body_txt):
  # ---------------------------------------------------------------------------
    """
    Send email
    """
    receiver = receivers if type(receivers) is list else [receivers]
    if self.debug:
      print("Send:{} -> {}: ".format( fromSender, receiver, subject))
    msg = email.message.EmailMessage()
    msg["from"] = fromSender
    msg["to"] = receiver
    msg["Subject"] = subject
    msg.set_content(body_txt)

    try:
      # send_message(msg,fromSender,receiver,mail_options,rcpt_options)
      res = self.mySmtpCli.send_message(msg,fromSender,receiver)
      if self.debug:
        print("Send:returns {}".format(res))
#    except OSError:
#      print("Warning:OSError. Reconnecting smpt")
#      self.smtp_connect()
#    except smtplib.SMTPServerDisconnected:
#      print("Warning:smtplib.SMTPServerDisconnected. Reconnecting smtp")
#      self.smtp_connect()
    except Exception as e:
      print("Warning:Smtp {}".format(e))

  # -----------------------------------------------------------------------
  def main_loop( self, fromDate, func_msgParser ):
  # -----------------------------------------------------------------------
    myWait = self.myConf['automail']['poll_frequency']
    while True:  # Main loop
      try:
        msgs = self.get_msg_test(fromDate)
        if not msgs is None:
           for a in msgs.keys():
             if type(a) is not int:
                continue
             cmds = func_msgParser(self, msgs, a)
      except KeyboardInterrupt:
        print("Warning:Keyboard interrupt. Exiting")
        self.disconnect()
        break
      except OSError:
        print("Warning:OSError. Reconnecting imap")
        self.imap_connect()
        continue
      except smtplib.SMTPServerDisconnected:
        print("Warning:smtplib.SMTPServerDisconnected. Reconnecting smtp")
        self.smtp_connect()
        continue

      # -- Sleep before getting more messages
      if self.debug:
        print("...{}...".format(myWait))  # Blank line for clarity
      time.sleep(myWait)

  # -----------------------------------------------------------------------
  def load_config( self,filename ):
  # -----------------------------------------------------------------------
    conf = {}
    try:
        print( "Reading config file {}".format(filename))
        conf = bios.read(filename)

    except IOError:
        print( "Config file {} not found. Manual configuration".format(filename))
        conf['imap'] =  {}
        conf['imap']['server_domain']= input("IMAP server domain: ")
        conf['imap']['server_user']= input("IMAP server user: ")
        conf['imap']['server_pass']= input("IMAP server passwd: ")
        conf['imap']['server_folder_inbox']= input("IMAP server inbox ('INBOX'): ")

        conf['smtp'] =  {}
        conf['smtp']['server_host']= input("SMTP server domain: ")
        conf['smtp']['server_user']= input("SMTP server user: ")
        conf['smtp']['server_pass']= input("SMTP server passwd: ")
        conf['smtp']['server_protocol']= input("SMTP server protocol ('ssl'): ")
        conf['smtp']['server_port']= input("SMTP server port ('487'): ")
        if not conf['smtp']['server_port'] or conf['smtp']['server_port']== "":
           conf['smtp']['server_port']= 587

        conf['automail'] =  {}
        conf['automail']['poll_frecuency']= input("AUTOMAIL poll frecuency ('5'): ")
        conf['automail']['hashtag_test']= '#TEST'

        conf['commands'] =  {}
        conf['command']['sender_whitelist'] = input("COMMANDS Trusted addresses to receive from: ")  # address to receive commands from

    #finally:
    if self.debug:
      print("Config: {}".format(conf))
    return conf
