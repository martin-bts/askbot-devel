"""middleware that allows anonymous users
receive messages using the now deprecated `message_set()`
interface of the user objects.

To allow anonymous users accept messages, a special
message manager is defined here, and :meth:`__deepcopy__()` method
added to the :class:`AnonymousUser` so that user could be pickled.

Secondly, it sends greeting message to anonymous users.
"""

class AnonymousMessageManager(object):
    """message manager for the anonymous user"""
    def __init__(self, request):
        self.request = request

    def create(self, message=''):
        """send message to anonymous user

        Create a message in the current session.
        """
        assert hasattr(self.request, 'session'), "django-session-messages requires session middleware to be installed. Edit your MIDDLEWARE setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."

        try:
            self.request.session['messages'].append(message)
        except KeyError:
            self.request.session['messages'] = [message]

    def get_and_delete(self):
        """returns messages sent to the anonymous user
        via session, and removes messages from the session

        Get and delete all messages for current session.
        Optionally also fetches user messages from django.contrib.auth.
        """
        assert hasattr(self.request, 'session'), "django-session-messages requires session middleware to be installed. Edit your MIDDLEWARE setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        messages = self.request.session.pop('messages', [])
        return messages

    @classmethod
    def connect_anonymous_user(cls, request):
        def dummy_deepcopy(*arg):
            """this is necessary to prevent deepcopy() on anonymous user object
            that now contains reference to request, which cannot be deepcopied
            """
            return None
        request.user.__deepcopy__ = dummy_deepcopy
        request.user.message_set = AnonymousMessageManager(request)
        request.user.get_and_delete_messages = \
                    request.user.message_set.get_and_delete
