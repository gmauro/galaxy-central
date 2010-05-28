import tarfile
from galaxy.web.base.controller import *
from galaxy.webapps.community import model
from galaxy.model.orm import *
from galaxy.web.framework.helpers import time_ago, iff, grids
from galaxy.web.form_builder import SelectField
import logging
log = logging.getLogger( __name__ )

class CommonController( BaseController ):
    @web.expose
    def edit_tool( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_tools',
                                                              message='Select a tool to edit',
                                                              status='error' ) )
        tool = get_tool( trans, id )
        if params.get( 'edit_tool_button', False ):
            if params.get( 'in_categories', False ):
                in_categories = [ trans.sa_session.query( trans.app.model.Category ).get( x ) for x in util.listify( params.in_categories ) ]
                trans.app.security_agent.set_entity_category_associations( tools=[ tool ], categories=in_categories )
            else:
                # There must not be any categories associated with the tool
                trans.app.security_agent.set_entity_category_associations( tools=[ tool ], categories=[] )
            user_description = util.restore_text( params.get( 'user_description', '' ) )
            if user_description:
                tool.user_description = user_description
            else:
                tool.user_description = ''
            trans.sa_session.add( tool )
            trans.sa_session.flush()
            message="Tool '%s' description and category associations have been saved" % tool.name
            return trans.response.send_redirect( web.url_for( controller='common',
                                                              action='edit_tool',
                                                              cntrller=cntrller,
                                                              id=id,
                                                              message=message,
                                                              status='done' ) )
        elif params.get( 'approval_button', False ):
            if params.get( 'in_categories', False ):
                in_categories = [ trans.sa_session.query( trans.app.model.Category ).get( x ) for x in util.listify( params.in_categories ) ]
                trans.app.security_agent.set_entity_category_associations( tools=[ tool ], categories=in_categories )
            else:
                # There must not be any categories associated with the tool
                trans.app.security_agent.set_entity_category_associations( tools=[ tool ], categories=[] )
            user_description = util.restore_text( params.get( 'user_description', '' ) )
            if user_description:
                tool.user_description = user_description
            else:
                tool.user_description = ''
            trans.sa_session.add( tool )
            trans.sa_session.flush()
            # Move the state from NEW to WAITING
            event = trans.app.model.Event( state=trans.app.model.Tool.states.WAITING )
            tea = trans.app.model.ToolEventAssociation( tool, event )
            trans.sa_session.add_all( ( event, tea ) )
            trans.sa_session.flush()
            message = "Tool '%s' has been submitted for approval and can no longer be modified" % ( tool.name )
            return trans.response.send_redirect( web.url_for( controller='common',
                                                              action='view_tool',
                                                              cntrller=cntrller,
                                                              id=id,
                                                              message=message,
                                                              status='done' ) )
        in_categories = []
        out_categories = []
        for category in get_categories( trans ):
            if category in [ x.category for x in tool.categories ]:
                in_categories.append( ( category.id, category.name ) )
            else:
                out_categories.append( ( category.id, category.name ) )
        return trans.fill_template( '/webapps/community/tool/edit_tool.mako',
                                    cntrller=cntrller,
                                    tool=tool,
                                    id=id,
                                    in_categories=in_categories,
                                    out_categories=out_categories,
                                    message=message,
                                    status=status )
    @web.expose
    def view_tool( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_tools',
                                                              message='Select a tool to view',
                                                              status='error' ) )
        tool = get_tool( trans, id )
        categories = [ tca.category for tca in tool.categories ]
        tool_file_contents = tarfile.open( tool.file_name, 'r' ).getnames()
        versions = get_versions( trans, tool )
        return trans.fill_template( '/webapps/community/tool/view_tool.mako',
                                    tool=tool,
                                    tool_file_contents=tool_file_contents,
                                    versions=versions,
                                    categories=categories,
                                    cntrller=cntrller,
                                    message=message,
                                    status=status )
    @web.expose
    def delete_tool( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            message='Select a tool to delete'
            status='error'
        else:
            tool = get_tool( trans, id )
            # Create a new event
            event = trans.model.Event( state=trans.model.Tool.states.DELETED )
            # Flush so we can get an event id
            trans.sa_session.add( event )
            trans.sa_session.flush()
            # Associate the tool with the event
            tea = trans.model.ToolEventAssociation( tool=tool, event=event )
            # Delete the tool, keeping state for categories, events and versions
            tool.deleted = True
            trans.sa_session.add_all( ( tool, tea ) )
            trans.sa_session.flush()
            # TODO: What if the tool has versions, should they all be deleted?
            message = "Tool '%s' has been marked deleted"
            status = 'done'
        return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                          action='browse_tools',
                                                          message=message,
                                                          status=status ) )
    @web.expose
    def upload_new_tool_version( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_tools',
                                                              message='Select a tool to to upload a new version',
                                                              status='error' ) )
        tool = get_tool( trans, id )
        return trans.response.send_redirect( web.url_for( controller='upload',
                                                          action='upload',
                                                          message=message,
                                                          status=status,
                                                          replace_id=id ) )
    @web.expose
    def browse_category( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_categories',
                                                              message='Select a category',
                                                              status='error' ) )
        category = get_category( trans, id )
        # If request came from the tool controller, then we need to filter by the state of the
        # tool in addition to the category.
        if cntrller == 'tool':
            ids = get_approved_tools( trans, category=category )
        else:
            # If request came from the admin controller, we don't filter on tool state.
            ids = [ tca.tool.id for tca in category.tools ]
        if not ids:
            ids = 'none'
        return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                          action='browse_tools',
                                                          ids=ids ) )
    @web.expose
    def browse_tools_by_user( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_tools',
                                                              message='Select a user',
                                                              status='error' ) )
        user = get_user( trans, id )
        # If request came from the tool controller, then we need to filter by the state of the
        # tool if the user is not viewing his own tools
        if cntrller == 'tool':
            ids = get_tools_uploaded_by( trans, user )
        else:
            # If request came from the admin controller we don't filter on tool state.
            ids = [ tool.id for tool in user.tools ]
        if not ids:
            ids = 'none'
        if cntrller == 'tool' and user != trans.user:
            # If the user is browsing someone else's tools, then we do not want to
            # use the BrowseToolsByUser list grid since it includes a status column.
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_tools',
                                                              ids=ids ) ) 
        return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                          action='browse_tools_by_user',
                                                          ids=ids ) )

