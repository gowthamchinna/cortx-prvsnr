#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import logging
import configparser
from enum import Enum
from typing import Type, List
from copy import deepcopy
from pathlib import Path

from .validate_setup import (
    NetworkParamsValidation,
    ReleaseParamsValidation,
    StorageEnclosureDefaultParamsValidation,
    NodeParamsValidation,
    StorageNodeParamsValidation,
    ServerDefaultParamsValidation
)
from .. import inputs
from ..vendor import attr

from ..utils import run_subprocess_cmd

from ..values import UNCHANGED
from . import (
    CommandParserFillerMixin
)


logger = logging.getLogger(__name__)


class SetupType(Enum):
    SINGLE = "single"
    DUAL = "dual"
    GENERIC = "generic"
    THREE_NODE = "3_node"


class RunArgsConfigureSetupAttrs:
    path: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "config path to update pillar"
            }
        }
    )
    setup_type: str = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "the type of the setup",
                'choices': [st.value for st in SetupType]
            }
        },
        default=SetupType.GENERIC.value,
        # TODO EOS-12076 better validation
        converter=(lambda v: SetupType(v))
    )
    number_of_nodes: int = attr.ib(
        metadata={
            inputs.METADATA_ARGPARSER: {
                'help': "No of nodes in cluster"
            }
        },
        converter=int
    )


@attr.s(auto_attribs=True)
class RunArgsConfigureSetup:
    path: str = RunArgsConfigureSetupAttrs.path
    number_of_nodes: int = RunArgsConfigureSetupAttrs.number_of_nodes

    # FIXME number of nodes might be the same for different setup types
    setup_type: str = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        if self.number_of_nodes == 1:
            self.setup_type = SetupType.SINGLE
        elif self.number_of_nodes == 2:
            self.setup_type = SetupType.DUAL
        elif self.number_of_nodes == 3:
            self.setup_type = SetupType._3_NODE
        else:
            self.setup_type = SetupType.GENERIC


@attr.s(auto_attribs=True)
class ConfigureSetup(CommandParserFillerMixin):
    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = RunArgsConfigureSetup

    validate_map = {"cluster": NetworkParamsValidation,
                    "node": NodeParamsValidation,
                    "controller": StorageNodeParamsValidation,
                    "srv_default": ServerDefaultParamsValidation,
                    "storage_enclosure_default": StorageEnclosureDefaultParamsValidation}

    def _parse_params(self, input):
        params = {}
        for key in input:
            val = key.split(".")
            conf_values = [
                'ip', 'user', 'secret', 'ipaddr', 'interfaces', 'gateway',
                'netmask', 'public_ip_addr', 'type',
                'id', 'roles', 'data_devices', 'metadata_device' ]

            if len(val) > 2 and val[-1] in conf_values:
                params[f'{val[-3]}_{val[-2]}_{val[-1]}'] = input[key]

            elif len(val) > 1 and val[-1] in conf_values:
                params[f'{val[-2]}_{val[-1]}'] = input[key]
            else:
                params[val[-1]] = input[key]
        return params

    def _validate_params(self, input_type, content):
        params = self._parse_params(content)
        self.validate_map[input_type](**params)

    def _parse_input(self, input):
        for key in input:
            if input[key] and "," in input[key]:
                value = [f'\"{x.strip()}\"' for x in input[key].split(",")]
                value = ','.join(value)
                input[key] = f'[{value}]'
            #elif 'network.mgmt.interfaces' in key:
            elif 'interfaces' or 'device' or 'devices' in key:
                # special case single value as array
                # Need to fix this array having single value
                input[key] = f'[\"{input[key]}\"]'
            else:
                if input[key]:
                    if input[key] == 'None':
                        input[key] = '\"\"'
                    else:
                        input[key] = f'\"{input[key]}\"'
                else:
                    input[key] = UNCHANGED

    def _parse_pillar_key(self, key):
        pillar_key = deepcopy(key)
        return pillar_key.replace(".", "/")

    def run(self, path, number_of_nodes):  # noqa: C901

        if not Path(path).is_file():
            raise ValueError('config file is missing')

        config = configparser.ConfigParser()
        config.read(path)
        logger.info("Updating salt data :")
        content = {section: dict(config.items(section)) for section in config.sections()}  # noqa: E501
        logger.debug(f"params data {content}")

        input_type = None
        pillar_type = None
        node_list = []
        count = int(number_of_nodes)

        pillar_map = {"srv_default": "cluster",
                      "storage_enclosure_default": "storage_enclosure"}

        for section in content:
            input_type = section
            pillar_type = section
            if 'default' in section:
                #for section_name in ['srv_default', 'storage_enclosure_default']:
                if 'srvnode' in section:
                    input_type = 'srv_default'
                elif 'storage' in section:
                    input_type = 'storage_enclosure_default'
                pillar_map_type = pillar_map[input_type]
                pillar_type = f'{pillar_map_type}/{section}'
                count = count - 1
                node_list.append(f"\"{section}\"")

            else:
                if 'srvnode' in section:
                    input_type = 'node'
                    pillar_type = f'cluster/{section}'
                elif 'storage' in section:
                    # TODO: verify input_type and 
                    # pillar_type for storage_enclosure
                    input_type = 'controller'
                    pillar_type = f'storage_enclosure/{section}'
                count = count - 1
                node_list.append(f"\"{section}\"")

            self._validate_params(input_type, content[section])
            self._parse_input(content[section])

            for pillar_key in content[section]:
                key = f'{pillar_type}/{self._parse_pillar_key(pillar_key)}'
                run_subprocess_cmd([
                       "provisioner", "pillar_set",
                       key, f"{content[section][pillar_key]}"])

        # Update cluster/node_list
        run_subprocess_cmd([
            "provisioner", "pillar_set",
            "cluster/node_list", f"[{','.join(node_list)}]"])

        if content.get('cluster', None):
            if content.get('cluster').get('cluster_ip', None):
                run_subprocess_cmd([
                       "provisioner", "pillar_set",
                       "s3clients/ip",
                       f"{content.get('cluster').get('cluster_ip')}"])

        if 3 == int(number_of_nodes):
            run_subprocess_cmd([
                "provisioner", "pillar_set",
                "cluster/type", "\"3_node\""])
        elif 2 == int(number_of_nodes):
            run_subprocess_cmd([
                "provisioner", "pillar_set",
                "cluster/type", "\"dual\""])
        elif 1 == int(number_of_nodes):
            run_subprocess_cmd([
                "provisioner", "pillar_set",
                "cluster/type", "\"single\""])
        else:
            run_subprocess_cmd([
                "provisioner", "pillar_set",
                "cluster/type", "\"generic\""])

        if count > 0:
            raise ValueError(f"Node information for {count} node missing")

        logger.info("Pillar data updated Successfully.")
