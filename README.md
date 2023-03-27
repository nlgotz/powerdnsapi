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
