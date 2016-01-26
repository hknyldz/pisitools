#!/usr/bin/python
# -*- coding: utf-8 -*-

import dbus
import time

bus = dbus.SystemBus()

obj = bus.get_object('org.pisilinux.comar3', '/', introspect=False)
obj.setLocale('tr', dbus_interface='org.pisilinux.comar3')

obj = bus.get_object('org.pisilinux.comar3', '/package/apache', introspect=False)
print((obj.info(dbus_interface='org.pisilinux.comar3.System.Service', timeout=60)))
