from galaxy.web.base.controller import *
from galaxy.webapps.community import model
from galaxy.model.orm import *
from galaxy.web.framework.helpers import time_ago, iff, grids
from common import ToolListGrid, CategoryListGrid, get_category, get_tools, get_event, get_tool, get_versions
import logging
log = logging.getLogger( __name__ )

class UserListGrid( grids.Grid ):
    # TODO: move this to an admin_common controller since it is virtually the same
    # in the galaxy webapp.  NOTE the additional ToolsColumn in this grid though...
    class UserLoginColumn( grids.TextColumn ):
        def get_value( self, trans, grid, user ):
            return user.email
    class UserNameColumn( grids.TextColumn ):
        def get_value( self, trans, grid, user ):
            if user.username:
                return user.username
            return 'not set'
    class GroupsColumn( grids.GridColumn ):
        def get_value( self, trans, grid, user ):
            if user.groups:
                return len( user.groups )
            return 0
    class RolesColumn( grids.GridColumn ):
        def get_value( self, trans, grid, user ):
            if user.roles:
                return len( user.roles )
            return 0
    class ExternalColumn( grids.GridColumn ):
        def get_value( self, trans, grid, user ):
            if user.external:
                return 'yes'
            return 'no'
    class LastLoginColumn( grids.GridColumn ):
        def get_value( self, trans, grid, user ):
            if user.galaxy_sessions:
                return self.format( user.galaxy_sessions[ 0 ].update_time )
            return 'never'
    class StatusColumn( grids.GridColumn ):
        def get_value( self, trans, grid, user ):
            if user.purged:
                return "purged"
            elif user.deleted:
                return "deleted"
            return ""
    class ToolsColumn( grids.TextColumn ):
        def get_value( self, trans, grid, user ):
            return len( user.tools )
    class EmailColumn( grids.GridColumn ):
        def filter( self, trans, user, query, column_filter ):
            if column_filter == 'All':
                return query
            return query.filter( and_( model.Tool.table.c.user_id == model.User.table.c.id,
                                       model.User.table.c.email == column_filter ) )
    # Grid definition
    webapp = "community"
    title = "Users"
    model_class = model.User
    template='/admin/user/grid.mako'
    default_sort_key = "email"
    columns = [
        UserLoginColumn( "Email",
                     key="email",
                     model_class=model.User,
                     link=( lambda item: dict( operation="information", id=item.id, webapp="community" ) ),
                     attach_popup=True,
                     filterable="advanced" ),
        UserNameColumn( "User Name",
                        key="username",
                        model_class=model.User,
                        attach_popup=False,
                        filterable="advanced" ),
        GroupsColumn( "Groups", attach_popup=False ),
        RolesColumn( "Roles", attach_popup=False ),
        ExternalColumn( "External", attach_popup=False ),
        LastLoginColumn( "Last Login", format=time_ago ),
        StatusColumn( "Status", attach_popup=False ),
        ToolsColumn( "Uploaded Tools",
                     model_class=model.User,
                     link=( lambda item: dict( operation="tools_by_user", id=item.id, webapp="community" ) ),
                     attach_popup=False,
                     filterable="advanced" ),
        # Columns that are valid for filtering but are not visible.
        EmailColumn( "Email",
                     key="email",
                     model_class=model.User,
                     visible=False )
    ]
    columns.append( grids.MulticolFilterColumn( "Search", 
                                                cols_to_filter=[ columns[0], columns[1] ], 
                                                key="free-text-search",
                                                visible=False,
                                                filterable="standard" ) )
    global_actions = [
        grids.GridAction( "Create new user",
                          dict( controller='admin', action='users', operation='create', webapp="community" ) )
    ]
    operations = [
        grids.GridOperation( "Manage Roles and Groups",
                             condition=( lambda item: not item.deleted ),
                             allow_multiple=False,
                             url_args=dict( webapp="community", action="manage_roles_and_groups_for_user" ) ),
        grids.GridOperation( "Reset Password",
                             condition=( lambda item: not item.deleted ),
                             allow_multiple=True,
                             allow_popup=False,
                             url_args=dict( webapp="community", action="reset_user_password" ) )
    ]
    standard_filters = [
        grids.GridColumnFilter( "Active", args=dict( deleted=False ) ),
        grids.GridColumnFilter( "Deleted", args=dict( deleted=True, purged=False ) ),
        grids.GridColumnFilter( "Purged", args=dict( purged=True ) ),
        grids.GridColumnFilter( "All", args=dict( deleted='All' ) )
    ]
    num_rows_per_page = 50
    preserve_state = False
    use_paging = True
    def get_current_item( self, trans, **kwargs ):
        return trans.user

