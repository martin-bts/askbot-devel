from django.conf import settings as django_settings
from django.contrib import messages
from askbot.conf import settings as askbot_settings
from askbot.user_messages.anon_user import AnonymousMessageManager

class AnonymousUserMessagesMiddleware(object):
    """Middleware that attaches messages to anonymous users, and
    makes sure that anonymous user greeting is shown just once.
    Middleware does not do anything if the anonymous user greeting
    is disabled.
    """
    def __init__(self, get_response=None): # i think get_reponse is never None. If it's not another middleware it's the view, I think
        if get_response is None:
            get_response = lambda x:x
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/' + django_settings.ASKBOT_URL) \
        and request.user.is_anonymous:
            self.process_request(request)

        response = self.get_response(request) # i think this simply chains all middleware

        if request.path.startswith('/' + django_settings.ASKBOT_URL):
            response = self.process_response(request, response)

        return response

    def process_request(self, request):
        """Enables anonymous users to receive messages
        the same way as authenticated users, and sets
        the anonymous user greeting, if it should be shown"""

        #1) Attach the ability to receive messages
        #plug on deepcopy which may be called by django db "driver"
        AnonymousMessageManager.connect_anonymous_user(request)

        #2) set the first greeting one time per session only
        if  askbot_settings.ENABLE_GREETING_FOR_ANON_USER \
        and request.session.get('greeting_set') is not None \
        and request.COOKIES.get('askbot_visitor') is not None:
            request.session['greeting_set'] = True
            msg = askbot_settings.GREETING_FOR_ANONYMOUS_USER
            #messages.info(request, message=msg) # don't use Django messages as a mini PoC
            request.user.message_set.create(message=msg)

    def process_response(self, request, response):
        """Adds the ``'askbot_visitor'``key to cookie if user ever
        authenticates so that the anonymous user message won't
        be shown after the user logs out"""
        if request.user.is_authenticated \
        and request.COOKIES.get('askbot_visitor') is None:
            #import datetime
            #max_age = 365*24*60*60
            #expires = datetime.datetime.strftime\
            #        (datetime.datetime.utcnow() +
            #                datetime.timedelta(seconds=max_age),\
            #                        "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie('askbot_visitor', False)
        return response
