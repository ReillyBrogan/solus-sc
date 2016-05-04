#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  This file is part of solus-sc
#
#  Copyright © 2014-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#

from gi.repository import Gtk, GLib, GdkPixbuf
from pisi.db.packagedb import PackageDB
from pisi.db.installdb import InstallDB

import pisi.api


PACKAGE_ICON_SECURITY = "software-update-urgent-symbolic"
# security-high-symbolic? doesn't stick out much..
PACKAGE_ICON_NORMAL = "software-update-available-symbolic"


class ScUpdatesView(Gtk.VBox):

    installdb = None
    packagedb = None
    tview = None

    def __init__(self):
        Gtk.VBox.__init__(self, 0)

        self.scroll = Gtk.ScrolledWindow(None, None)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.scroll.set_overlay_scrolling(False)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_property("kinetic-scrolling", True)
        self.pack_start(self.scroll, True, True, 0)

        self.tview = Gtk.TreeView()
        self.tview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        # Defugly
        self.tview.set_property("enable-grid-lines", False)
        self.tview.set_property("headers-visible", False)
        self.scroll.add(self.tview)

        # Install it?
        ren = Gtk.CellRendererToggle()
        ren.set_activatable(True)
        ren.connect('toggled', self.on_toggled)
        ren.set_padding(5, 5)
        column = Gtk.TreeViewColumn("Install?", ren, active=4, activatable=5)
        self.tview.append_column(column)

        # Type, image based.
        ren = Gtk.CellRendererPixbuf()
        ren.set_padding(5, 5)
        column = Gtk.TreeViewColumn("Type", ren, icon_name=3)
        self.tview.append_column(column)

        ren = Gtk.CellRendererText()
        ren.set_padding(5, 5)
        column = Gtk.TreeViewColumn("Name", ren, text=0)
        self.tview.append_column(column)

        # Installed version
        column = Gtk.TreeViewColumn("Version", ren, text=1)
        self.tview.append_column(column)

        # New version
        column = Gtk.TreeViewColumn("New version", ren, text=2)
        self.tview.append_column(column)

        # Update size
        ren = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Size", ren, text=7)
        self.tview.append_column(column)

        GLib.idle_add(self.init_view)

    def on_toggled(self, w, path):
        model = self.tview.get_model()
        model[path][4] = not model[path][4]

    def get_history_between(self, old_release, new):
        """ Get the history items between the old release and new pkg """
        ret = list()

        for i in new.history:
            if i.release <= old_release:
                continue
            ret.append(i)
        return ret

    def get_update_size(self, oldPkg, newPkg):
        """ Determine the update size for a given package """
        # FIXME: Check pisi config
        deltasEnabled = True

        pkgSize = newPkg.packageSize
        if not deltasEnabled:
            return pkgSize
        if not oldPkg:
            return pkgSize
        delt = newPkg.get_delta(int(oldPkg.release))
        """ No delta available. """
        if not delt:
            return pkgSize
        return delt.packageSize

    def init_view(self):
        # Need a shared context for these guys
        self.installdb = InstallDB()
        self.packagedb = PackageDB()

        model = Gtk.ListStore(str, str, str, str, bool, bool, int, str)

        # Expand with a plan operation to be up front about new deps
        upgrades = pisi.api.list_upgradable()
        model.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        for item in upgrades:
            new_pkg = self.packagedb.get_package(item)
            new_version = "%s-%s" % (str(new_pkg.version),
                                     str(new_pkg.release))
            pkg_name = str(new_pkg.name)
            old_pkg = None
            old_version = "Not installed"
            systemBase = False
            oldRelease = 0

            icon = PACKAGE_ICON_NORMAL
            if new_pkg.partOf == "system.base":
                systemBase = True

            if self.installdb.has_package(item):
                old_pkg = self.installdb.get_package(item)
                old_version = "%s-%s" % (str(old_pkg.version),
                                         str(old_pkg.release))
                oldRelease = int(old_pkg.release)

            histories = self.get_history_between(oldRelease, new_pkg)
            # Initial security update detection
            securities = [x for x in histories if x.type == "security"]
            if len(securities) > 0:
                icon = PACKAGE_ICON_SECURITY

            # Finally, actual size, and readable size
            pkgSize = self.get_update_size(old_pkg, new_pkg)
            dlSize = "%.1f %s" % pisi.util.human_readable_size(pkgSize)

            model.append([pkg_name, old_version, new_version,
                          icon, systemBase, not systemBase,
                          pkgSize, dlSize])
            while (Gtk.events_pending()):
                Gtk.main_iteration()

        """
        model.append(["security-update", "old", "new",
                      PACKAGE_ICON_SECURITY, False, True])
        model.append(["non-security-update", "old", "new",
                      PACKAGE_ICON_NORMAL, False, True])
        model.append(["system.base update", "old", "new",
                      PACKAGE_ICON_NORMAL, True, False])"""

        self.tview.set_model(model)
        return False
