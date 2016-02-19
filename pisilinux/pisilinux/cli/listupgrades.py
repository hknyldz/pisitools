# -*- coding:utf-8 -*-
#
# Copyright (C) 2005-2010, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import optparse

import gettext
__trans = gettext.translation('pisilinux', fallback=True)
_ = __trans.ugettext

import pisilinux.cli.command as command
import pisilinux.blacklist
import pisilinux.context as ctx
import pisilinux.api
import pisilinux.db

class ListUpgrades(command.Command, metaclass=command.autocommand):
    __doc__ = _("""List packages to be upgraded

Usage: list-upgrades

Lists the packages that will be upgraded.
""")

    def __init__(self, args):
        super(ListUpgrades, self).__init__(args)
        self.componentdb = pisilinux.db.componentdb.ComponentDB()
        self.installdb = pisilinux.db.installdb.InstallDB()

    name = ("list-upgrades", "lu")

    def options(self):
        group = optparse.OptionGroup(self.parser, _("list-upgrades options"))
        group.add_option("-l", "--long", action="store_true",
                               default=False, help=_("Show in long format"))
        group.add_option("-c", "--component", action="store",
                               default=None, help=_("List upgradable packages under given component"))
        group.add_option("-i", "--install-info", action="store_true",
                               default=False, help=_("Show detailed install info"))
        self.parser.add_option_group(group)

    def run(self):
        self.init(database = True, write = False)
        upgradable_pkgs = pisilinux.api.list_upgradable()

        component = ctx.get_option('component')
        if component:
            #FIXME: pisilinux api is insufficient to do this
            component_pkgs = self.componentdb.get_union_packages(component, walk=True)
            upgradable_pkgs = list(set(upgradable_pkgs) & set(component_pkgs))

        upgradable_pkgs = pisilinux.blacklist.exclude_from(upgradable_pkgs, ctx.const.blacklist)

        if not upgradable_pkgs:
            ctx.ui.info(_('No packages to upgrade.'))
            return

        upgradable_pkgs.sort()

        # Resize the first column according to the longest package name
        maxlen = max([len(_p) for _p in upgradable_pkgs])

        if self.options.install_info:
            ctx.ui.info(_('Package Name          |St|        Version|  Rel.|  Distro|             Date'))
            print('===========================================================================')
        for pkg in upgradable_pkgs:
            package = self.installdb.get_package(pkg)
            inst_info = self.installdb.get_info(pkg)
            if self.options.long:
                ctx.ui.info(package)
                print(inst_info)
            elif self.options.install_info:
                ctx.ui.info('%-20s |%s ' % (package.name, inst_info.one_liner()))
            else:
                package.name = package.name + ' ' * (maxlen - len(package.name))
                ctx.ui.info('%s - %s' % (package.name, str(package.summary)))
