# @file private.py
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
import json

from twisted.internet import defer
from telephus.cassandra.ttypes import NotFoundException
from metaswitch.crest.api.base import BaseHandler
from ..models import PrivateID

_log = logging.getLogger("crest.api.homestead.cache")

JSON_DIGEST_HA1 = "digest_ha1"
JSON_REALM = "realm"
JSON_ASSOC_IRS = "associated_implicit_registration_sets"
JSON_ASSOC_PUBLIC_IDS = "associated_public_ids"


class PrivateHandler(BaseHandler):
    @defer.inlineCallbacks
    def get(self, private_id):
        try:
            (digest_ha1, realm) = yield PrivateID(private_id).get_digest()
            body = {JSON_DIGEST_HA1: digest_ha1, JSON_REALM: realm}
            self.send_json(body)

        except NotFoundException:
            self.send_error(404)

    @defer.inlineCallbacks
    def put(self, private_id):
        body = self.request.body
        if body:
            try:
                obj = json.loads(body)
            except ValueError:
                self.send_error(400, "Invalid JSON")

            try:
                digest_ha1 = obj[JSON_DIGEST_HA1]
                realm = obj.get(JSON_REALM) # may be absent
                yield PrivateID(private_id).put_digest(digest_ha1, realm)
                self.finish()
            except KeyError:
                self.send_error(400, "Missing %s key" & JSON_DIGEST_HA1)
        else:
            self.send_error(400, "Empty body")

    @defer.inlineCallbacks
    def delete(self, private_id):
        yield PrivateID(private_id).delete()
        self.finish()


class PrivateAllIrsHandler(BaseHandler):
    @defer.inlineCallbacks
    def get(self, private_id):
        try:
            irses = yield PrivateID(private_id).get_irses()
            self.send_json({JSON_ASSOC_IRS: irses})

        except NotFoundException:
            self.send_error(404)


class PrivateOneIrsHandler(BaseHandler):
    @BaseHandler.requires_empty_body
    @defer.inlineCallbacks
    def put(self, private_id, irs_uuid):
        try:
            yield PrivateID(private_id).associate_irs(irs_uuid)
            self.finish()
        except NotFoundException:
            self.send_error(404)

    @BaseHandler.requires_empty_body
    @defer.inlineCallbacks
    def delete(self, private_id, irs_uuid):
        try:
            yield PrivateID(private_id).dissociate_irs(irs_uuid)
            self.finish()
        except NotFoundException:
            self.send_error(404)


class PrivateAllPublicIdsHandler(BaseHandler):
    @defer.inlineCallbacks
    def get(self, private_id):
        try:
            public_ids = yield PrivateID(private_id).get_public_ids()
            self.send_json({JSON_ASSOC_PUBLIC_IDS: public_ids})
        except NotFoundException:
            self.send_error(404)
