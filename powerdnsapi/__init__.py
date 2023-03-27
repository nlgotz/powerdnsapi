"""PowerDNS API."""
from pkg_resources import DistributionNotFound, get_distribution

from powerdnsapi.powerdnsapi import PowerDNSAPI

__all__ = ["PowerDNSAPI"]

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass
