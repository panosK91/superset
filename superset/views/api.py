# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from typing import Any, TYPE_CHECKING

import simplejson as json
from flask import request, jsonify
from flask_appbuilder import expose
from flask_appbuilder.api import rison
from flask_appbuilder.security.decorators import has_access_api
from flask_babel import lazy_gettext as _

from superset import db, event_logger
from superset.commands.chart.exceptions import (
    TimeRangeAmbiguousError,
    TimeRangeParseFailError,
)
from superset.legacy import update_time_range
from superset.models.slice import Slice
from superset.superset_typing import FlaskResponse
from superset.utils import core as utils
from superset.utils.date_parser import get_since_until
from superset.views.base import api, BaseSupersetView, handle_api_exception

if TYPE_CHECKING:
    from superset.common.query_context_factory import QueryContextFactory

get_time_range_schema = {"type": "string"}

# Model for User Preference
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id = Column(Integer, primary_key=True)
    navbar_color = Column(String(7), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def __init__(self, navbar_color):
        self.navbar_color = navbar_color
# End Model for User Preference

class Api(BaseSupersetView):
    query_context_factory = None

    @event_logger.log_this
    @api
    @handle_api_exception
    @has_access_api
    @expose("/v1/query/", methods=("POST",))
    def query(self) -> FlaskResponse:
        """
        Take a query_obj constructed in the client and returns payload data response
        for the given query_obj.

        raises SupersetSecurityException: If the user cannot access the resource
        """
        query_context = self.get_query_context_factory().create(
            **json.loads(request.form["query_context"])
        )
        query_context.raise_for_access()
        result = query_context.get_payload()
        payload_json = result["queries"]
        return json.dumps(
            payload_json, default=utils.json_int_dttm_ser, ignore_nan=True
        )

    @event_logger.log_this
    @api
    @handle_api_exception
    @has_access_api
    @expose("/v1/form_data/", methods=("GET",))
    def query_form_data(self) -> FlaskResponse:
        """
        Get the form_data stored in the database for existing slice.
        params: slice_id: integer
        """
        form_data = {}
        if slice_id := request.args.get("slice_id"):
            slc = db.session.query(Slice).filter_by(id=slice_id).one_or_none()
            if slc:
                form_data = slc.form_data.copy()

        update_time_range(form_data)

        return self.json_response(form_data)

    @api
    @handle_api_exception
    @has_access_api
    @rison(get_time_range_schema)
    @expose("/v1/time_range/", methods=("GET",))
    def time_range(self, **kwargs: Any) -> FlaskResponse:
        """Get actual time range from human-readable string or datetime expression."""
        time_range = kwargs["rison"]
        try:
            since, until = get_since_until(time_range)
            result = {
                "since": since.isoformat() if since else "",
                "until": until.isoformat() if until else "",
                "timeRange": time_range,
            }
            return self.json_response({"result": result})
        except (ValueError, TimeRangeParseFailError, TimeRangeAmbiguousError) as error:
            error_msg = {"message": _("Unexpected time range: %(error)s", error=error)}
            return self.json_response(error_msg, 400)

    def get_query_context_factory(self) -> QueryContextFactory:
        if self.query_context_factory is None:
            # pylint: disable=import-outside-toplevel
            from superset.common.query_context_factory import QueryContextFactory

            self.query_context_factory = QueryContextFactory()
        return self.query_context_factory

    # New API to Save Navbar Color
    @event_logger.log_this
    @api
    @handle_api_exception
    @has_access_api
    @expose("/v1/readpostgres", methods=("POST",))
    def save_navbar_color(self) -> FlaskResponse:
        """
        Save the custom navbar color preference to the database.
        Expects a JSON payload: {"navbarColor": "#455a64"}
        """
        data = request.get_json()
        navbar_color = data.get("navbarColor")
        if not navbar_color:
            return self.json_response({"error": "Navbar color not provided"}, 400)
        try:
            new_pref = UserPreference(navbar_color=navbar_color)
            db.session.add(new_pref)
            db.session.commit()
            return self.json_response({
                "message": "Navbar color preference saved successfully.",
                "navbar_color": navbar_color,
            }, 200)
        except Exception as e:
            db.session.rollback()
            return self.json_response({"error": str(e)}, 500)
    # End API to Save Navbar Color

