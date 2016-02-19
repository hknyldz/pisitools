# -*- coding:utf-8 -*-
#
# Copyright (C) 2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import optparse

import gettext
__trans = gettext.translation('pisilinux', fallback=True)
_ = __trans.ugettext

import pisilinux.cli.command as command
import pisilinux.context as ctx
import pisilinux.api

class Fetch(command.Command, metaclass=command.autocommand):
    __doc__ = _("""Fetch a package

Usage: fetch [<package1> <package2> ... <packagen>]

<packagei>: package name

Downloads the given pisilinux packages to working directory
""")

    def __init__(self,args):
        super(Fetch, self).__init__(args)

    name = ("fetch", "fc")

    def options(self):
        group = optparse.OptionGroup(self.parser, _("fetch options"))
        self.add_options(group)
        self.parser.add_option_group(group)

    def add_options(self, group):
        group.add_option("-o", "--output-dir", action="store", default=os.path.curdir,
                               help=_("Output directory for the fetched packages"))

    def run(self):
        self.init(database = False, write = False)

        if not self.args:
            self.help()
            return

        pisilinux.api.fetch(self.args, ctx.config.options.output_dir)
