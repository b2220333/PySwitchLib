import pyswitchlib
import requests
import weakref
import re
import os
import sys
import xml.etree.ElementTree as ElementTree
import xmltodict
import json

class RestInterfaceError(Exception):
    pass

class UnsupportedOSError(Exception):
    pass

class Asset(object):
    """
    This is an auto-generated class for the PySwitchLib device asset.
    Asset provides connection information for PySwitchLib APIs.
    """

    def __init__(self, ip_addr='', auth=('admin', 'password'), fw_ver='', timeout=''):
        def on_deletion (killed_ref):
            self._session.close()

        self._weakref = weakref.ref(self, on_deletion)

        self._ip_addr = ip_addr
        self._auth = auth
        self._os_type = 'nos'
        self._os_ver = fw_ver
        self._os_full_ver = fw_ver
        self._default_connection_timeout = 60                                                                                                                                       
        self._default_response_timeout = 1800                                                                                                                                       
        self._session_timeout = (self._default_connection_timeout, self._default_response_timeout) 
        self._session = requests.Session()
        self._response = requests.Response()
        self._overall_success = True
        self._overall_status = []

        if timeout != '':
            self._session_timeout = timeout

        self._rest_config_path = '/rest/config/running'
        self._rest_operational_path = '/rest/operational-state'
        self._rest_rpc_path = '/rest/operational-state'
        self._rest_discover_path = '/rest'
        self._yang_list = None
        self._module_obj = None

        self._update_uri_prefix_paths()
        self._update_fw_version()
        self._supported_module_name = self._get_supported_module()
        #self._load_module(supported_module_name=self._supported_module_name)

        self._proxied = pyswitchlib.PySwitchLib(module_name=self._supported_module_name, module_obj=self._module_obj, rest_operation=self._rest_operation)

    def __getattr__(self, name):
        return getattr(self._proxied, name)

    def _rest_operation(self, rest_commands=None, yang_list=None, timeout=None):
        auth = self._auth
        del self._overall_status[:]
    
        if isinstance(timeout, basestring):
            if timeout == '':
                timeout = self._session_timeout

        for rest_cmd in rest_commands:
            if len(rest_cmd) < 4:
                rest_cmd.append ("config")

            if rest_cmd[3] == "config":
                uri_prefix_path = self._rest_config_path
            elif rest_cmd[3] == "operational":
                uri_prefix_path = self._rest_operational_path
            elif rest_cmd[3] == "rpc":
                uri_prefix_path = self._rest_rpc_path
            elif rest_cmd[3] == "discover":
                uri_prefix_path = self._rest_discover_path

            header = {"Resource-Depth" : str(rest_cmd[4])}
            url = "http://"+self._ip_addr+uri_prefix_path

            if rest_cmd[0] == "GET":
                self._response = self._session.get(url + rest_cmd[1], headers=header, auth=auth, timeout=timeout)
            elif rest_cmd[0] == "POST":
                self._response = self._session.post(url + rest_cmd[1], auth=auth, data=rest_cmd[2], timeout=timeout)
            elif rest_cmd[0] == "PUT":
                self._response = self._session.put(url + rest_cmd[1], auth=auth, data=rest_cmd[2], timeout=timeout)
            elif rest_cmd[0] == "PATCH":
                self._response = self._session.patch(url + rest_cmd[1], auth=auth, data=rest_cmd[2], timeout=timeout)
            elif rest_cmd[0] == "DELETE":
                self._response = self._session.delete(url + rest_cmd[1], auth=auth, timeout=timeout)

            if yang_list:
                self._yang_list = yang_list
            else:
                self._yang_list = None

            self._overall_status.append({self._ip_addr : {'request': {'op_code': rest_cmd[0], 'uri': rest_cmd[1], 'data': rest_cmd[2]}, 'response': {'status_code': self._response.status_code, 'url': self._response.url, 'text': self._response.text}}})

        return self._get_results()

    def _get_results(self):
        self._overall_success = True

        for status in self._overall_status:
            for key in status:
                if (status[key]['response']['status_code'] < 200) or (status[key]['response']['status_code'] > 299):
                    self._overall_success = False

        return self._overall_success, self._overall_status

    def _update_fw_version(self):
        rest_command = (
            ["POST", "/show-firmware-version", "", "rpc", 1],
        )

        self._rest_operation(rest_command)

        status, result = self._get_results()

        if status == False:                                                                                                                                                         
            if result[0][self._ip_addr]['response']['status_code'] == 404:                                                                                                          
                raise RestInterfaceError('Status Code: ' + str(result[0][self._ip_addr]['response']['status_code']) + ', Error: Not Found.') 

        try:
            rest_root = ElementTree.fromstring(re.sub(' xmlns[^ \t\n\r\f\v>]+', '', result[0][self._ip_addr]['response']['text']))

            if rest_root.find('show-firmware-version').find('os-name') is not None:
                if 'Network Operating System' in rest_root.find('show-firmware-version').find('os-name').text:
                    self._os_type = 'nos'
                elif 'SLX' in rest_root.find('show-firmware-version').find('os-name').text:
                    self._os_type = 'slxos'

            if 'Server' in self._response.headers:
                if 'NOS' in self._response.headers['Server']:
                    self._os_type = 'nos'
                elif 'SLX' in self._response.headers['Server']:
                    self._os_type = 'slxos'

            if rest_root.find('show-firmware-version').find('os-version') is not None:
                self._os_ver = rest_root.find('show-firmware-version').find('os-version').text

            if rest_root.find('show-firmware-version').find('firmware-full-version') is not None:
                self._os_full_ver = rest_root.find('show-firmware-version').find('firmware-full-version').text
        except:
            pass

    def _update_uri_prefix_paths(self):
        rest_command = (
            ["GET", "", "", "discover", 1],
        )

        self._rest_operation(rest_command)

        status, result = self._get_results()

        if status == False:                                                                                                                                                         
            if result[0][self._ip_addr]['response']['status_code'] == 404:                                                                                                          
                raise RestInterfaceError('Status Code: ' + str(result[0][self._ip_addr]['response']['status_code']) + ', Error: Not Found.') 

        try:
            rest_root = ElementTree.fromstring(re.sub(' xmlns[^ \t\n\r\f\v>]+|y:', '', result[0][self._ip_addr]['response']['text']))

            if rest_root.find('config').find('running') is not None:
                self._rest_config_path = rest_root.find('config').find('running').get('self')

            if rest_root.find('operational-state') is not None:
                self._rest_rpc_path = rest_root.find('operational-state').get('self')
                self._rest_operational_path = rest_root.find('operational-state').get('self')

            if rest_root.find('operations') is not None:
                self._rest_rpc_path = rest_root.find('operations').get('self')
        except:
            pass

    def _xml_to_json(self, xml=''):
        return json.dumps(xmltodict.parse(xml))

    def _get_supported_module(self):
        pybind_dir = ''
        site_dir = sys.path

        for site_path in site_dir:
            pybind_dir = os.path.join(site_path, 'pybind')
            if os.path.isdir(pybind_dir):
                pybind_dir = os.path.join(pybind_dir, self._os_type)
                break

        pybind_ver_tree = {}

        max_depth = 1
        cur_depth = pybind_dir.count(os.sep)
        max_os_walk_depth = cur_depth + max_depth

        for (dirpath, dirs, files) in os.walk(pybind_dir):
            if dirpath.count(os.sep) >= max_os_walk_depth:
                del dirs[:]

            submodule = dirpath.partition(pybind_dir)[2].lstrip('/').replace(os.sep, '.')

            if submodule:
                tuple = submodule.strip('v_').split('_')

                for index, elem in enumerate(tuple):
                    if index == 0:
                        if elem not in pybind_ver_tree:
                            pybind_ver_tree[elem] = {}
                    elif index == 1:
                        if elem not in pybind_ver_tree[tuple[0]]:
                            pybind_ver_tree[tuple[0]][elem] = {}
                    elif index == 2:
                        if elem not in pybind_ver_tree[tuple[0]][tuple[1]]:
                            pybind_ver_tree[tuple[0]][tuple[1]][elem] = {}
                    elif index == 3:
                        if elem not in pybind_ver_tree[tuple[0]][tuple[1]][tuple[2]]:
                            pybind_ver_tree[tuple[0]][tuple[1]][tuple[2]][elem] = {}

        os_version_tuple = self._os_ver.strip('.').split('.')
        supported_os_version = []

        if os_version_tuple[0] in pybind_ver_tree:
            supported_os_version.append(os_version_tuple[0])
        else:
            for major in sorted(pybind_ver_tree, reverse=True):
                if os_version_tuple[0] >= re.sub('\D', '', major):
                    supported_os_version.append(major)
                    break;

        if len(supported_os_version) < 1:
            raise UnsupportedOSError("OS Version: " + self._os_type + " " + self._os_ver + " is unsupported.")

        if supported_os_version[0] == os_version_tuple[0] and os_version_tuple[1] in pybind_ver_tree[supported_os_version[0]]:
            supported_os_version.append(os_version_tuple[1])
        else:
            for minor in sorted(pybind_ver_tree[supported_os_version[0]], reverse=True):
                if supported_os_version[0] == os_version_tuple[0]:
                    if os_version_tuple[1] >= minor:
                        supported_os_version.append(minor)
                        break;
                else:
                    supported_os_version.append(minor)
                    break;

        if len(supported_os_version) < 2:
            raise UnsupportedOSError("OS Version: " + self._os_type + " " + self._os_ver + " is unsupported.")

        if supported_os_version[0] == os_version_tuple[0] and supported_os_version[1] == os_version_tuple[1] and os_version_tuple[2] in pybind_ver_tree[supported_os_version[0]][supported_os_version[1]]:
            supported_os_version.append(os_version_tuple[2])
        else:
            for patch in sorted(pybind_ver_tree[supported_os_version[0]][supported_os_version[1]], reverse=True):
                if supported_os_version[0] == os_version_tuple[0] and supported_os_version[1] == os_version_tuple[1]:
                    if os_version_tuple[2] >= patch:
                        supported_os_version.append(patch)
                        break;
                else:
                    supported_os_version.append(patch)
                    break;

        safe_os_version = 'v'+'_'.join(supported_os_version)
        package_name = '.'.join(['pybind', self._os_type, safe_os_version])

        return package_name

    def _load_module(self, supported_module_name=''):
        if supported_module_name:
            self._module_obj =  __import__(supported_module_name, fromlist=['*'])

    def _format_dict_output(self, container=None, keys=None):
        if keys and container:
            if isinstance(container, dict):
                for k in container:
                    if isinstance(container[k], dict):
                        if k.lower() in keys:
                            keys.remove(k.lower())
                            container[k] = [container[k]]
                            self._format_dict_output(container=container[k], keys=keys)
                        else:
                            self._format_dict_output(container=container[k], keys=keys)
                    elif isinstance(container[k], list):
                        for elem in container[k]:
                            self._format_dict_output(container=elem, keys=keys)
            elif isinstance(container, list):
                for elem in container:
                    self._format_dict_output(container=elem, keys=keys)

    def get_os_type(self):
        """
        This is an auto-generated method for the PySwitchLib.

        :rtype: *string*
        :returns: Returns "nos" or "slxos" of the approprate switch type.
        """
        return self._os_type

    def get_os_version(self):
        """
        This is an auto-generated method for the PySwitchLib.

        :rtype: *string*
        :returns: Returns "os-version" value from the show-firmware-version RPC call.
        """
        return self._os_ver

    def get_os_full_version(self):
        """
        This is an auto-generated method for the PySwitchLib.

        :rtype: *string*
        :returns: Returns "full-firmware-version" value from the show-firmware-version RPC call.
        """
        return self._os_full_ver

    def get_xml_output(self):
        """
        This is an auto-generated method for the PySwitchLib.

        :rtype: *string*
        :returns: Returns the xml output response from the last api call.
        """
        return self._overall_status[0][self._ip_addr]['response']['text']

    def get_dict_output(self):
        """
        This is an auto-generated method for the PySwitchLib.

        :rtype: *dict*
        :returns: Returns the json output response from the last api call.
        """
        xml_output = self.get_xml_output()

        if not re.match('^<output', xml_output):
            xml_output = '<output>\r\n' + xml_output + '</output>\r\n' 

        dict_output = json.loads(self._xml_to_json(xml_output))
         
        if dict_output and self._yang_list:
            self._format_dict_output(container=dict_output, keys=self._yang_list)

        return dict_output


