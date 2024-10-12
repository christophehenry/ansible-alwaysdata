import json
import re
from urllib.error import HTTPError

from ansible.module_utils.urls import fetch_url


def api_query(
    module,
    token,
    route,
    *,
    expected_status=None,
    fail_msg="Unexpected server error.",
    method="GET",
    data=None,
    **kwargs,
):
    route = re.sub(r"/+", "/", "/{}/".format(route))
    kwargs.setdefault("headers", {})
    kwargs["headers"].setdefault("Accept", "application/json")

    if data is not None:
        kwargs["data"] = module.jsonify(data)
        kwargs["headers"]["Content-Type"] = "application/json"

    response, info = fetch_url(
        module,
        "https://{}:@api.alwaysdata.com/v1{}".format(token, route),
        method=method,
        **kwargs,
    )

    if response.status == 401:
        http_screw_up(module, "Got unauthorized response: bad token provided", info)

    if 500 <= response.status < 600:
        http_screw_up(module, "The AlwaysData HTTP API has a problem. Retry later", info)

    if isinstance(response, HTTPError):
        http_screw_up(module, "Unexpected server error.", info)

    if expected_status and response.status != expected_status:
        http_screw_up(module, fail_msg, info)

    response_body = response.read().decode("utf-8")
    return json.loads(response_body) if response_body else None


def http_screw_up(module, msg, info):
    kwargs = {"msg": msg}
    if module._verbosity >= 3:
        kwargs["debug"] = info
    module.fail_json(**kwargs)


def list_domains(module, token):
    return api_query(module, token, "domain")
