'''
Copyright 2013 Sven Reissmann <sven@0x80.io>

This file is part of ddserver.

ddserver is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

ddserver is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ddserver.  If not, see <http://www.gnu.org/licenses/>.
'''

import uuid
import smtplib

from email.mime.text import MIMEText

from ddserver.db import database as db
from ddserver.config import config


class Email(object):

  def __init__(self, username):
    self.smtp_host = config.mail_smtp_host
    self.smtp_port = config.mail_smtp_port
    self.mail_from = config.mail_sender_address

    self.username = username

    self.mail_rcpt = Email.get_mailaddress(username)


  @staticmethod
  def get_mailaddress(username):
    with db.cursor() as cur:
      cur.execute('''
        SELECT email
        FROM users
        WHERE username = %(username)s
      ''', {'username' : username})
      row = cur.fetchone()

    return row['email']


  def make_hash(self):
    ''' generate a uuid as email challange
    '''
    # make a random UUID
    self.uuid = uuid.uuid4()

    with db.cursor() as cur:
      cur.execute('''
        UPDATE users
        SET `authcode` = %(uuid)s
        WHERE `username` = %(username)s
      ''', {'uuid': self.uuid,
            'username': self.username})


  def account_activation(self):
    self.make_hash()

    self.mail_subject = "ddserver: Activate your account"
    self.mail_text = '''
    Hi %s,

    Thank you for registering for a ddserver account.
    Your account has been created. Please use the link below to activate it.

    %s/signup/activate/%s/%s

    If you did not signup for a ddserver account yourself, you can delete
    the account using the same link.

    Sincerely,
    %s
    ''' % (self.username,
           config.baseurl,
           self.username,
           self.uuid,
           config.admin)

    self.send()


  def password_reminder(self):
    self.make_hash()

    self.mail_subject = "ddserver: Your password reset request"
    self.mail_text = '''
    Hi %s,

    We heard you lost your ddserver password.

    Don't panic, changing your password is simple. Please click the link
    below to set a new password for your account.

    %s/lostpass/recover/%s/%s

    If you did not request a password reset, please use the same link to
    cancel the password reset request.

    Sincerely,
    %s
    ''' % (self.username,
           config.baseurl,
           self.username,
           self.uuid,
           config.admin)

    self.send()


  def send(self):
    msg = MIMEText(self.mail_text)
    msg['Subject'] = self.mail_subject
    msg['From'] = self.mail_from
    msg['To'] = self.mail_rcpt

    s = smtplib.SMTP(host = self.smtp_host,
                     port = self.smtp_port)
    s.sendmail(self.mail_from,
               [self.mail_rcpt],
               msg.as_string())
    s.quit()
