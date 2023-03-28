# PowerDNSAPI

Python Package to make API calls to PowerDNS Authoritative Server.

This does not implement functions for all PowerDNS Authoritative API calls, rather common ones that I want automated.

## Installing

TBD

## Usage

```python
from powerdnsapi import PowerDNSAPI

pdns = PowerDNSAPI("http://my_server:8081", "123ABC")

pdns.get_servers()
```

## Q&A

**Why another PowerDNS API python library?** Looking at the existing projects, none suited what I wanted. I wanted to have some helpers to simplify common tasks and also get the data back as a dict/list instead of nested objects.

**Why no tests?** This is a side/after hours project and I haven't set aside time for that yet.

## Roadmap

- Add documentation
- Add PowerDNS Container for local development
- Add unit tests
- Add integration tests against different versions of PowerDNS
