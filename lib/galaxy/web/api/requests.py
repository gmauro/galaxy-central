"""
API operations on a sample tracking system.
"""
import logging, os, string, shutil, urllib, re, socket
from cgi import escape, FieldStorage
from galaxy import util, datatypes, jobs, web, util
from galaxy.web.base.controller import *
from galaxy.util.sanitize_html import sanitize_html
from galaxy.model.orm import *
from galaxy.util.bunch import Bunch

log = logging.getLogger( __name__ )

class RequestsController( BaseController ):
    update_types = Bunch( REQUEST = 'request_state', 
                          SAMPLE = 'sample_state',
                          SAMPLE_DATASET = 'sample_dataset_transfer_status' )
    update_type_values = [v[1] for v in update_types.items()]
    @web.expose_api
    def index( self, trans, **kwd ):
        """
        GET /api/requests
        Displays a collection (list) of sequencing requests.
        """
        # if admin user then return all requests
        if trans.user_is_admin():
            query = trans.sa_session.query( trans.app.model.Request )\
                                    .filter(  trans.app.model.Request.table.c.deleted == False )\
                                    .all()
        else:
            query = trans.sa_session.query( trans.app.model.Request )\
                                    .filter( and_( trans.app.model.Request.table.c.user_id == trans.user.id \
                                                   and trans.app.model.Request.table.c.deleted == False ) ) \
                                    .all()
        rval = []
        for request in query:
            item = request.get_api_value()
            item['url'] = url_for( 'requests', id=trans.security.encode_id( request.id ) )
            item['id'] = trans.security.encode_id( item['id'] )
            if trans.user_is_admin():
                item['user'] = request.user.email
            rval.append( item )
        return rval
    @web.expose_api
    def show( self, trans, id, **kwd ):
        """
        GET /api/requests/{encoded_request_id}
        Displays details of a sequencing request.
        """
        try:
            request_id = trans.security.decode_id( id )
        except TypeError:
            trans.response.status = 400
            return "Malformed  %s id ( %s ) specified, unable to decode." % ( update_type, str( id ) )
        try:
            request = trans.sa_session.query( trans.app.model.Request ).get( request_id )
        except:
            request = None
        if not request or not ( trans.user_is_admin() or request.user.id == trans.user.id ):
            trans.response.status = 400
            return "Invalid request id ( %s ) specified." % str( request_id )
        item = request.get_api_value()
        item['url'] = url_for( 'requests', id=trans.security.encode_id( request.id ) )
        item['id'] = trans.security.encode_id( item['id'] )
        item['user'] = request.user.email
        item['num_of_samples'] = len(request.samples)
        return item
    @web.expose_api
    def update( self, trans, id, key, payload, **kwd ):
        # TODO RC: move samples-related updates over to the samples api controller - I've added a new
        # update method there...
        """
        PUT /api/requests/{encoded_request_id}
        Updates a request state, sample state or sample dataset transfer status
        depending on the update_type
        """
        params = util.Params( kwd )
        update_type = None
        if 'update_type' not in payload:
            trans.response.status = 400
            return "Missing required 'update_type' parameter.  Please consult the API documentation for help."
        else:
            update_type = payload.pop( 'update_type' )
        if update_type not in self.update_type_values:
            trans.response.status = 400
            return "Invalid value for 'update_type' parameter ( %s ) specified.  Please consult the API documentation for help." % update_type
        try:
            request_id = trans.security.decode_id( id )
        except TypeError:
            trans.response.status = 400
            return "Malformed  request id ( %s ) specified, unable to decode." % str( id )
        try:
            request = trans.sa_session.query( trans.app.model.Request ).get( request_id )
        except:
            request = None
        if not request or not ( trans.user_is_admin() or request.user.id == trans.user.id ):
            trans.response.status = 400
            return "Invalid request id ( %s ) specified." % str( request_id )
        # check update type
        if update_type == 'request_state': 
            return self.__update_request_state( trans, encoded_request_id=id )
        elif update_type == 'sample_state': 
            return self.__update_sample_state( trans, request.type, **payload )
        elif update_type == 'sample_dataset_transfer_status': 
            # update sample_dataset transfer status
            return self.__update_sample_dataset_status( trans, **payload )
    def __update_request_state( self, trans, encoded_request_id ):
        requests_common_cntrller = trans.webapp.controllers['requests_common']
        status, output = requests_common_cntrller.update_request_state( trans, 
                                                                        cntrller='api', 
                                                                        request_id=encoded_request_id )
        return status, output
    def __update_sample_state( self, trans, request_type, **payload ):
        # only admin user may update sample state in Galaxy sample tracking
        if not trans.user_is_admin():
            trans.response.status = 403
            return "only an admin user may update sample state in Galaxy sample tracking."
        if 'sample_ids' not in payload or 'new_state' not in payload:
            trans.response.status = 400
            return "Missing one or more required parameters: 'sample_ids' and 'new_state'."
        sample_ids = payload.pop( 'sample_ids' )
        new_state_name = payload.pop( 'new_state' )
        comment = payload.get( 'comment', '' )
        # check if the new state is a valid sample state
        possible_states = request_type.states
        new_state = None
        for state in possible_states:
            if state.name == new_state_name:
                new_state = state
        if not new_state:
            trans.response.status = 400
            return "Invalid sample state requested ( %s )." % new_state
        requests_common_cntrller = trans.webapp.controllers['requests_common']
        status, output = requests_common_cntrller.update_sample_state(  trans, 
                                                                       cntrller='api', 
                                                                       sample_ids=sample_ids,
                                                                       new_state=new_state,
                                                                       comment=comment )
        return status, output
    def __update_sample_dataset_status( self, trans, **payload ):
        # only admin user may transfer sample datasets in Galaxy sample tracking
        if not trans.user_is_admin():
            trans.response.status = 403
            return "Only an admin user may transfer sample datasets in Galaxy sample tracking and thus update transfer status."
        if 'sample_dataset_ids' not in payload or 'new_status' not in payload:
            trans.response.status = 400
            return "Missing one or more required parameters: 'sample_dataset_ids' and 'new_status'."
        sample_dataset_ids = payload.pop( 'sample_dataset_ids' )
        new_status = payload.pop( 'new_status' )
        error_msg = payload.get( 'error_msg', '' )
        requests_admin_cntrller = trans.webapp.controllers['requests_admin']
        status, output = requests_admin_cntrller.update_sample_dataset_status( trans, 
                                                                               cntrller='api', 
                                                                               sample_dataset_ids=sample_dataset_ids,
                                                                               new_status=new_status,
                                                                               error_msg=error_msg )
        return status, output