class RoleListGrid( grids.Grid ):
    # TODO: move this to an admin_common controller since it is virtually the same
    # in the galaxy webapp.
    class NameColumn( grids.TextColumn ):
        def get_value( self, trans, grid, role ):
            return role.name
    class DescriptionColumn( grids.TextColumn ):
        def get_value( self, trans, grid, role ):
            if role.description:
                return role.description
            return ''
    class TypeColumn( grids.TextColumn ):
        def get_value( self, trans, grid, role ):
            return role.type
    class StatusColumn( grids.GridColumn ):
        def get_value( self, trans, grid, role ):
            if role.deleted:
                return "deleted"
            return ""
    class GroupsColumn( grids.GridColumn ):
        def get_value( self, trans, grid, role ):
            if role.groups:
                return len( role.groups )
            return 0
    class UsersColumn( grids.GridColumn ):
        def get_value( self, trans, grid, role ):
            if role.users:
                return len( role.users )
            return 0

    # Grid definition
    webapp = "community"
    title = "Roles"
    model_class = model.Role
    template='/admin/dataset_security/role/grid.mako'
    default_sort_key = "name"
    columns = [
        NameColumn( "Name",
                    key="name",
                    link=( lambda item: dict( operation="Manage users and groups", id=item.id, webapp="community" ) ),
                    model_class=model.Role,
                    attach_popup=True,
                    filterable="advanced" ),
        DescriptionColumn( "Description",
                           key='description',
                           model_class=model.Role,
                           attach_popup=False,
                           filterable="advanced" ),
        TypeColumn( "Type",
                    key='type',
                    model_class=model.Role,
                    attach_popup=False,
                    filterable="advanced" ),
        GroupsColumn( "Groups", attach_popup=False ),
        UsersColumn( "Users", attach_popup=False ),
        StatusColumn( "Status", attach_popup=False ),
        # Columns that are valid for filtering but are not visible.
        grids.DeletedColumn( "Deleted",
                             key="deleted",
                             visible=False,
                             filterable="advanced" )
    ]
    columns.append( grids.MulticolFilterColumn( "Search", 
                                                cols_to_filter=[ columns[0], columns[1], columns[2] ], 
                                                key="free-text-search",
                                                visible=False,
                                                filterable="standard" ) )
    global_actions = [
        grids.GridAction( "Add new role",
                          dict( controller='admin', action='roles', operation='create', webapp="community" ) )
    ]
    operations = [ grids.GridOperation( "Rename",
                                        condition=( lambda item: not item.deleted ),
                                        allow_multiple=False,
                                        url_args=dict( webapp="community", action="rename_role" ) ),
                   grids.GridOperation( "Delete",
                                        condition=( lambda item: not item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="mark_role_deleted" ) ),
                   grids.GridOperation( "Undelete",
                                        condition=( lambda item: item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="undelete_role" ) ),
                   grids.GridOperation( "Purge",
                                        condition=( lambda item: item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="purge_role" ) ) ]
    standard_filters = [
        grids.GridColumnFilter( "Active", args=dict( deleted=False ) ),
        grids.GridColumnFilter( "Deleted", args=dict( deleted=True ) ),
        grids.GridColumnFilter( "All", args=dict( deleted='All' ) )
    ]
    num_rows_per_page = 50
    preserve_state = False
    use_paging = True
    def apply_query_filter( self, trans, query, **kwd ):
        return query.filter( model.Role.type != model.Role.types.PRIVATE )

