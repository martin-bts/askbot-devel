"""
Context processor for lightweight session messages.

Time-stamp: <2008-07-19 23:16:19 carljm context_processors.py>

"""
from django.conf import settings as django_settings

def user_messages(request):
    """
    Returns session messages for the current session.
    """
    if not request.path.startswith('/' + django_settings.ASKBOT_URL):
        # only do work when visiting the Askbot app
        return {}

    #the get_and_delete_messages is added to anonymous user by the
    #ConnectToSessionMessages middleware by the process_request,
    #however - if the user is logging out via /admin/logout/
    #the AnonymousUser is installed in the response and thus
    #the Askbot's session messages hack will fail, so we have
    #an extra if statement here.
    if  hasattr(request.user, 'message_set') \
    and hasattr(request.user.message_set, 'get_and_delete_messages'):
        messages = request.user.message_set.get_and_delete_messages()
        return { 'user_messages': messages }
    return {}
