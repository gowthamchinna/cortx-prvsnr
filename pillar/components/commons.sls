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

commons:
  health-map:
    path: /opt/seagate/cortx_configs/healthmap/
    file: healthmap-schema.json
  version:
    consul: 1.9.1-1
    opendistroforelasticsearch: 1.12.0
    erlang: latest
    opendistroforelasticsearch-kibana: 1.12.0-1
    nodejs: v12.13.0
    rabbitmq: latest
    rsyslog: 8.40.0-1.el7
    rsyslog-elasticsearch: 8.40.0-1.el7
    rsyslog-mmjsonparse: 8.40.0-1.el7
    kafka: 2.13-2.7.0
    cortx:
      # TODO
      # - update install.sls files for components
      # - think about generic logic and sls macros, e.g.:
      #   - define map: pkg - dependencies
      #   - define map: component - pkgs
      #   - loop over required and install them along with deps (e.g. using requisites)
      #   - loop over optional and install if they are available (again - with deps)
      cortx-csm_agent: latest
      cortx-csm_web: latest
      cortx-ha: latest
      cortx-hare: latest
      cortx-motr: latest
      cortx-prvsnr: latest
      python36-cortx-prvsnr: latest
      cortx-s3server: latest
      cortx-s3iamcli: latest
      cortx-sspl: latest
      cortx-sspl-test: latest
      uds-pyi: latest
      cortx-cli: latest
  sw_data:
    provisioner:
      base_sls: components.provisioner
      mini: /opt/seagate/cortx/provisioner/conf/setup.yaml
    utils:
      base_sls: components.cortx_utils
      mini: /opt/seagate/cortx/utils/conf/setup.yaml
    motr:
      base_sls: components.motr
      mini: /opt/seagate/cortx/motr/conf/setup.yaml
    s3:
      base_sls: components.s3server
      mini: /opt/seagate/cortx/s3/conf/setup.yaml
    hare:
      base_sls: components.hare
      mini: /opt/seagate/cortx/hare/conf/setup.yaml
    ha:
      base_sls: components.ha.cortx-ha
      mini: /opt/seagate/cortx/ha/conf/setup.yaml
    sspl:
      base_sls: components.sspl
      mini: /opt/seagate/cortx/sspl/conf/setup.yaml
    uds:
      base_sls: components.uds
      mini: /opt/seagate/cortx/uds/conf/setup.yaml
    csm:
      base_sls: components.csm
      mini: /opt/seagate/cortx/csm/conf/setup.yaml
      mini_sw:
        - csm
        - usl
    # usl:
    #   base_sls: null
    #   mini: /opt/seagate/cortx/csm/conf/setup.yaml
    #   mini_sw:
    #     - csm
    #     - usl
