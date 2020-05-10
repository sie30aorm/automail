import time
import pyzmail
from datetime import date
from Automail import *
from plugins import *

# ---------------------------------------------------------------------------
def scan_msg(mailer, rawMessageList, idMsg):
# ---------------------------------------------------------------------------
    rawMsg = rawMessageList[idMsg]
    msg_body = pyzmail.PyzMessage.factory(rawMsg[b'BODY[]'])
    msg_subject = msg_body.get_subject();
    print("Msg:{}: Analyzing '{}'".format(idMsg,msg_subject))
    test = mailer.myConf['automail']['hashtag_test']
    if( test in msg_subject ):
        print("Msg:{}: detected {} in {}".format(idMsg,test,msg_subject))

        theSender   = "alvaro.paricio@masmovilb2b.onmicrosoft.com"
        theSender   = "alvaro.paricio@masmovil.com"
        theReceiver = "alvaro.paricio@masmovil.com"
        theSubject  = "TEST-SUBJECTD-REPLACEABLE"
        theBody     = "(this is the body)"
        mailer.send_msg( theSender, theReceiver, theSubject, theBody )

# ---------------------------------------------------------------------------
def scan_msg_ORI(conf, rawMessage, a):
# ---------------------------------------------------------------------------
    """
    Analyze message.  Determine if sender and command are valid.
    Return values:
    None: Sender is invalid or no text part
    False: Invalid command
    Otherwise:
    Array: message split by lines
    :type raws: dict
    """
    print("Msg:{}: Analyzing".format(a))
    msg = pyzmail.PyzMessage.factory(rawMessage[a][b'BODY[]'])
    frm = msg.get_addresses('from')
    if frm[0][1] != sadr:
        print("Unread is from %s <%s> skipping" % (frm[0][0],
                                                   frm[0][1]))
        return None
    global subject
    if not subject.startswith("Re"):
        subject = "Re: " + msg.get_subject()
    print("subject is", subject)
    if msg.text_part is None:
        print("No text part, cannot parse")
        return None
    text = msg.text_part.get_payload().decode(msg.text_part.charset)
    cmds = text.replace('\r', '').split('\n')  # Remove any \r and split on \n
    if cmds[0] not in commands:
        print("Command %s is not in commands" % cmds[0])
        return False
    else:
        return cmds

# ------------------------------------------------------------------------------
def main_loop_ORI( conf, myImapCli, mySmtpCli ):
  while True:  # Main loop
    try:
        print()  # Blank line for clarity
        msgs = get_msg_unread(conf,myImapCli)
        while msgs is None:
            msgs = get_msg_unread(conf,myImapCli)
        for a in msgs.keys():
            if type(a) is not int:
                continue
            cmds = scan_msg(conf,msgs, a)
            if cmds is None:
                continue
            elif cmds is False:  # Invalid Command
                t = "The command is invalid. The commands are: \n"
                for l in commands.keys():
                    t = t + str(l) + "\n"
                mail(t)
                continue
            else:
                print("Command received: \n%s" % cmds)
                r = commands[cmds[0]](cmds)
            mail(str(r))
            print("Command successfully completed! ")
    except KeyboardInterrupt:
        myImapCli.logout()
        mySmtpCli.quit()
        break
    except OSError:
        myImapCli = mailer.imap_connect()
        continue
    except smtplib.SMTPServerDisconnected:
        myImapSmtp = mailer.smtp_connect()
        continue
    finally:
        myImapCli.logout()
        mySmtpCli.quit()
    # -- Sleep before getting more messages
    time.sleep(conf['automail']['poll_frequency'])


# ------------------------------------------------------------------------------
if __name__ == "__main__":
# ------------------------------------------------------------------------------
  mailer = Automail( )
  mailer.set_debug(True)
  mailer.load_conf_file( "config.yaml" )
  mailer.imap_connect()
  mailer.smtp_connect()

  fromDate = date(2020,4,26)
  mailer.main_loop( fromDate, scan_msg )

  mailer.disconnect()
