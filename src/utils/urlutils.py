import urlparse


def get_qs_parsed(qs):
    return urlparse.parse_qs(qs)


def get_parameter(parsedQS, key, defaultValue):
    return int(parsedQS[key][0]) if parsedQS.has_key(key) else defaultValue


def get_string_parameter(parsedQS, key, defaultValue):
    return parsedQS[key][0] if parsedQS.has_key(key) else defaultValue