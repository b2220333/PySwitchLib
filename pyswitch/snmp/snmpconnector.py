from hnmp import *
from hnmp import _convert_value_to_native as convert_value_to_native

class SnmpUtils:

    SNMP_DEVICE_MAP = {
                        '1.3.6.1.4.1.1991.1.3.44.3.2' : 'MLX',
                      }


class SnmpConnector(SNMP):

    def __init__(self, host, port=161, timeout=1, retries=5, community="public", version=2,
                 username="", authproto="sha", authkey="", privproto="aes128", privkey=""):
        SNMP.__init__(self, host, port, timeout, retries, community, version, username, authproto,
                      authkey, privproto, privkey)

    def set_multiple(self, oid):
        """
        Sets a single OID value. If you do not pass value_type hnmp will
        try to guess the correct type. Autodetection is supported for:

        * int and float (as Integer, fractional part will be discarded)
        * IPv4 address (as IpAddress)
        * str (as OctetString)

        Unfortunately, pysnmp does not support the SNMP FLOAT type so
        please use Integer instead.
        """

        varbindlist = list()
        snmpsecurity = self._get_snmp_security()
        for i in range(len(oid)):
            value_type = None
            value = oid[i][1]
            if len(oid[i]) == 3:
                value_type = oid[i][2]

            if value_type is None:
                if isinstance(value, int):
                    data = Integer(value)
                elif isinstance(value, float):
                    data = Integer(value)
                elif isinstance(value, str):
                    if is_ipv4_address(value):
                        data = IpAddress(value)
                    else:
                        data = OctetString(value)
                else:
                    raise TypeError(
                        "Unable to autodetect type. Please pass one of "
                        "these strings as the value_type keyword arg: "
                        ", ".join(TYPES.keys())
                    )
            else:
                if value_type not in TYPES:
                    raise ValueError("'{}' is not one of the supported types: {}".format(
                        value_type,
                        ", ".join(TYPES.keys())
                    ))
                data = TYPES[value_type](value)
            oid_tup = (oid[i][0], data)
            varbindlist.append(oid_tup)

        try:
            engine_error, pdu_error, pdu_error_index, objects = self._cmdgen.setCmd(
                snmpsecurity,
                cmdgen.UdpTransportTarget((self.host, self.port), timeout=self.timeout,
                                          retries=self.retries),
                *varbindlist
            )
            if engine_error:
                raise SNMPError(engine_error)
            if pdu_error:
                raise SNMPError(pdu_error.prettyPrint())
        except Exception as e:
            raise SNMPError(e)

        _, value = objects[0]
        value = convert_value_to_native(value)
        return value

    def get_os_version(self):
        raw = self.table("1.3.6.1.2.1.47.1.1.1.1",
                         columns={
                            2: "PhysicalDescr",
                            7: "PhysicalName",
                            10: "SoftwareRev",
                         },
                         fetch_all_columns=False,
                   )
        version = []
        for oitem in raw.rows:
            if oitem['PhysicalDescr'] == 'NI-MLX-MR Management Module':
                ver = (oitem['PhysicalName'], oitem['SoftwareRev'], 'NI')
                version.append(ver)

        return version
