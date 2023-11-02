import phonenumbers


def get_e164_phone(phone_number):
    try:
        if phone_number.startswith("8"):
            phone_number = "+7" + phone_number[1:]
        elif phone_number.startswith("7"):
            phone_number = "+" + phone_number
        elif not phone_number.startswith("+"):
            phone_number = "+" + phone_number

        phone_number = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        phone_number = phonenumbers.parse(phone_number, "")

        if phonenumbers.is_valid_number(phone_number):
            return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
        else:
            raise ValueError("Invalid phone number")
    except phonenumbers.NumberParseException as e:
        raise ValueError("Invalid phone number") from e


def format_phone_number(phone_number):
    cleaned_number = ''.join(c for c in phone_number if c.isdigit() or (c == '+' and phone_number.index(c) == 0))

    if not cleaned_number.startswith("+"):
        cleaned_number = "+" + cleaned_number

    return cleaned_number