class GroupListGrid( grids.Grid ):
    # TODO: move this to an admin_common controller since it is virtually the same
    # in the galaxy webapp.
    class NameColumn( grids.TextColumn ):
        def get_value( self, trans, grid, group ):
            return group.name
    class StatusColumn( grids.GridColumn ):
        def get_value( self, trans, grid, group ):
            if group.deleted:
                return "deleted"
            return ""
    class RolesColumn( grids.GridColumn ):
        def get_value( self, trans, grid, group ):
            if group.roles:
                return len( group.roles )
            return 0
    class UsersColumn( grids.GridColumn ):
        def get_value( self, trans, grid, group ):
            if group.members:
                return len( group.members )
            return 0

    # Grid definition
    webapp = "community"
    title = "Groups"
    model_class = model.Group
    template='/admin/dataset_security/group/grid.mako'
    default_sort_key = "name"
    columns = [
        NameColumn( "Name",
                    #key="name",
                    link=( lambda item: dict( operation="Manage users and roles", id=item.id, webapp="community" ) ),
                    model_class=model.Group,
                    attach_popup=True
                    #filterable="advanced"
                    ),
        UsersColumn( "Users", attach_popup=False ),
        RolesColumn( "Roles", attach_popup=False ),
        StatusColumn( "Status", attach_popup=False ),
        # Columns that are valid for filtering but are not visible.
        grids.DeletedColumn( "Deleted",
                             key="deleted",
                             visible=False,
                             filterable="advanced" )
    ]
    columns.append( grids.MulticolFilterColumn( "Search", 
                                                cols_to_filter=[ columns[0], columns[1], columns[2] ], 
                                                key="free-text-search",
                                                visible=False,
                                                filterable="standard" ) )
    global_actions = [
        grids.GridAction( "Add new group",
                          dict( controller='admin', action='groups', operation='create', webapp="community" ) )
    ]
    operations = [ grids.GridOperation( "Rename",
                                        condition=( lambda item: not item.deleted ),
                                        allow_multiple=False,
                                        url_args=dict( webapp="community", action="rename_group" ) ),
                   grids.GridOperation( "Delete",
                                        condition=( lambda item: not item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="mark_group_deleted" ) ),
                   grids.GridOperation( "Undelete",
                                        condition=( lambda item: item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="undelete_group" ) ),
                   grids.GridOperation( "Purge",
                                        condition=( lambda item: item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="purge_group" ) ) ]
    standard_filters = [
        grids.GridColumnFilter( "Active", args=dict( deleted=False ) ),
        grids.GridColumnFilter( "Deleted", args=dict( deleted=True ) ),
        grids.GridColumnFilter( "All", args=dict( deleted='All' ) )
    ]
    num_rows_per_page = 50
    preserve_state = False
    use_paging = True

class AdminToolListGrid( ToolListGrid ):
    class StateColumn( grids.TextColumn ):
        def get_value( self, trans, grid, tool ):
            state = tool.state()
            if state == 'approved':
                state_color = 'ok'
            elif state == 'rejected':
                state_color = 'error'
            elif state == 'archived':
                state_color = 'upload'
            else:
                state_color = state
            return '<div class="count-box state-color-%s">%s</div>' % ( state_color, state )
    class ToolStateColumn( grids.StateColumn ):
        def filter( self, trans, user, query, column_filter ):
            """Modify query to filter by state."""
            if column_filter == "All":
                pass
            elif column_filter in [ v for k, v in self.model_class.states.items() ]:
                # Get all of the latest ToolEventAssociation ids
                tea_ids = [ tea_id_tup[0] for tea_id_tup in trans.sa_session.query( func.max( model.ToolEventAssociation.table.c.id ) ) \
                                                                            .group_by( model.ToolEventAssociation.table.c.tool_id ) ]
                # Get all of the Event ids associated with the latest ToolEventAssociation ids
                event_ids = [ event_id_tup[0] for event_id_tup in trans.sa_session.query( model.ToolEventAssociation.table.c.event_id ) \
                                                                                  .filter( model.ToolEventAssociation.table.c.id.in_( tea_ids ) ) ]
                # Filter our query by state and event ids
                return query.filter( and_( model.Event.table.c.state == column_filter,
                                           model.Event.table.c.id.in_( event_ids ) ) )
            return query

    columns = [ col for col in ToolListGrid.columns ]
    columns.append(
        StateColumn( "Status",
                     model_class=model.Tool,
                     link=( lambda item: dict( operation="tools_by_state", id=item.id, webapp="community" ) ),
                     attach_popup=False ),
    )
    columns.append(
        # Columns that are valid for filtering but are not visible.
        ToolStateColumn( "State",
                         key="state",
                         model_class=model.Tool,
                         visible=False,
                         filterable="advanced" )
    )
    operations = [
        grids.GridOperation( "Edit information",
                             condition=( lambda item: not item.deleted ),
                             allow_multiple=False,
                             url_args=dict( controller="common", action="edit_tool", cntrller="admin", webapp="community" ) )
    ]

