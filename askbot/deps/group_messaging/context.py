from askbot.deps.group_messaging.models import get_unread_inbox_counter, Message

def group_messaging_context(request):
    if not request.user.is_authenticated:
        return {}
    count_record  = get_unread_inbox_counter(request.user)
    notifications = Message.notifications.get_and_delete_messages(request.user)
    return {
        'group_messaging_unread_inbox_count': count_record.count,
        'group_messaging_notifications': notifications
        }
