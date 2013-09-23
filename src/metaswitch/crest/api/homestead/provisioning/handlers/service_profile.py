# @file service_profile.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

import logging
from twisted.internet import defer
from telephus.cassandra.ttypes import NotFoundException
from metaswitch.crest.api._base import BaseHandler

JSON_PUBLIC_IDS = "public_ids"

def check_hierarchy(func):
    """Decorator that check that the Service Profile is a child of the Implicit
    Registration Set, and (if supplied) the Public ID is a child of the profile.
    """
    @defer.inlineCallbacks
    def wrapper(handler, irs_uuid, sp_uuid, public_id=None):

        try:
            parent_irs_uuid = yield ServiceProfile(sp_uuid).get_irs()
            if irs_uuid != parent_irs_uuid:
                handler.send_error(403, "Service Profile not a child of IRS")
                defer.returnValue(None)

            if public_id:
                parent_sp_uuid = yield PublicID(public_id).get_sp()
                if sp_uuid != parent_sp_uuid:
                    handler.send_error(
                                403, "Public ID not a child of Service Profile")
                    defer.returnValue(None)

            retval = func(handler, *pos_args, **kwd_args)
            defer.returnValue(retval)

        except NotFoundException:
            send_error(404)

    return wrapper


class AllServiceProfilesHandler(BaseHandler):
    @BaseHandler.requires_empty_body
    @defer.inlineCallbacks
    def post(self, irs_uuid):
        sp_uuid = yield ServiceProfile.create()
        self.set_header("Location", "/irs/%s/service_profile/%s" %
                                                            (irs_uuid, sp_uuid))
        self.set_status(201)
        self.finish()


class ServiceProfileHandler(BaseHandler):
    @BaseHandler.requires_empty_body
    @check_hierarchy
    @defer.inlineCallbacks
    def delete(self, irs_uuid, sp_uuid):
        yield ServiceProfile(sp_uuid).delete()
        self.finish()


class SPAllPublicIDsHandler(BaseHandler):
    @check_hierarchy
    @defer.inlineCallbacks
    def get(self, irs_uuid, sp_uuid):
        public_ids = yield ServiceProfile(sp_uuid).get_public_ids()
        self.send_json({JSON_PUBLIC_IDS: public_ids})


class SPPublicIDHandler(BaseHandler):
    @check_hierarchy
    @defer.inlineCallbacks
    def put(self, irs_uuid, sp_uuid, public_id):
        try:
            xml = self.request.body
            xml_root = ET.from_string(xml)
            xml_public_id = xml_root.find("Identity").text

            if public_id == xml_public_id:
                yield PublicID(public_id).put_publicidentity(xml)
            else:
                self.send_error(403, "Incorrect XML Identity")
        except:
            self.send_error(400, "Badly formed XML")

    @check_hierarchy
    @defer.inlineCallbacks
    def delete(self, irs_uuid, sp_uuid, public_id):
        PublicID(public_id).delete()
        self.finish()


class SPFilterCriteriaHandler(BaseHandler):
    @check_hierarchy
    @defer.inlineCallbacks
    def get(self, irs_uuid, sp_uuid):
        try:
            ifc = yield ServiceProfile(sp_uuid).get_ifc()
            self.write(ifc)
            self.finish()
        except NotFoundException:
            self.send_error(404)

    @check_hierarchy
    @defer.inlineCallbacks
    def put(self, irs_uuid, sp_uuid):
        xml_body = self.request.body

        if self.request.body:
            yield ServiceProfile(sp_uuid).update_ifc(xml_body)
        else:
            self.send_error(400, "Body is empty")