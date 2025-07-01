#!/bin/bash

IFACE=$(ip link show | awk -F: '$0 !~ "lo" {print $2;exit}' |  tr -d "[:blank:]")


if grep -q 'Debian\|Ubuntu' /etc/*-release ; then

        cat << EOF > /etc/network/interfaces
# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug $IFACE
iface $IFACE inet dhcp

EOF

        ip link set $IFACE up
        dhclient

        exit 0
else
        service network stop
        find /etc/sysconfig/network-scripts/ -type f -not \( -name 'ifup*' -or -name 'ifdown*' -or -name 'init*' -or -name 'network*' -or -name 'ifcfg-lo' \) -delete
        cat << EOF > /etc/sysconfig/network-scripts/ifcfg-${IFACE}
DEVICE=${IFACE}
BOOTPROTO=dhcp
ONBOOT=yes
EOF

        cat << EOF > /etc/sysconfig/network
NETWORKING=yes
EOF

        service network start

fi

