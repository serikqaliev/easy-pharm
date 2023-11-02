def get_last_message_text(message_type, is_mine, name, changed_to=None):
    message_templates = {
        'GROUP_CREATED': ('created new group', 'You created new group'),
        'EVENT_CHAT_CREATED': ('created new event chat', 'You created new event'),
        'TITLE_CHANGED': ('changed title', 'You changed title'),
        'DESCRIPTION_CHANGED': ('changed description', 'You changed description'),
        'COVER_CHANGED': ('changed cover', 'You changed cover'),
        'MEMBER_ADDED': ('added', 'You added'),
        'MEMBER_REMOVED': ('removed', 'You removed'),
        'MEMBER_LEFT': ('left', 'You left'),
        'MEMBER_KICKED': ('kicked', 'You kicked'),
        'MESSAGE_PINNED': ('pinned message', 'You pinned message'),
        'MESSAGE_UNPINNED': ('unpinned message', 'You unpinned message'),
    }

    template = message_templates.get(message_type)
    if not template:
        return ''

    message, fallback = template
    if changed_to is not None:
        fallback = f'{fallback} "{changed_to}"'

    if is_mine:
        return fallback
    else:
        return f'{name} {message}' if changed_to is None else f'{name} {message} "{changed_to}"'
