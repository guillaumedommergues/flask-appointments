""" Functions to communicate with employees/ customers """

import pytz
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from twilio.rest import Client
import StringIO
from data_model import Branch, User, Appointment

##################### SMS COMMUNICATION #######################################

TWILIO_SID = '<your_account_sid>' 
TWILIO_TOKEN = '<your_account_token>'
TWILIO_NUMBER = '<your_account_number>'
MAILGUN_ADDRESS = '<your_hhtp_call_address>'
MAILGUN_EMAIL = '<your_email_address>'
MAILGUN_KEY = '<your_key>'

def send_sms(appointment, sms_method):
    """ Sends a message to the customers via the Twilio API
    to create, cancel, or confirm the appointment.  
    """
    if sms_method == 'PUBLISH':
        message = "Appointment at %s on %s booked. Reply 'no appointment' to\
cancel" %(appointment.time,appointment.date)
    if sms_method == 'CANCEL':
        message= "Appointment cancelled!"
    if sms_method == 'CONFIRM':
        message= "A friendly reminder: %s is expecting you tomorrow %s at %s."%(
                appointment.user.name, appointment.time,
                appointment.user.branch.name)
    account_sid = TWILIO_SID
    auth_token = TWILIO_TOKEN
    client=Client(account_sid,auth_token)
    client.messages.create(to=appointment.booked_by_phone,
                        from_=TWILIO_NUMBER,
                        body=message)
    return

def send_reminder(timezone):
    """ Triggers the send_sms function for the right customers
    to remind the customers of the appointment.
    """
    tomorrow = datetime.now(pytz.timezone(timezone)).date()+timedelta(days=1)
    appointments = (Appointment.query
                    .filter(Appointment.date==tomorrow)
                    .filter(Appointment.bookable_booked=="booked")
                    .join(Appointment.user).join(User.branch)
                    .filter(Branch.time_zone==timezone)
                    .all())
    for appointment in appointments:
        send_sms(appointment, sms_method='CONFIRM')
    return

######################### EMAIL COMMUNICATION #################################

def create_ics_file(_appointment, _ics_method):
    """ Returns an ICS file (the standard for email invitations)
    that will be sent to the agent to let them know
    if an appointment is booked or cancelled
    """
    tz = pytz.timezone(_appointment.user.branch.time_zone)
    date_start = tz.localize(
        datetime.combine(_appointment.date,_appointment.time))
    date_end = date_start+timedelta(hours=1)
    filename = str(_appointment.id)+".ics"
    #step 1: creating the message
    if _ics_method =='PUBLISH':
        sequence = 1
        summary = _appointment.booked_by_name+"'s appointment"
        description = _appointment.booked_by_name+' would like to meet for '\
                    +_appointment.topic+'.His number :'+_appointment.booked_by_phone
    if _ics_method =='CANCEL':
        sequence = 2
        summary = _appointment.booked_by_name+' appointment cancellation'
        description = 'Cancelling' +_appointment.booked_by_name+"'s appointment"
    #step 2: embedding message in the ICS format
    event = Event()
    event.add('dtstart', date_start)
    event.add('dtend', date_end)
    event.add('description', description)
    event.add('summary', summary)
    event.add('organizer', MAILGUN_EMAIL)
    event.add('sequence', sequence)
    event['uid'] = 'boh_booking'+str(_appointment.id)
    cal = Calendar()
    cal.add('prodid', '-//My calendar application//example.com//')
    cal.add('method', _ics_method)
    cal.add_component(event)
    cal_content = cal.to_ical()
    ics_file = StringIO.StringIO()
    ics_file.write(cal_content)
    return ics_file, filename

def send_outlook_invite(filename, recepient, ics_file, invite_method):
    """ Sends an email with the ICS file in it via Mailgun API """
    #step 1: creating email message"
    if invite_method =='PUBLISH':
        subject = "New appointment booked"
        text = "Please remember to add it to your calendar!"
    if invite_method == 'CANCEL':
        subject = "Appointment ceancelled"
        text = "Please remove it to your calendar!"
    #step 2: send message"
    ics_file.seek(0)
    requests.post(
        MAILGUN_ADDRESS,
        auth = ("api", MAILGUN_KEY),
        files = [("attachment", (filename, ics_file))],
        data = {
            "from": MAILGUN_EMAIL,
            "to": recepient,
            "subject": subject,
            "text": text})
    ics_file.close()
    return


