#!/usr/bin/python

from __future__ import absolute_import, division, print_function

import re

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.christophehenry.alwaysdata.plugins.module_utils.alwaysdata import (
    api_query,
    list_domains,
)

# from .domain import list_domains

__metaclass__ = type


DOCUMENTATION = r"""
---
module: dnsrecord
short_description: Add to or delete DSN records from a domain
version_added: "0.0.1"
author:
    - Christophe Henry (@christophehenry)

options:
    domain:
        description: The domain to manage as displayed on https://admin.alwaysdata.com/domain/
        required: true
        type: str
    token:
        description: The API token to use as defined in https://admin.alwaysdata.com/token/
        required: true
        type: str
    type:
        description: The type of DNS record
        required: if 'state' is 'present'
        type: str
        choices:
        - A
        - AAAA
        - ALIAS
        - CAA
        - CNAME
        - DS
        - MX
        - NS
        - PTR
        - SOA
        - SRV
        - TXT
    name:
        description: Host name; can be null
        required: false
        type: str
    state:
        description: |
            Whether the record should be present or absent.

            When this value is 'absent', and one or several records with the same 'name', 'type'
            and 'value' exists, it will be removed. If 'regex' if specified, it will be used to
            check against records instead of 'value". So any record which 'value' field matches the
            specified 'regex' will be removed.

            When this value is 'present', a new record will be created or existing records will be
            updated with provided values. Existing records will be detected of they have the same
            'name', 'type' and 'value' or if 'existing records' 'values' matches 'regex' when
            procided.
        required: false
        choices:
        - present
        - absent
        default: present
    value:
        description: The value for this DNS record. For instance the IP for A and AAAA records.
        required: if state is 'present'
        type: str
    regex:
        description: |
            A regex to use to detect if record is present. If set, this regex will be used against
            the record value instead the 'name' argument. This is useful, for instance, for records
            of type TXT where the value can be arbitrary.
        required: false
        type: str
    priority:
        description: Priority. Required for MX and SRV records.
        required: false
        type: int
    ttl:
        description: TTL value.
        required: false
        type: int
    annotation:
        description: Appears in records listing.
        required: false
        type: str

attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
"""

EXAMPLES = r"""
# Creating or updating a record
- name: Creating 'git' subdomain
  christophehenry.alwaysdata.dnsrecord:
    domain: example.com
    token: "6^6c*evw95f@2q6s%moh49+gaerd06^&a!*#y&=z8g3vt+=pew"
    state: present
    type: A
    name: git
    value: "128.45.87.69"

# Removing a record
- name: Removing all 'git' subdomain
  christophehenry.alwaysdata.dnsrecord:
    domain: example.com
    token: "6^6c*evw95f@2q6s%moh49+gaerd06^&a!*#y&=z8g3vt+=pew"
    state: absent
    name: git
"""

RETURN = r"""
domain:
    description: The domain used
    type: str
type:
    description: The type of managed DNS record
    type: str
    choices:
    - A
    - AAAA
    - ALIAS
    - CAA
    - CNAME
    - DS
    - MX
    - NS
    - PTR
    - SOA
    - SRV
    - TXT
name:
    description: Host name used
    type: str
"""


__route__ = "record"


MODULE_ARGS = dict(
    domain=dict(type="str", required=True),
    token=dict(type="str", required=True, no_log=True),
    type=dict(
        type="str",
        choices=[
            "A",
            "AAAA",
            "ALIAS",
            "CAA",
            "CNAME",
            "DS",
            "MX",
            "NS",
            "PTR",
            "SOA",
            "SRV",
            "TXT",
        ],
    ),
    name=dict(type="str"),
    state=dict(type="str", default="present", choices=["absent", "present"]),
    value=dict(type="str"),
    regex=dict(type="str"),
    priority=dict(type="int"),
    ttl=dict(type="int"),
    annotation=dict(type="str"),
)


class Domain(object):
    def __init__(self, id, name, href, **_):
        self.id = id
        self.name = name
        self.href = href


class ApiParams(object):
    def __init__(
        self,
        domain,
        type,
        value,
        name=None,
        priority=None,
        ttl=None,
        annotation=None,
        **_,  # Allows passing dict and ignoring other values
    ):
        self.domain = domain
        self.type = type
        self.value = value
        self.priority = priority
        self.name = name
        self.ttl = ttl
        self.annotation = annotation

    def to_api_params(self):
        params = {
            "domain": self.domain.id,
            "type": self.type,
            "value": self.value,
        }
        for param in ("name", "priority", "ttl", "annotation"):
            param_value = getattr(self, param, None)
            if param_value is not None:
                params[param] = param_value

        return params


def list_dnsrecord(module, token):
    return api_query(module, token, __route__)


def delete_dnsrecord(module, token, record_id):
    return api_query(
        module,
        token,
        "{}/{}".format(__route__, record_id),
        expected_status=204,
        fail_msg="Resource was not deleted",
        method="DELETE",
    )


def create_dnsrecord(module, token, **data):
    return api_query(
        module,
        token,
        __route__,
        expected_status=201,
        fail_msg="Ressource was not created",
        method="POST",
        data=data,
    )


def update_dnsrecord(module, token, record_id, /, **data):
    return api_query(module, token, "{}/{}".format(__route__, record_id), method="PUT", data=data)


def state_present(module, token, domain, filtered_records):
    result = {"changed": False}

    params = ApiParams(**{**module.params, "domain": domain})
    api_params = params.to_api_params()
    if not filtered_records:
        # No record present: we're creating
        if not module.check_mode:
            create_dnsrecord(module, token, **api_params)

        result["changed"] = True
        result["diff"] = {
            "before": "",
            "after": {
                "domain": domain.name,
                "name": api_params["name"],
                "type": api_params["type"],
                "value": api_params["value"],
            },
        }

        return module.exit_json(**result)

    before = []
    after = []
    for record in filtered_records:
        old_params = ApiParams(**{**record, "domain": domain})
        updated_params = {**old_params.to_api_params(), **params.to_api_params()}

        if not set(old_params.to_api_params().items()) - set(updated_params.items()):
            # Nothing to change
            continue

        result["changed"] = True
        before.append({**old_params.to_api_params(), "domain": domain.name})
        after.append({**params.to_api_params(), "domain": domain.name})

        if not module.check_mode:
            update_dnsrecord(module, token, record["id"], **params.to_api_params())

    result["diff"] = {
        "before": before,
        "after": after,
    }

    return module.exit_json(**result)


def state_absent(module, token, domain, filtered_records):
    result = {
        "changed": False,
        "domain": module.params["domain"],
    }
    for param in ("type", "value", "name"):
        if module.params.get(param, None):
            result[param] = module.params[param]

    if not filtered_records:
        result["diff"] = {"before": "", "after": ""}
        return module.exit_json(**result)

    if not module.check_mode:
        for filtered_record in filtered_records:
            delete_dnsrecord(module, token, filtered_record["id"])

    result["changed"] = True
    result["diff"] = {
        "before": [
            {
                "domain": domain.name,
                "type": filtered_record["type"],
                "name": filtered_record["name"],
                "value": filtered_record["value"],
            }
            for filtered_record in filtered_records
        ],
        "after": [],
    }

    return module.exit_json(**result)


def dnsrecord():
    module = AnsibleModule(
        argument_spec=MODULE_ARGS,
        supports_check_mode=True,
        required_one_of=[["value", "name", "regex"]],
        required_if=[["state", "present", ["value", "type"]]],
    )

    # ~~~~~~~~~~~~~~~~~~~~~~~ Args checks ~~~~~~~~~~~~~~~~~~~~~~~ #
    if module.params.get("name") and not re.compile(r"[\w\-.]+").match(module.params["name"]):
        return module.fail_json(
            msg=(
                "'name' argument must be composed of ASCII letters (a-z), "
                "numbers (0-9) dashes, underscores and dots."
            )
        )

    if module.params.get("priority") is None and module.params["type"] in ("MX", "SRV"):
        return module.fail_json(msg="'priority' argument is required for 'MX', 'SRV' records.")

    token = module.params.get("token")
    state = module.params.get("state")

    # ~~~~~~~~~~~~~~~~~~~~~~~ Checking domain ~~~~~~~~~~~~~~~~~~~~~~~ #
    domains = list_domains(module, token)
    domain = [it for it in domains if it["name"] == module.params["domain"]]

    if not domain:
        return module.fail_json(
            msg="Unkown domain {}; available: {}".format(
                module.params["domain"], [it["name"] for it in domains]
            )
        )

    domain = Domain(**domain[0])

    def filter_record(record):
        prereq = record["domain"]["href"] == domain.href and record["name"] == module.params["name"]

        if module.params.get("type"):
            prereq = prereq and record["type"] == module.params["type"]

        if module.params.get("regex"):
            return prereq and re.compile(module.params["regex"]).match(record["value"])

        if state == "absent" and module.params.get("value") is not None:
            prereq = prereq and record["value"] == module.params["value"]

        return prereq

    filtered_records = list(filter(filter_record, list_dnsrecord(module, token)))

    # ~~~~~~~~~~~~~~~~~~~~~~~ Execution ~~~~~~~~~~~~~~~~~~~~~~~ #
    if state == "absent":
        return state_absent(module, token, domain, filtered_records)

    return state_present(module, token, domain, filtered_records)


def main():
    dnsrecord()


if __name__ == "__main__":
    main()
