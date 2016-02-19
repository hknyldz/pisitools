# -*- coding:utf-8 -*-
#
# Copyright (C) 2005 - 2007, TUBITAK/UEKAE
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
import pisilinux.context as ctx
import pisilinux.api

class RebuildDb(command.Command, metaclass=command.autocommand):
    __doc__ = _("""Rebuild Databases

Usage: rebuilddb [ <package1> <package2> ... <packagen> ]

Rebuilds the pisilinux databases

If package specs are given, they should be the names of package
dirs under /var/lib/pisilinux
""")

    def __init__(self, args):
        super(RebuildDb, self).__init__(args)

    name = ("rebuild-db", "rdb")

    def options(self):

        group = optparse.OptionGroup(self.parser, _("rebuild-db options"))

        group.add_option("-f", "--files", action="store_true",
                               default=False, help=_("Rebuild files database"))

        self.parser.add_option_group(group)

    def run(self):
        self.init(database=True)
        if ctx.ui.confirm(_('Rebuild pisilinux databases?')):
            pisilinux.api.rebuild_db()
