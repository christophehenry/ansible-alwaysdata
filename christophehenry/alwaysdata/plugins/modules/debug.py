from logging import getLogger

from tox.session.cmd.run.common import logger

from christophehenry.alwaysdata.plugins.modules.dnsrecord import main

"""This file is used to debug the code during the development phase."""

if __name__ == "__main__":
    import json
    from ansible.module_utils import basic
    from ansible.module_utils.common.text.converters import to_bytes

    try:
        """
        Put you sensitive test data in ./debug_data/py. It is ignored by git and Ansible
        """
        from christophehenry.alwaysdata.plugins.modules.debug_data import data
    except ImportError:
        logger.error(
            "Put you sensitive test data in ./debug_data/py. It is ignored by git and Ansible."
        )
        raise SystemExit(1)

    logger = getLogger(__name__)
    logger.warning("This file is used to debug the code during the development phase")

    args = json.dumps({"ANSIBLE_MODULE_ARGS": data})
    basic._ANSIBLE_ARGS = to_bytes(args)
    main()
