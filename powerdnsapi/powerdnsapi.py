"""PowerDNS API Data retrieval."""
import json
from http import HTTPStatus
from typing import List, Optional, Tuple, Union

import jsonref  # type: ignore
import requests
from jsonschema import draft7_format_checker
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
from jsonschema.validators import Draft7Validator


class PowerDNSAPI:
    """Make API calls to PowerDNS Authoritative Server."""

    def __init__(self, api_url, api_key, api_version="v1", **kwargs) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.api_version = api_version
        self.headers = {"X-API-Key": api_key, "content-type": "application/json"}
        base_url = "{}/api".format(
            self.api_url if self.api_url[-1] != "/" else self.api_url[:-1]
        )
        self.base_url = f"{base_url}/{self.api_version}/"
        self.zone_schema = jsonref.replace_refs(self.ZONE_SCHEMA)
        self.session = requests.Session()

    ZONE_SCHEMA = {
        "type": "object",
        "required": ["name", "kind"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string", "pattern": ".*\\.$"},
            "type": {"type": "string", "enum": ["zone"]},
            "url": {"type": "string"},
            "kind": {
                "type": "string",
                "enum": ["Native", "Master", "Slave", "Producer", "Consumer"],
            },
            "rrsets": {"$ref": "#/$defs/rrsets"},
            "serial": {"type": "integer"},
            "notified_serial": {"type": "integer"},
            "edited_serial": {"type": "integer"},
            "masters": {"type": "array", "items": {"type": "string"}},
            "dnssec": {"type": "boolean"},
            "nsec3param": {"type": "string"},
            "nsec3narrow": {"type": "boolean"},
            "presigned": {"type": "boolean"},
            "soa_edit": {"type": "string"},
            "soa_edit_api": {"type": "string"},
            "api_rectify": {"type": "boolean"},
            "zone": {"type": "string"},
            "catalog": {"type": "string"},
            "account": {"type": "string"},
            "nameservers": {"type": "array", "items": {"type": "string"}},
            "master_tsig_key_ids": {"type": "array", "items": {"type": "string"}},
            "slave_tsig_key_ids": {"type": "array", "items": {"type": "string"}},
        },
        "$defs": {
            "record": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "disabled": {"type": ["boolean", "null"]},
                },
            },
            "comment": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "account": {"type": "string"},
                    "modified_at": {"type": "integer"},
                },
            },
            "rrset": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "type", "ttl", "records"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "ttl": {"type": "integer"},
                    "changetype": {"type": "string", "enum": ["REPLACE", "DELETE"]},
                    "records": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/record"},
                    },
                    "comments": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/record"},
                    },
                },
            },
            "rrsets": {
                "type": "array",
                "items": {"$ref": "#/$defs/rrset"},
            },
        },
    }

    def _validate(self, schema: dict, data: Union[dict, list]) -> Tuple[bool, str]:
        try:
            Draft7Validator(schema, format_checker=draft7_format_checker).validate(data)
        except JSONSchemaValidationError as err:
            return False, err.message
        return True, ""

    def _make_call(
        self,
        method: str,
        query: str,
        params: Optional[dict] = None,
        data: Optional[Union[dict, str]] = None,
    ) -> requests.Response:
        if isinstance(data, dict):
            data = json.dumps(data)
        request = self.session.request(
            method,
            f"{self.base_url}{query}",
            params=params,
            data=data,
            headers=self.headers,
        )

        return request

    def _make_call_json(
        self,
        method: str,
        query: str,
        params: Optional[dict] = None,
        data: Optional[Union[dict, str]] = None,
    ) -> Union[list, dict]:
        request = self._make_call(method, query, params, data)
        value: Union[list, dict] = []
        if request.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]:
            value = request.json()
        return value

    def get(self, query: str) -> Union[list, dict]:
        """Run GET on PDNS Server.

        Args:
            query (str): _description_

        Returns:
            Union[requests.Response, list, dict]: _description_
        """
        return self._make_call_json("GET", query)

    def post(self, query: str, data: dict) -> Union[list, dict]:
        """Run POST on PDNS Server.

        Args:
            query (str): _description_
            data (dict): _description_

        Returns:
            Union[requests.Response, list, dict]: _description_
        """
        return self._make_call_json("POST", query, data=data)

    def delete(self, query: str) -> requests.Response:
        """Run Delete on PDNS Server.

        Args:
            query (str): _description_

        Returns:
            Union[requests.Response, list, dict]: _description_
        """
        return self._make_call("DELETE", query)

    def patch(self, query: str, data: dict) -> requests.Response:
        """Run PATCH on PDNS Server.

        Args:
            query (str): _description_
            data (dict): _description_

        Returns:
            Union[requests.Response, list, dict]: _description_
        """
        return self._make_call("PATCH", query, data=data)

    def get_servers(self, server_id: Optional[str] = None) -> Union[list, dict]:
        """Get PDNS Server.

        Args:
            server_id (Optional[str], optional): _description_. Defaults to None.

        Returns:
            list: _description_
        """
        query = "servers"
        if server_id:
            query = f"{query}/{server_id}"
        return self.get(query)

    def get_zones(
        self, server_id: str, zone: Optional[str] = None
    ) -> Union[list, dict]:
        """Get PDNS Zones.

        Args:
            server_id (str): _description_
            zone (Optional[str], optional): _description_. Defaults to None.

        Returns:
            Union[requests.Response, list, dict]: _description_
        """
        query = f"servers/{server_id}/zones"
        if zone:
            query = f"{query}/{zone}"
        return self.get(query)

    def validate_zone(self, zone: dict) -> Tuple[bool, str]:
        """Valide PDNS Zone Data.

        Args:
            zone (dict): _description_

        Returns:
            Tuple[bool, str]: _description_
        """
        return self._validate(self.zone_schema, zone)

    def create_zone(
        self, server_id: str, zone: dict
    ) -> Union[list, dict, Tuple[bool, str]]:
        """Create new PDNS Zone.

        Args:
            server_id (str): _description_
            zone (dict): _description_

        Returns:
            Union[dict, Tuple[bool, str]]: _description_
        """
        validate_zone, err = self.validate_zone(zone)
        if validate_zone:
            new_zone = self.post(f"servers/{server_id}/zones", data=zone)
        else:
            return validate_zone, err
        return new_zone

    def update_zone(self, server_id: str, zone: str, data: dict) -> bool:
        """Update PDNS Zone.

        Args:
            server_id (str): _description_
            zone (str): _description_
            data (dict): _description_

        Returns:
            bool: _description_
        """
        successfully_updated: bool = False
        update_zone: requests.Response = self._make_call(
            "PUT", f"servers/{server_id}/zones/{zone}", data=data
        )
        if update_zone.status_code == HTTPStatus.NO_CONTENT:
            successfully_updated = True
        return successfully_updated

    def delete_zone(self, server_id: str, zone: str) -> bool:
        """Delete Zone.

        Args:
            server_id (str): _description_
            zone (str): _description_

        Returns:
            bool: _description_
        """
        successfully_deleted: bool = False
        delete_zone: requests.Response = self.delete(
            f"servers/{server_id}/zones/{zone}"
        )
        if delete_zone.status_code == HTTPStatus.NO_CONTENT:
            successfully_deleted = True

        return successfully_deleted

    def get_rrsets(
        self,
        server_id: str,
        zone: str,
        name: Optional[str] = "",
        type: Optional[str] = "",
    ) -> list:
        """Get Record(s) from Zone.

        Args:
            server_id (str): _description_
            zone (str): _description_
            name (Optional[str], optional): _description_. Defaults to "".
            type (Optional[str], optional): _description_. Defaults to "".

        Returns:
            list: _description_
        """
        zone_data = self.get_zones(server_id, zone)
        rrsets: list = []
        if isinstance(zone_data, dict):
            rrsets = zone_data["rrsets"]

        if name or type:
            if isinstance(rrsets, list):
                rrsets = [
                    data
                    for data in rrsets
                    if name in data["name"] and type in data["type"]
                ]
        return rrsets

    def validate_rrset(self, rrset: Union[list, dict]) -> Tuple[bool, str]:
        """Validate Record(s).

        Args:
            rrset (Union[list, dict]): _description_

        Returns:
            Tuple[bool, str]: _description_
        """
        if isinstance(rrset, list):
            return self._validate(self.zone_schema["$defs"]["rrsets"], rrset)
        elif isinstance(rrset, dict):
            return self._validate(self.zone_schema["$defs"]["rrset"], rrset)
        else:
            return False, "Not a list or dict"

    def process_rrset(
        self, server_id: str, zone: str, rrset: Union[list, dict]
    ) -> bool:
        """Process (Create, Update, Delete) Records.

        Args:
            server_id (str): _description_
            zone (str): _description_
            rrset (Union[list, dict]): _description_

        Returns:
            bool: _description_
        """
        successfully_updated: bool = False
        validate, _ = self.validate_rrset(rrset)
        if validate:
            if isinstance(rrset, list):
                rrset = {"rrsets": rrset}
            elif isinstance(rrset, dict):
                rrset = {"rrsets": [rrset]}

            change_rrset = self.patch(f"servers/{server_id}/zones/{zone}", data=rrset)
            if change_rrset.status_code == HTTPStatus.NO_CONTENT:
                successfully_updated = True
        return successfully_updated

    def create_rrset(self, records: List[dict]) -> Tuple[bool, List[dict]]:
        """Simple Way to create a usable RRSET.

        Args:
            records (List[dict]): A list of dictionaries containing name, type, content and optionally ttl.

        Returns:
            Tuple[bool, List[dict]]: Boolean of if records contained all needed keys,
            List of RRSET object and an error message.
        """
        status = False
        if isinstance(records, list) and all(
            all(key in record for key in ["name", "type", "content"])
            for record in records
        ):
            for record in records:
                record["ttl"] = record.get("ttl", 3600)
                record["changetype"] = "REPLACE"
                record["records"] = [
                    {"content": record.get("content"), "disabled": False}
                ]
                record.pop("content")
            status = True
        return status, records
