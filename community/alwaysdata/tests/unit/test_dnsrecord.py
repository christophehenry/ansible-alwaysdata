import unittest
from datetime import datetime, timezone, timedelta
from random import randint
from unittest import mock

from ansible_collections.community.alwaysdata.plugins.modules import (
    dnsrecord,
    yaml_dump,
)

from .utils import AlwaysDataTestModule, AnsibleFailJson, AnsibleExitJson


class TestDNSRecordModule(AlwaysDataTestModule):
    def setUp(self):
        super().setUp()
        self.token = "n=w@j75(@@&0kfu1@e!0wmg_&87vht$i3cg@tl8sl%9_5&vo&!"
        self.main_domain = "example.test"
        self.other_domains = ("example2.test", "example3.test")
        self.record_names = ("git", "ansible", "wololo")
        self.ips = ("12.102.160.30", "6b39:4323:4a95:8bd3:79fb:23da:a6b0:1dec")

        self.domains = {
            domain: {
                "id": (domain_id := randint(10000, 99999)),
                "name": domain,
                "is_internal": True,
                "auto_renew": True,
                "date_expiration": (
                    datetime.now(tz=timezone.utc) + timedelta(days=365)
                ).isoformat(),
                "default_ip_address": None,
                "default_ssl_certificate": None,
                "alias_mail_of": None,
                "dkim_selector": None,
                "dkim_public_key": None,
                "dkim_private_key": None,
                "href": f"/v1/domain/{domain_id}/",
                "annotation": "Lorem ipsum",
            }
            for domain in (self.main_domain, *self.other_domains)
        }

        self.main_domain_records = [
            {
                "id": (record_id := randint(10000, 99999)),
                "domain": {"href": f"/v1/domain/{self.domains[self.main_domain]['id']}/"},
                "type": "A",
                "name": name,
                "value": ip,
                "priority": None,
                "ttl": 300,
                "href": f"/v1/record/{record_id}/",
                "annotation": "",
                "is_user_defined": False,
                "is_active": True,
            }
            for name in self.record_names
            for ip in self.ips
        ]

        self.records = [
            {
                "id": (record_id := randint(10000, 99999)),
                "domain": {"href": f"/v1/domain/{self.domains[domain]['id']}/"},
                "type": "A",
                "name": name,
                "value": ip,
                "priority": None,
                "ttl": 300,
                "href": f"/v1/record/{record_id}/",
                "annotation": "",
                "is_user_defined": False,
                "is_active": True,
            }
            for name in self.record_names
            for ip in self.ips
            for domain in self.other_domains
        ]
        self.records = [*self.records, *self.main_domain_records]

        self.correct_data = {
            "domain": self.main_domain,
            "token": self.token,
            "type": "A",
            "value": self.ips[0],
            "name": self.record_names[0],
            "state": "present",
        }

    def test_module_args(self):
        with self.subTest("No arg"):
            with self.assertRaises(AnsibleFailJson):
                self.set_module_args({})
                dnsrecord.main()

        with self.subTest("type=Nope"):
            self.set_module_args({**self.correct_data, "type": "Nope"})
            with self.assertRaises(AnsibleFailJson) as e:
                dnsrecord.main()

            self.assertEqual(
                {
                    "msg": (
                        "value of type must be one of: A, AAAA, ALIAS, CAA, "
                        "CNAME, DS, MX, NS, PTR, SOA, SRV, TXT, got: Nope"
                    ),
                    "failed": True,
                },
                e.exception.args[0],
            )

        with self.subTest("name argument sanity checking"):
            self.set_module_args({**self.correct_data, "name": "#test.com"})
            with self.assertRaises(AnsibleFailJson) as e:
                dnsrecord.main()

            self.assertEqual(
                {
                    "msg": (
                        "'name' argument must be composed of ASCII letters (a-z), "
                        "numbers (0-9) dashes, underscores and dots."
                    ),
                    "failed": True,
                },
                e.exception.args[0],
            )

        for t in ("MX", "SRV"):
            with self.subTest(f"priority required for {t}"):
                self.set_module_args({**self.correct_data, "type": t})
                with self.assertRaises(AnsibleFailJson) as e:
                    dnsrecord.main()

                self.assertEqual(
                    {
                        "msg": "'priority' argument is required for 'MX', 'SRV' records.",
                        "failed": True,
                    },
                    e.exception.args[0],
                )

        with self.subTest("Can't remove all records of the same type"):
            self.set_module_args(
                {
                    "domain": self.correct_data["domain"],
                    "token": self.correct_data["token"],
                    "type": self.correct_data["type"],
                    "state": "absent",
                }
            )
            with self.assertRaises(AnsibleFailJson) as e:
                dnsrecord.main()

            self.assertEqual(
                {
                    "msg": "one of the following is required: value, name, regex",
                    "failed": True,
                },
                e.exception.args[0],
            )

        with self.subTest("Unknown domain"):
            self.set_module_args(self.correct_data)

            with unittest.mock.patch(
                "ansible_collections.community.alwaysdata.plugins.modules.dnsrecord.list_domains",
                return_value=[],
            ):
                with self.assertRaises(AnsibleFailJson) as e:
                    dnsrecord.main()

                self.assertEqual(
                    {
                        "msg": "Unkown domain example.test; available: []",
                        "failed": True,
                    },
                    e.exception.args[0],
                )

    @mock.patch(f"{dnsrecord.__name__}.delete_dnsrecord")
    @mock.patch(f"{dnsrecord.__name__}.list_dnsrecord")
    @mock.patch(f"{dnsrecord.__name__}.list_domains")
    @mock.patch(f"{dnsrecord.__name__}.state_absent", wraps=dnsrecord.state_absent)
    def test_absent(
        self,
        state_absent_mock: mock.Mock,
        list_domains_mock: mock.Mock,
        list_dnsrecord_mock: mock.Mock,
        delete_dnsrecord_mock: mock.Mock,
    ):
        with self.subTest("I can remove all the records of the same name"):
            self.set_module_args(
                {
                    "domain": self.correct_data["domain"],
                    "token": self.correct_data["token"],
                    "name": self.correct_data["name"],
                    "state": "absent",
                }
            )

            list_domains_mock.return_value = list(self.domains.values())
            list_dnsrecord_mock.return_value = list(self.main_domain_records)
            delete_dnsrecord_mock.return_value = None

            records_to_remove = [
                it for it in self.main_domain_records if it["name"] == self.correct_data["name"]
            ]

            self.assertEqual(2, len(records_to_remove))

            with self.assertRaises(AnsibleExitJson) as e:
                dnsrecord.main()

            self.assertEqual(
                {
                    "changed": True,
                    "domain": self.correct_data["domain"],
                    "name": self.correct_data["name"],
                    "diff": {
                        "after": yaml_dump([]),
                        "before": yaml_dump(
                            [
                                {
                                    "domain": self.correct_data["domain"],
                                    "name": it["name"],
                                    "type": it["type"],
                                    "value": it["value"],
                                }
                                for it in records_to_remove
                            ]
                        ),
                    },
                },
                e.exception.args[0],
            )

            state_absent_mock.assert_called_once_with(
                mock.ANY, self.token, mock.ANY, records_to_remove
            )
