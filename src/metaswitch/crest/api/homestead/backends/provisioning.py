# @file provisioning.py.py
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

from twisted.internet import defer

from .backend import Backend
from metaswitch.crest import settings

class ProvisioningBackend(Backend):
    """
    Backend providing access to the homestead provisioning database.

    When new data is provisioned the cache is automatically updated at the same
    time (and the cached data never expires). As such all methods on this class
    simply return None).
    """

    def __init__(self, cache):
        self._cache = cache

    @staticmethod
    def sync_return(value):
        """Synchronously return a value from a function that is called as if it
        returns asynchrnously.

        In twisted asynchronous functions return a deferred.  There is therfore
        an issue if a function implements an asynchronous interface but wants to
        return synchronously.  The solve this, we create a new deferred, and
        immediately pass it the value to return.  When this reaches the reactor
        it will get processed immediately."""
        d = defer.Deferred()
        d.callback(value)
        return d

    def get_av(self, private_id, public_id, authtype, autn):
        return self.sync_return(None)

    def get_ims_subscription(self, public_id, private_id):
        return self.sync_return(None)

    # Return the sprout hostname on S-CSCF lookups when no HSS is configured
    def get_registration_status(self, private_id, public_id, visited_network, auth_type):
        return self.sync_return({"result-code": 2001, "scscf": "sip:%s:%d" % 
                                 (settings.SPROUT_HOSTNAME, settings.SPROUT_PORT)})

    def get_location_information(self, public_id, originating, auth_type):
        return self.sync_return({"result-code": 2001, "scscf": "sip:%s:%d" % 
                                 (settings.SPROUT_HOSTNAME, settings.SPROUT_PORT)})