class AdminCategoryListGrid( CategoryListGrid ):
    # Override standard filters
    standard_filters = [
        grids.GridColumnFilter( "Active", args=dict( deleted=False ) ),
        grids.GridColumnFilter( "Deleted", args=dict( deleted=True ) ),
        grids.GridColumnFilter( "All", args=dict( deleted='All' ) )
    ]

class ManageCategoryListGrid( CategoryListGrid ):
    columns = [ col for col in CategoryListGrid.columns ]
    # Override the NameColumn to include an Edit link
    columns[ 0 ] = CategoryListGrid.NameColumn( "Name",
                                                key="name",
                                                link=( lambda item: dict( operation="Edit", id=item.id, webapp="community" ) ),
                                                model_class=model.Category,
                                                attach_popup=False,
                                                filterable="advanced" )
    global_actions = [
        grids.GridAction( "Add new category",
                          dict( controller='admin', action='manage_categories', operation='create', webapp="community" ) )
    ]
    operations = [ grids.GridOperation( "Delete",
                                        condition=( lambda item: not item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="mark_category_deleted" ) ),
                   grids.GridOperation( "Undelete",
                                        condition=( lambda item: item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="undelete_category" ) ),
                   grids.GridOperation( "Purge",
                                        condition=( lambda item: item.deleted ),
                                        allow_multiple=True,
                                        url_args=dict( webapp="community", action="purge_category" ) ) ]

