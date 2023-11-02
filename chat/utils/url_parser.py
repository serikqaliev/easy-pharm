import re

def url_parser(string):
    return re.search("(?P<url>https?://[^\s]+)", string).group("url")