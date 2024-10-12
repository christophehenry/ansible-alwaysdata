__route__ = "domain"

from . import api_query


def list_domains(module, token):
    return api_query(module, token, __route__)