## ---- Utility methods -------------------------------------------------------

def get_versions( trans, tool ):
    versions = [tool]
    this_tool = tool
    while tool.newer_version:
        versions.insert( 0, tool.newer_version )
        tool = tool.newer_version
    tool = this_tool
    while tool.older_version:
        versions.append( tool.older_version[0] )
        tool = tool.older_version[0]
    return versions
def get_categories( trans ):
    """Get all categories from the database"""
    return trans.sa_session.query( trans.model.Category ) \
                           .filter( trans.model.Category.table.c.deleted==False ) \
                           .order_by( trans.model.Category.table.c.name ).all()
def get_unassociated_categories( trans, obj ):
    """Get all categories from the database that are not associated with obj"""
    # TODO: we currently assume we are setting a tool category, so this method may need
    # tweaking if / when we decide to set history or workflow categories
    associated_categories = []
    for tca in obj.categories:
        associated_categories.append( tca.category )
    categories = []
    for category in get_categories( trans ):
        if category not in associated_categories:
            categories.append( category )
    return categories
def get_category( trans, id ):
    return trans.sa_session.query( trans.model.Category ).get( trans.security.decode_id( id ) )
def set_categories( trans, obj, category_ids, delete_existing_assocs=True ):
    if delete_existing_assocs:
        for assoc in obj.categories:
            trans.sa_session.delete( assoc )
            trans.sa_session.flush()
    for category_id in category_ids:
        # TODO: we currently assume we are setting a tool category, so this method may need
        # tweaking if / when we decide to set history or workflow categories
        category = trans.sa_session.query( trans.model.Category ).get( category_id )
        obj.categories.append( trans.model.ToolCategoryAssociation( obj, category ) )
def get_tool( trans, id ):
    return trans.sa_session.query( trans.model.Tool ).get( trans.app.security.decode_id( id ) )
def get_tools( trans ):
    # Return only the latest version of each tool
    return trans.sa_session.query( trans.model.Tool ) \
                           .filter( trans.model.Tool.newer_version_id == None ) \
                           .order_by( trans.model.Tool.name )
def get_approved_tools( trans, category=None ):
    # TODO: write this as a query using eagerload - will be much faster.
    ids = []
    if category:
        # Return only the approved tools in the category
        for tca in category.tools:
            tool = tca.tool
            if tool.is_approved():
                ids.append( tool.id )
    else:
        # Return all approved tools
        for tool in get_tools( trans ):
            if tool.is_approved():
                ids.append( tool.id )
    return ids
def get_tools_uploaded_by( trans, user ):
    # TODO: write this as a query using eagerload - will be much faster.
    ids = []
    if trans.user == user:
        # If the current user is browsing his own tools, then don't filter on state
        ids = [ tool.id for tool in user.tools ]
    else:
        # The current user is viewing tools uploaded by another user, so show only approved tools
        for tool in user.active_tools:
            if tool.is_approved():
                ids.append( tool.id )
    return ids
def get_event( trans, id ):
    return trans.sa_session.query( trans.model.Event ).get( trans.security.decode_id( id ) )
def get_user( trans, id ):
    return trans.sa_session.query( trans.model.User ).get( trans.security.decode_id( id ) )
