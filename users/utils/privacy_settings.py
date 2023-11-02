from users.models import Privacy, Contact


def get_user_avatar(user, requested_user):  # user, requested_user
    privacy_settings = Privacy.objects.filter(user=user).first()
    profile_image_visibility = privacy_settings.profile_image if privacy_settings else None
    avatar = user.avatar.url if user.avatar else None

    if not profile_image_visibility:
        avatar = avatar

    if profile_image_visibility == 'All':
        avatar = avatar
    elif profile_image_visibility == 'My Contacts':
        # TODO: check if user is in contacts
        contact = Contact.objects.filter(phone=user.phone, user=requested_user).first()
        if contact:
            avatar = avatar
        else:
            avatar = None

    return avatar
