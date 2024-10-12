# Ansible Collection - christophehenry.alwaysdata

Collection of modules for interacting with AlwaysData's HTTP API

This collection currently only supports [registering DNS records](https://api.alwaysdata.com/v1/record/doc/).

## Contributing

How to test:

```shell
pip install -e .[dev]
cd christophehenry/alwaysdata
ansible-test units --venv
```