class AdminController( BaseController, Admin ):
    
    user_list_grid = UserListGrid()
    role_list_grid = RoleListGrid()
    group_list_grid = GroupListGrid()
    manage_category_list_grid = ManageCategoryListGrid()
    category_list_grid = AdminCategoryListGrid()
    tool_list_grid = AdminToolListGrid()

    @web.expose
    @web.require_admin
    def browse_tools( self, trans, **kwd ):
        # We add params to the keyword dict in this method in order to rename the param
        # with an "f-" prefix, simulating filtering by clicking a search link.  We have
        # to take this approach because the "-" character is illegal in HTTP requests.
        if 'operation' in kwd:
            operation = kwd['operation'].lower()
            if operation == "edit_tool":
                return trans.response.send_redirect( web.url_for( controller='common',
                                                                  action='edit_tool',
                                                                  cntrller='admin',
                                                                  **kwd ) )
            elif operation == "view_tool":
                return trans.response.send_redirect( web.url_for( controller='common',
                                                                  action='view_tool',
                                                                  cntrller='admin',
                                                                  **kwd ) )
            elif operation == 'tool_history':
                return trans.response.send_redirect( web.url_for( controller='common',
                                                                  cntrller='admin',
                                                                  action='events',
                                                                  **kwd ) )
            elif operation == "tools_by_user":
                # Eliminate the current filters if any exist.
                for k, v in kwd.items():
                    if k.startswith( 'f-' ):
                        del kwd[ k ]
                if 'user_id' in kwd:
                    user = get_user( trans, kwd[ 'user_id' ] )
                    kwd[ 'f-email' ] = user.email
                    del kwd[ 'user_id' ]
                else:
                    # The received id is the tool id, so we need to get the id of the user
                    # that uploaded the tool.
                    tool_id = kwd.get( 'id', None )
                    tool = get_tool( trans, tool_id )
                    kwd[ 'f-email' ] = tool.user.email
            elif operation == "tools_by_state":
                # Eliminate the current filters if any exist.
                for k, v in kwd.items():
                    if k.startswith( 'f-' ):
                        del kwd[ k ]
                if 'state' in kwd:
                    # Called from the Admin menu
                    kwd[ 'f-state' ] = kwd[ 'state' ]
                else:
                    # Called from the ToolStateColumn link
                    tool_id = kwd.get( 'id', None )
                    tool = get_tool( trans, tool_id )
                    kwd[ 'f-state' ] = tool.state()
            elif operation == "tools_by_category":
                # Eliminate the current filters if any exist.
                for k, v in kwd.items():
                    if k.startswith( 'f-' ):
                        del kwd[ k ]
                category_id = kwd.get( 'id', None )
                category = get_category( trans, category_id )
                kwd[ 'f-category' ] = category.name
        # Render the list view
        return self.tool_list_grid( trans, **kwd )
    @web.expose
    @web.require_admin
    def browse_categories( self, trans, **kwd ):
        if 'operation' in kwd:
            operation = kwd['operation'].lower()
            if operation in [ "tools_by_category", "tools_by_state", "tools_by_user" ]:
                # Eliminate the current filters if any exist.
                for k, v in kwd.items():
                    if k.startswith( 'f-' ):
                        del kwd[ k ]
                return trans.response.send_redirect( web.url_for( controller='admin',
                                                                  action='browse_tools',
                                                                  **kwd ) )
        # Render the list view
        return self.category_list_grid( trans, **kwd )
    @web.expose
    @web.require_admin
    def manage_categories( self, trans, **kwd ):
        if 'operation' in kwd:
            operation = kwd['operation'].lower()
            if operation == "create":
                return self.create_category( trans, **kwd )
            elif operation == "delete":
                return self.mark_category_deleted( trans, **kwd )
            elif operation == "undelete":
                return self.undelete_category( trans, **kwd )
            elif operation == "purge":
                return self.purge_category( trans, **kwd )
            elif operation == "edit":
                return self.edit_category( trans, **kwd )
        # Render the list view
        return self.manage_category_list_grid( trans, **kwd )
    @web.expose
    @web.require_admin
    def create_category( self, trans, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        if params.get( 'create_category_button', False ):
            name = util.restore_text( params.name )
            description = util.restore_text( params.description )
            error = False
            if not name or not description:
                message = 'Enter a valid name and a description'
                error = True
            elif trans.sa_session.query( trans.app.model.Category ) \
                                 .filter( trans.app.model.Category.table.c.name==name ) \
                                 .first():
                message = 'A category with that name already exists'
                error = True
            if error:
                return trans.fill_template( '/webapps/community/category/create_category.mako',
                                            name=name,
                                            description=description,
                                            message=message,
                                            status='error' )
            else:
                # Create the category
                category = trans.app.model.Category( name=name, description=description )
                trans.sa_session.add( category )
                message = "Category '%s' has been created" % category.name
                trans.sa_session.flush()
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='manage_categories',
                                                           message=util.sanitize_text( message ),
                                                           status='done' ) )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='create_category',
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        else:
            name = ''
            description = ''
        return trans.fill_template( '/webapps/community/category/create_category.mako',
                                    name=name,
                                    description=description,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def set_tool_state( self, trans, state, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        comments = util.restore_text( params.get( 'comments', '' ) )
        id = params.get( 'id', None )
        if not id:
            message = "No tool id received for setting status"
            status = 'error'
        else:
            tool = get_tool( trans, id )
            if state == trans.app.model.Tool.states.APPROVED:
                # If we're approving a tool, all previously approved versions must be set to archived
                for version in get_versions( tool ):
                    # TODO: get latest approved version instead of all versions
                    if version != tool and version.is_approved():
                        # Create an event with state ARCHIVED for the previously approved version of this tool
                        self.__create_tool_event( trans,
                                                  version,
                                                  trans.app.model.Tool.states.ARCHIVED )
                # Create an event with state APPROVED for this tool
                self.__create_tool_event( trans, tool, state, comments )
            elif state == trans.app.model.Tool.states.REJECTED:
                # If we're rejecting a tool, comments about why are necessary.
                return trans.fill_template( '/webapps/community/admin/reject_tool.mako',
                                            tool=tool,
                                            cntrller='admin' )
            message = "State of tool '%s' is now %s" % ( tool.name, state )
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='browse_tools',
                                                   message=message,
                                                   status=status ) )
    @web.expose
    @web.require_admin
    def reject_tool( self, trans, **kwd ):
        params = util.Params( kwd )
        if params.get( 'cancel_reject_button', False ):
            # Fix up the keyword dict to include params to view the current tool
            # since that is the page from which we originated.
            del kwd[ 'cancel_reject_button' ]
            del kwd[ 'comments' ]
            kwd[ 'webapp' ] = 'community'
            kwd[ 'operation' ] = 'view_tool'
            message = 'Tool rejection cancelled'
            status = 'done'
            return trans.response.send_redirect( web.url_for( controller='admin',
                                                              action='browse_tools',
                                                              message=message,
                                                              status=status,
                                                              **kwd ) )
        id = params.get( 'id', None )
        if not id:
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_tools',
                                                              message='No tool id received for rejecting',
                                                              status='error' ) )
        tool = get_tool( trans, id )
        if not trans.app.security_agent.can_approve_or_reject( trans.user, trans.user_is_admin(), 'admin', tool ):
            return trans.response.send_redirect( web.url_for( controller='admin',
                                                              action='browse_tools',
                                                              message='You are not allowed to reject this tool',
                                                              status='error' ) )
        # Comments are required when rejecting a tool.
        comments = util.restore_text( params.get( 'comments', '' ) )
        if not comments:
            message = 'The reason for rejection is required when rejecting a tool.'
            return trans.fill_template( '/webapps/community/admin/reject_tool.mako',
                                        tool=tool,
                                        cntrller='admin',
                                        message=message,
                                        status='error' )
        # Create an event with state REJECTED for this tool
        self.__create_tool_event( trans, tool, trans.app.model.Tool.states.REJECTED, comments )
        message = 'The tool "%s" has been rejected.' % tool.name
        return trans.response.send_redirect( web.url_for( controller='admin',
                                                          action='browse_tools',
                                                          operation='tools_by_state',
                                                          state='rejected',
                                                          message=message,
                                                          status='done' ) )
    def __create_tool_event( self, trans, tool, state, comments='' ):
        event = trans.model.Event( state, comments )
        # Flush so we can get an id
        trans.sa_session.add( event )
        trans.sa_session.flush()
        tea = trans.model.ToolEventAssociation( tool, event )
        trans.sa_session.add( tea )
        trans.sa_session.flush()
    @web.expose
    @web.require_admin
    def purge_tool( self, trans, **kwd ):
        # This method completely removes a tool record and all associated foreign key rows
        # from the database, so it must be used carefully.
        # This method should only be called for a tool that has previously been deleted.
        # Purging a deleted tool deletes all of the following from the database:
        # - ToolCategoryAssociations
        # - ToolEventAssociations and associated Events
        # TODO: when we add tagging for tools, we'll have to purge them as well
        params = util.Params( kwd )
        id = kwd.get( 'id', None )
        if not id:
            message = "No tool ids received for purging"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='browse_tools',
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Purged %d tools: " % len( ids )
        for tool_id in ids:
            tool = get_tool( trans, tool_id )
            message += " %s " % tool.name
            if not tool.deleted:
                message = "Tool '%s' has not been deleted, so it cannot be purged." % tool.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='browse_tools',
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            # Delete ToolCategoryAssociations
            for tca in tool.categories:
                trans.sa_session.delete( tca )
            # Delete ToolEventAssociations and associated events
            for tea in tool.events:
                event = tea.event
                trans.sa_session.delete( event )
                trans.sa_session.delete( tea )
            # Delete the tool
            trans.sa_session.delete( tool )
            trans.sa_session.flush()
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='browse_tools',
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def edit_category( self, trans, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            message = "No category ids received for editing"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='manage_categories',
                                                       message=message,
                                                       status='error' ) )
        category = get_category( trans, id )
        if params.get( 'edit_category_button', False ):
            new_name = util.restore_text( params.get( 'name', '' ) ).strip()
            new_description = util.restore_text( params.get( 'description', '' ) ).strip()
            if category.name != new_name or category.description != new_description:
                if not new_name:
                    message = 'Enter a valid name'
                    status = 'error'
                elif category.name != new_name and \
                    trans.sa_session.query( trans.app.model.Category ).filter( trans.app.model.Category.table.c.name==new_name ).first():
                    message = 'A category with that name already exists'
                    status = 'error'
                else:
                    category.name = new_name
                    category.description = new_description
                    trans.sa_session.add( category )
                    trans.sa_session.flush()
                    message = "The information has been saved for category '%s'" % ( category.name )
                    return trans.response.send_redirect( web.url_for( controller='admin',
                                                                      action='manage_categories',
                                                                      message=util.sanitize_text( message ),
                                                                      status='done' ) )
        return trans.fill_template( '/webapps/community/category/edit_category.mako',
                                    category=category,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def mark_category_deleted( self, trans, **kwd ):
        params = util.Params( kwd )
        id = kwd.get( 'id', None )
        if not id:
            message = "No category ids received for deleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='manage_categories',
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Deleted %d categories: " % len( ids )
        for category_id in ids:
            category = get_category( trans, category_id )
            category.deleted = True
            trans.sa_session.add( category )
            trans.sa_session.flush()
            message += " %s " % category.name
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='manage_categories',
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def undelete_category( self, trans, **kwd ):
        params = util.Params( kwd )
        id = kwd.get( 'id', None )
        if not id:
            message = "No category ids received for undeleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='manage_categories',
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        count = 0
        undeleted_categories = ""
        for category_id in ids:
            category = get_category( trans, category_id )
            if not category.deleted:
                message = "Category '%s' has not been deleted, so it cannot be undeleted." % category.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='manage_categories',
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            category.deleted = False
            trans.sa_session.add( category )
            trans.sa_session.flush()
            count += 1
            undeleted_categories += " %s" % category.name
        message = "Undeleted %d categories: %s" % ( count, undeleted_categories )
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='manage_categories',
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def purge_category( self, trans, **kwd ):
        # This method should only be called for a Category that has previously been deleted.
        # Purging a deleted Category deletes all of the following from the database:
        # - ToolCategoryAssociations where category_id == Category.id
        params = util.Params( kwd )
        id = kwd.get( 'id', None )
        if not id:
            message = "No category ids received for purging"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='manage_categories',
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Purged %d categories: " % len( ids )
        for category_id in ids:
            category = get_category( trans, category_id )
            if not category.deleted:
                message = "Category '%s' has not been deleted, so it cannot be purged." % category.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='manage_categories',
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            # Delete ToolCategoryAssociations
            for tca in category.tools:
                trans.sa_session.delete( tca )
            trans.sa_session.flush()
            message += " %s " % category.name
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='manage_categories',
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )

## ---- Utility methods -------------------------------------------------------

def get_tools_by_state( trans, state ):
    # TODO: write this as a query using eagerload - will be much faster.
    ids = []
    if state == trans.model.Tool.states.NEW:
        for tool in get_tools( trans ):
            if tool.is_new():
                ids.append( tool.id )
    elif state == trans.model.Tool.states.ERROR:
        for tool in get_tools( trans ):
            if tool.is_error():
                ids.append( tool.id )
    elif state == trans.model.Tool.states.DELETED:
        for tool in get_tools( trans ):
            if tool.is_deleted():
                ids.append( tool.id )
    elif state == trans.model.Tool.states.WAITING:
        for tool in get_tools( trans ):
            if tool.is_waiting():
                ids.append( tool.id )
    elif state == trans.model.Tool.states.APPROVED:
        for tool in get_tools( trans ):
            if tool.is_approved():
                ids.append( tool.id )
    elif state == trans.model.Tool.states.REJECTED:
        for tool in get_tools( trans ):
            if tool.is_rejected():
                ids.append( tool.id )
    elif state == trans.model.Tool.states.ARCHIVED:
        for tool in get_tools( trans ):
            if tool.is_archived():
                ids.append( tool.id )
    return ids
