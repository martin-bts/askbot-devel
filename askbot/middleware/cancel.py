from django.http import HttpResponseRedirect
from askbot.utils.forms import get_next_url
class CancelActionMiddleware(object):
    def __init__(self, get_response=None): # i think get_reponse is never None. If it's not another middleware it's the view, I think
        if get_response is None:
            get_response = lambda x:x
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'cancel' in request.GET or 'cancel' in request.POST:
            #todo use session messages for the anonymous users
            try:
                msg = getattr(view_func,'CANCEL_MESSAGE')
            except AttributeError:
                msg = 'action canceled'
            request.user.message_set.create(message=str(msg))
            return HttpResponseRedirect(get_next_url(request))
        else:
            return None
