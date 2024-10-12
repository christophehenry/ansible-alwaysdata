import json
import unittest
from unittest.mock import patch

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


class AnsibleExitJson(Exception): ...


class AnsibleFailJson(Exception): ...


def exit_json_patch(*args, **kwargs):
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json_patch(*args, **kwargs):
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path_patch(self, arg, required=False):
    if arg.endswith("my_command"):
        return "/usr/bin/my_command"
    else:
        if required:
            fail_json_patch(msg="%r not found !" % arg)


class AlwaysDataTestModule(unittest.TestCase):
    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json_patch,
            fail_json=fail_json_patch,
            get_bin_path=get_bin_path_patch,
        )
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_module_args(self, args):
        args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
        basic._ANSIBLE_ARGS = to_bytes(args)
