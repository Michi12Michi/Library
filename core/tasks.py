from datetime import datetime
from django.core.mail import send_mail
from .models import CheckOut, Hold, User

def check_checkout_validity():

    def generate_return_email(**kwargs):
        return f'''Dear {kwargs['user'].first_name} {kwargs['user'].last_name}, we are sorry to inform you that your checkout has been expired on {kwargs['c'].end_time}.\nHere's the relevant checkout data:\n\nTitle: {kwargs['c'].book.title}\nEdition: {kwargs['c'].book.edition.name}\nCheckout start date: {kwargs['c'].start_time}\n\nWe strongly encourage you to return the book to the Random Central Library.\n\nYour account has been deactivated: you won't be able to submit holds and checkout until the book is returned.\nFeel free to contact our staff in case of troubles.\n\nKind regards, Public Library.'''

    current_dt = datetime.now()
    expired_checkouts = CheckOut.objects.filter(is_returned=False, end_time__lte=current_dt, email_sent=False).all()
    if expired_checkouts:
        for c in expired_checkouts:
            user = User.objects.get(c.user)
            user.is_active = False
            user.save()
            send_mail(subject="Expired checkout!", 
                      message=generate_return_email(user, c),
                      from_email=None, 
                      recipient_list=[f"{user.email}"])
            c.email_sent = True
            c.save()

def check_hold_validity():

    current_dt = datetime.now()
    expired_holds = Hold.objects.filter(end_time__lt=current_dt).all()
    if expired_holds:
        for e in expired_holds:
            e.delete()