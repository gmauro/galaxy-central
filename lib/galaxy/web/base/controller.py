"""
Contains functionality needed in every web interface
"""
import os, time, logging, re, string, sys, glob
from datetime import datetime, timedelta
from galaxy import config, tools, web, util
from galaxy.web import error, form, url_for
from galaxy.model.orm import *
from galaxy.workflow.modules import *
from galaxy.web.framework import simplejson
from galaxy.web.form_builder import AddressField, CheckboxField, SelectField, TextArea, TextField, WorkflowField, HistoryField, build_select_field
from galaxy.visualization.tracks.data_providers import get_data_provider
from galaxy.visualization.tracks.visual_analytics import get_tool_def

from Cheetah.Template import Template

log = logging.getLogger( __name__ )

# States for passing messages
SUCCESS, INFO, WARNING, ERROR = "done", "info", "warning", "error"

# RE that tests for valid slug.
VALID_SLUG_RE = re.compile( "^[a-z0-9\-]+$" )
    
class BaseController( object ):
    """
    Base class for Galaxy web application controllers.
    """
    def __init__( self, app ):
        """Initialize an interface for application 'app'"""
        self.app = app
    def get_toolbox(self):
        """Returns the application toolbox"""
        return self.app.toolbox
    def get_class( self, trans, class_name ):
        """ Returns the class object that a string denotes. Without this method, we'd have to do eval(<class_name>). """
        if class_name == 'History':
            item_class = trans.model.History
        elif class_name == 'HistoryDatasetAssociation':
            item_class = trans.model.HistoryDatasetAssociation
        elif class_name == 'Page':
            item_class = trans.model.Page
        elif class_name == 'StoredWorkflow':
            item_class = trans.model.StoredWorkflow
        elif class_name == 'Visualization':
            item_class = trans.model.Visualization
        elif class_name == 'Tool':
            item_class = trans.model.Tool
        elif class_name == 'Job':
            item_class == trans.model.Job
        else:
            item_class = None
        return item_class
        
Root = BaseController

class SharableItemSecurity:
    """ Mixin for handling security for sharable items. """
    def security_check( self, user, item, check_ownership=False, check_accessible=False ):
        """ Security checks for an item: checks if (a) user owns item or (b) item is accessible to user. """
        if check_ownership:
            # Verify ownership.
            if not user:
                error( "Must be logged in to manage Galaxy items" )
            if item.user != user:
                error( "%s is not owned by current user" % item.__class__.__name__ )
        if check_accessible:
            # Verify accessible.
            if ( item.user != user ) and ( not item.importable ) and ( user not in item.users_shared_with_dot_users ):
                error( "%s is not accessible to current user" % item.__class__.__name__ )
        return item

#
# TODO: need to move UsesHistory, etc. mixins to better location - perhaps lib/galaxy/model/XXX ?
#       

class UsesHistoryDatasetAssociation:
    """ Mixin for controllers that use HistoryDatasetAssociation objects. """
    def get_dataset( self, trans, dataset_id, check_ownership=True, check_accessible=False ):
        """ Get an HDA object by id. """
        # DEPRECATION: We still support unencoded ids for backward compatibility
        try:
            data = trans.sa_session.query( trans.app.model.HistoryDatasetAssociation ).get( trans.security.decode_id( dataset_id ) )
            if data is None:
                raise ValueError( 'Invalid reference dataset id: %s.' % dataset_id )
        except:
            try:
                data = trans.sa_session.query( trans.app.model.HistoryDatasetAssociation ).get( int( dataset_id ) )
            except:
                data = None
        if not data:
            raise paste.httpexceptions.HTTPRequestRangeNotSatisfiable( "Invalid dataset id: %s." % str( dataset_id ) )
        if check_ownership:
            # Verify ownership.
            user = trans.get_user()
            if not user:
                error( "Must be logged in to manage Galaxy items" )
            if data.history.user != user:
                error( "%s is not owned by current user" % data.__class__.__name__ )
        if check_accessible:
            current_user_roles = trans.get_current_user_roles()
            if trans.app.security_agent.can_access_dataset( current_user_roles, data.dataset ):
                if data.state == trans.model.Dataset.states.UPLOAD:
                    return trans.show_error_message( "Please wait until this dataset finishes uploading before attempting to view it." )
            else:
                error( "You are not allowed to access this dataset" )
        return data
    def get_data( self, dataset, preview=True ):
        """ Gets a dataset's data. """
        # Get data from file, truncating if necessary.
        truncated = False
        dataset_data = None
        if os.path.exists( dataset.file_name ):
            max_peek_size = 1000000 # 1 MB
            if preview and os.stat( dataset.file_name ).st_size > max_peek_size:
                dataset_data = open( dataset.file_name ).read(max_peek_size)
                truncated = True
            else:
                dataset_data = open( dataset.file_name ).read(max_peek_size)
                truncated = False
        return truncated, dataset_data
        
class UsesVisualization( SharableItemSecurity ):
    """ Mixin for controllers that use Visualization objects. """

    len_files = None
    
    def _get_dbkeys( self, trans ):
        """ Returns all valid dbkeys that a user can use in a visualization. """
        
        # Read len files.
        if not self.len_files:
            len_files = glob.glob(os.path.join( trans.app.config.tool_data_path, 'shared','ucsc','chrom', "*.len" ))
            self.len_files = [ os.path.split(f)[1].split(".len")[0] for f in len_files ] # get xxx.len

        user_keys = {}
        user = trans.get_user()
        if 'dbkeys' in user.preferences:
            user_keys = from_json_string( user.preferences['dbkeys'] )
        
        dbkeys = [ (v, k) for k, v in trans.db_builds if k in self.len_files or k in user_keys ]
        return dbkeys
    
    def get_visualization( self, trans, id, check_ownership=True, check_accessible=False ):
        """ Get a Visualization from the database by id, verifying ownership. """
        # Load workflow from database
        try:
            visualization = trans.sa_session.query( trans.model.Visualization ).get( trans.security.decode_id( id ) )
        except TypeError:
            visualization = None
        if not visualization:
            error( "Visualization not found" )
        else:
            return self.security_check( trans.get_user(), visualization, check_ownership, check_accessible )
            
    def get_visualization_config( self, trans, visualization ):
        """ Returns a visualization's configuration. Only works for trackster visualizations right now. """

        config = None
        if visualization.type == 'trackster':
            # Trackster config; taken from tracks/browser
            latest_revision = visualization.latest_revision
            tracks = []

            # Set tracks.
            if 'tracks' in latest_revision.config:
                hda_query = trans.sa_session.query( trans.model.HistoryDatasetAssociation )
                for t in visualization.latest_revision.config['tracks']:
                    dataset_id = t['dataset_id']
                    try:
                        prefs = t['prefs']
                    except KeyError:
                        prefs = {}
                    dataset = hda_query.get( dataset_id )
                    track_type, _ = dataset.datatype.get_track_type()
                    track_data_provider_class = get_data_provider( original_dataset=dataset )
                    track_data_provider = track_data_provider_class( original_dataset=dataset )
                    
                    tracks.append( {
                        "track_type": track_type,
                        "name": dataset.name,
                        "dataset_id": dataset.id,
                        "prefs": simplejson.dumps(prefs),
                        "filters": track_data_provider.get_filters(),
                        "tool": get_tool_def( trans, dataset )
                    } )
            
            config = { "title": visualization.title, "vis_id": trans.security.encode_id( visualization.id ), 
                        "tracks": tracks, "chrom": "", "dbkey": visualization.dbkey }

            if 'viewport' in latest_revision.config:
                config['viewport'] = latest_revision.config['viewport']
            
        return config
        
class UsesStoredWorkflow( SharableItemSecurity ):
    """ Mixin for controllers that use StoredWorkflow objects. """
    def get_stored_workflow( self, trans, id, check_ownership=True, check_accessible=False ):
        """ Get a StoredWorkflow from the database by id, verifying ownership. """
        # Load workflow from database
        try:
            workflow = trans.sa_session.query( trans.model.StoredWorkflow ).get( trans.security.decode_id( id ) )
        except TypeError:
            workflow = None
        if not workflow:
            error( "Workflow not found" )
        else:
            return self.security_check( trans.get_user(), workflow, check_ownership, check_accessible )
    def get_stored_workflow_steps( self, trans, stored_workflow ):
        """ Restores states for a stored workflow's steps. """
        for step in stored_workflow.latest_workflow.steps:
            step.upgrade_messages = {}
            if step.type == 'tool' or step.type is None:
                # Restore the tool state for the step
                module = module_factory.from_workflow_step( trans, step )
                #Check if tool was upgraded
                step.upgrade_messages = module.check_and_update_state()
                # Any connected input needs to have value DummyDataset (these
                # are not persisted so we need to do it every time)
                module.add_dummy_datasets( connections=step.input_connections )                  
                # Store state with the step
                step.module = module
                step.state = module.state
                # Error dict
                if step.tool_errors:
                    errors[step.id] = step.tool_errors
            else:
                ## Non-tool specific stuff?
                step.module = module_factory.from_workflow_step( trans, step )
                step.state = step.module.get_runtime_state()
            # Connections by input name
            step.input_connections_by_name = dict( ( conn.input_name, conn ) for conn in step.input_connections )

class UsesHistory( SharableItemSecurity ):
    """ Mixin for controllers that use History objects. """
    def get_history( self, trans, id, check_ownership=True, check_accessible=False ):
        """Get a History from the database by id, verifying ownership."""
        # Load history from database
        try:
            history = trans.sa_session.query( trans.model.History ).get( trans.security.decode_id( id ) )
        except TypeError:
            history = None
        if not history:
            error( "History not found" )
        else:
            return self.security_check( trans.get_user(), history, check_ownership, check_accessible )
    def get_history_datasets( self, trans, history, show_deleted=False, show_hidden=False):
        """ Returns history's datasets. """
        query = trans.sa_session.query( trans.model.HistoryDatasetAssociation ) \
            .filter( trans.model.HistoryDatasetAssociation.history == history ) \
            .options( eagerload( "children" ) ) \
            .join( "dataset" ).filter( trans.model.Dataset.purged == False ) \
            .options( eagerload_all( "dataset.actions" ) ) \
            .order_by( trans.model.HistoryDatasetAssociation.hid )
        if not show_deleted:
            query = query.filter( trans.model.HistoryDatasetAssociation.deleted == False )
        return query.all()

class UsesFormDefinitions:
    """Mixin for controllers that use Galaxy form objects."""
    def get_all_forms( self, trans, all_versions=False, filter=None, form_type='All' ):
        """
        Return all the latest forms from the form_definition_current table 
        if all_versions is set to True. Otherwise return all the versions
        of all the forms from the form_definition table.
        """
        if all_versions:
            return trans.sa_session.query( trans.app.model.FormDefinition )
        if filter:
            fdc_list = trans.sa_session.query( trans.app.model.FormDefinitionCurrent ).filter_by( **filter )
        else:
            fdc_list = trans.sa_session.query( trans.app.model.FormDefinitionCurrent )
        if form_type == 'All':
            return [ fdc.latest_form for fdc in fdc_list ]
        else:
            return [ fdc.latest_form for fdc in fdc_list if fdc.latest_form.type == form_type ]
    def get_all_forms_by_type( self, trans, cntrller, form_type ):
        forms = self.get_all_forms( trans,
                                    filter=dict( deleted=False ),
                                    form_type=form_type )
        if not forms:
            message = "There are no forms on which to base the template, so create a form and then add the template."
            return trans.response.send_redirect( web.url_for( controller='forms',
                                                              action='create_form_definition',
                                                              cntrller=cntrller,
                                                              message=message,
                                                              status='done',
                                                              form_type=form_type ) )
        return forms
    @web.expose
    def add_template( self, trans, cntrller, item_type, form_type, **kwd ):
        params = util.Params( kwd )
        form_id = params.get( 'form_id', 'none' )
        message = util.restore_text( params.get( 'message', ''  ) )
        action = ''
        status = params.get( 'status', 'done' )
        forms = self.get_all_forms_by_type( trans, cntrller, form_type )
        # form_type must be one of: RUN_DETAILS_TEMPLATE, LIBRARY_INFO_TEMPLATE
        in_library = form_type == trans.model.FormDefinition.types.LIBRARY_INFO_TEMPLATE
        in_sample_tracking = form_type == trans.model.FormDefinition.types.RUN_DETAILS_TEMPLATE
        if in_library:
            show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
            use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
            library_id = params.get( 'library_id', None )
            folder_id = params.get( 'folder_id', None )
            ldda_id = params.get( 'ldda_id', None )
            is_admin = trans.user_is_admin() and cntrller in [ 'library_admin', 'requests_admin' ]
            current_user_roles = trans.get_current_user_roles()
        elif in_sample_tracking:
            request_type_id = params.get( 'request_type_id', None )
            sample_id = params.get( 'sample_id', None )
        try:
            if in_sample_tracking:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       request_type_id=request_type_id,
                                                                       sample_id=sample_id )
            elif in_library:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       library_id=library_id,
                                                                       folder_id=folder_id,
                                                                       ldda_id=ldda_id,
                                                                       is_admin=is_admin )
            if not item:
                message = "Invalid %s id ( %s ) specified." % ( item_desc, str( id ) )
                if in_sample_tracking:
                    return trans.response.send_redirect( web.url_for( controller='request_type',
                                                                      action='browse_request_types',
                                                                      id=request_type_id,
                                                                      message=util.sanitize_text( message ),
                                                                      status='error' ) )
                if in_library:
                    return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                      action='browse_library',
                                                                      cntrller=cntrller,
                                                                      id=library_id,
                                                                      show_deleted=show_deleted,
                                                                      message=util.sanitize_text( message ),
                                                                      status='error' ) )
        except ValueError:
            # At this point, the client has already redirected, so this is just here to prevent the unnecessary traceback
            return None
        if in_library:
            # Make sure the user is authorized to do what they are trying to do.
            authorized = True
            if not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, item ) ):
                authorized = False
                unauthorized = 'modify'
            if not ( is_admin or trans.app.security_agent.can_access_library_item( current_user_roles, item, trans.user ) ):
                authorized = False
                unauthorized = 'access'
            if not authorized:
                message = "You are not authorized to %s %s '%s'." % ( unauthorized, item_desc, item.name )
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='browse_library',
                                                                  cntrller=cntrller,
                                                                  id=library_id,
                                                                  show_deleted=show_deleted,
                                                                  message=util.sanitize_text( message ),
                                                                  status='error' ) )
            # If the inheritable checkbox is checked, the param will be in the request
            inheritable = CheckboxField.is_checked( params.get( 'inheritable', '' ) )
        if params.get( 'add_template_button', False ):
            if form_id not in [ None, 'None', 'none' ]:
                form = trans.sa_session.query( trans.app.model.FormDefinition ).get( trans.security.decode_id( form_id ) )
                form_values = trans.app.model.FormValues( form, {} )
                trans.sa_session.add( form_values )
                trans.sa_session.flush()
                if item_type == 'library':
                    assoc = trans.model.LibraryInfoAssociation( item, form, form_values, inheritable=inheritable )
                elif item_type == 'folder':
                    assoc = trans.model.LibraryFolderInfoAssociation( item, form, form_values, inheritable=inheritable )
                elif item_type == 'ldda':
                    assoc = trans.model.LibraryDatasetDatasetInfoAssociation( item, form, form_values )
                elif item_type in [ 'request_type', 'sample' ]:
                    run = trans.model.Run( form, form_values )
                    trans.sa_session.add( run )
                    trans.sa_session.flush()
                    if item_type == 'request_type':
                        # Delete current RequestTypeRunAssociation, if one exists.
                        rtra = item.run_details
                        if rtra:
                            trans.sa_session.delete( rtra )
                            trans.sa_session.flush()
                        # Add the new RequestTypeRunAssociation.  Templates associated with a RequestType
                        # are automatically inherited to the samples.
                        assoc = trans.model.RequestTypeRunAssociation( item, run )
                    elif item_type == 'sample':
                        assoc = trans.model.SampleRunAssociation( item, run )
                trans.sa_session.add( assoc )
                trans.sa_session.flush()
                message = 'A template based on the form "%s" has been added to this %s.' % ( form.name, item_desc )
                new_kwd = dict( action=action,
                                cntrller=cntrller,
                                message=util.sanitize_text( message ),
                                status='done' )
                if in_sample_tracking:
                    new_kwd.update( dict( controller='request_type',
                                          request_type_id=request_type_id,
                                          sample_id=sample_id,
                                          id=id ) )
                    return trans.response.send_redirect( web.url_for( **new_kwd ) )
                elif in_library:
                    new_kwd.update( dict( controller='library_common',
                                          use_panels=use_panels,
                                          library_id=library_id,
                                          folder_id=folder_id,
                                          id=id,
                                          show_deleted=show_deleted ) )
                    return trans.response.send_redirect( web.url_for( **new_kwd ) )
            else:
                message = "Select a form on which to base the template."
                status = "error"
        form_id_select_field = self.build_form_id_select_field( trans, forms, selected_value=kwd.get( 'form_id', 'none' ) )
        try:
            decoded_form_id = trans.security.decode_id( form_id )
        except:
            decoded_form_id = None
        if decoded_form_id:
            for form in forms:
                if decoded_form_id == form.id:
                    widgets = form.get_widgets( trans.user )
                    break
        else:
            widgets = []
        new_kwd = dict( cntrller=cntrller,
                        item_name=item.name,
                        item_desc=item_desc,
                        item_type=item_type,
                        form_type=form_type,
                        widgets=widgets,
                        form_id_select_field=form_id_select_field,
                        message=message,
                        status=status )
        if in_sample_tracking:
            new_kwd.update( dict( request_type_id=request_type_id,
                                  sample_id=sample_id ) )
        elif in_library:
            new_kwd.update( dict( use_panels=use_panels,
                                  library_id=library_id,
                                  folder_id=folder_id,
                                  ldda_id=ldda_id,
                                  inheritable_checked=inheritable,
                                  show_deleted=show_deleted ) )
        return trans.fill_template( '/common/select_template.mako',
                                    **new_kwd )
    @web.expose
    def edit_template( self, trans, cntrller, item_type, form_type, **kwd ):
        # Edit the template itself, keeping existing field contents, if any.
        params = util.Params( kwd )
        form_id = params.get( 'form_id', 'none' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        edited = util.string_as_bool( params.get( 'edited', False ) )
        action = ''
        # form_type must be one of: RUN_DETAILS_TEMPLATE, LIBRARY_INFO_TEMPLATE
        in_library = form_type == trans.model.FormDefinition.types.LIBRARY_INFO_TEMPLATE
        in_sample_tracking = form_type == trans.model.FormDefinition.types.RUN_DETAILS_TEMPLATE
        if in_library:
            show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
            use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
            library_id = params.get( 'library_id', None )
            folder_id = params.get( 'folder_id', None )
            ldda_id = params.get( 'ldda_id', None )
            is_admin = trans.user_is_admin() and cntrller in [ 'library_admin', 'requests_admin' ]
            current_user_roles = trans.get_current_user_roles()
        elif in_sample_tracking:
            request_type_id = params.get( 'request_type_id', None )
            sample_id = params.get( 'sample_id', None )
        try:
            if in_library:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       library_id=library_id,
                                                                       folder_id=folder_id,
                                                                       ldda_id=ldda_id,
                                                                       is_admin=is_admin )
            elif in_sample_tracking:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       request_type_id=request_type_id,
                                                                       sample_id=sample_id )
        except ValueError:
            return None
        if in_library:
            if not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, item ) ):
                message = "You are not authorized to modify %s '%s'." % ( item_desc, item.name )
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='browse_library',
                                                                  cntrller=cntrller,
                                                                  id=library_id,
                                                                  show_deleted=show_deleted,
                                                                  message=util.sanitize_text( message ),
                                                                  status='error' ) )
        # An info_association must exist at this point
        if in_library:
            info_association, inherited = item.get_info_association( restrict=True )
        elif in_sample_tracking:
            # Here run_details is a RequestTypeRunAssociation
            rtra = item.run_details
            info_association = rtra.run
        template = info_association.template
        info = info_association.info
        form_values = trans.sa_session.query( trans.app.model.FormValues ).get( info.id )
        if edited:
            # The form on which the template is based has been edited, so we need to update the
            # info_association with the current form
            fdc = trans.sa_session.query( trans.app.model.FormDefinitionCurrent ).get( template.form_definition_current_id )
            info_association.template = fdc.latest_form
            trans.sa_session.add( info_association )
            trans.sa_session.flush()
            message = "The template for this %s has been updated with your changes." % item_desc
            new_kwd = dict( action=action,
                            cntrller=cntrller,
                            id=id,
                            message=util.sanitize_text( message ),
                            status='done' )
            if in_library:
                new_kwd.update( dict( controller='library_common',
                                      use_panels=use_panels,
                                      library_id=library_id,
                                      folder_id=folder_id,
                                      show_deleted=show_deleted ) )
                return trans.response.send_redirect( web.url_for( **new_kwd ) )
            elif in_sample_tracking:
                new_kwd.update( dict( controller='request_type',
                                      request_type_id=request_type_id,
                                      sample_id=sample_id ) )
                return trans.response.send_redirect( web.url_for( **new_kwd ) )
        # "template" is a FormDefinition, so since we're changing it, we need to use the latest version of it.
        vars = dict( id=trans.security.encode_id( template.form_definition_current_id ),
                     response_redirect=web.url_for( controller='request_type',
                                                    action='edit_template',
                                                    cntrller=cntrller,
                                                    item_type=item_type,
                                                    form_type=form_type,
                                                    edited=True,
                                                    **kwd ) )
        return trans.response.send_redirect( web.url_for( controller='forms', action='edit_form_definition', **vars ) )
    @web.expose
    def edit_template_info( self, trans, cntrller, item_type, form_type, **kwd ):
        # Edit the contents of the template fields without altering the template itself.
        params = util.Params( kwd )
        # form_type must be one of: RUN_DETAILS_TEMPLATE, LIBRARY_INFO_TEMPLATE
        in_library = form_type == trans.model.FormDefinition.types.LIBRARY_INFO_TEMPLATE
        in_sample_tracking = form_type == trans.model.FormDefinition.types.RUN_DETAILS_TEMPLATE
        if in_library:
            library_id = params.get( 'library_id', None )
            folder_id = params.get( 'folder_id', None )
            ldda_id = params.get( 'ldda_id', None )
            show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
            use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
            is_admin = ( trans.user_is_admin() and cntrller == 'library_admin' )
            current_user_roles = trans.get_current_user_roles()
        elif in_sample_tracking:
            request_type_id = params.get( 'request_type_id', None )
            sample_id = params.get( 'sample_id', None )
            sample = trans.sa_session.query( trans.model.Sample ).get( trans.security.decode_id( sample_id ) )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        try:
            if in_library:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       library_id=library_id,
                                                                       folder_id=folder_id,
                                                                       ldda_id=ldda_id,
                                                                       is_admin=is_admin )
            elif in_sample_tracking:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       request_type_id=request_type_id,
                                                                       sample_id=sample_id )
        except ValueError:
            return None
        if in_library:
            if not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, item ) ):
                message = "You are not authorized to modify %s '%s'." % ( item_desc, item.name )
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='browse_library',
                                                                  cntrller=cntrller,
                                                                  id=library_id,
                                                                  show_deleted=show_deleted,
                                                                  message=util.sanitize_text( message ),
                                                                  status='error' ) )
        # We need the type of each template field widget
        widgets = item.get_template_widgets( trans )
        # The list of widgets may include an AddressField which we need to save if it is new
        for index, widget_dict in enumerate( widgets ):
            widget = widget_dict[ 'widget' ]
            if isinstance( widget, AddressField ):
                #value = util.restore_text( params.get( 'field_%i' % index, '' ) )
                value = util.restore_text( params.get( widget.name, '' ) )
                if value == 'new':
                    if params.get( 'edit_info_button', False ):
                        if self.field_param_values_ok( widget.name, 'AddressField', **kwd ):
                            # Save the new address
                            address = trans.app.model.UserAddress( user=trans.user )
                            self.save_widget_field( trans, address, widget.name, **kwd )
                            widget.value = str( address.id )
                        else:
                            message = 'Required fields are missing contents.'
                            new_kwd = dict( action=action,
                                            id=id,
                                            message=util.sanitize_text( message ),
                                            status='error' )
                            if in_library:
                                new_kwd.update( dict( controller='library_common',
                                                      cntrller=cntrller,
                                                      use_panels=use_panels,
                                                      library_id=library_id,
                                                      folder_id=folder_id,
                                                      show_deleted=show_deleted ) )
                                return trans.response.send_redirect( web.url_for( **new_kwd ) )
                            if in_sample_tracking:
                                new_kwd.update( dict( controller='request_type',
                                                      request_type_id=request_type_id,
                                                      sample_id=sample_id ) )
                                return trans.response.send_redirect( web.url_for( **new_kwd ) )
                    else:
                        # Form was submitted via refresh_on_change
                        widget.value = 'new'
                elif value == unicode( 'none' ):
                    widget.value = ''
                else:
                    widget.value = value
            elif isinstance( widget, CheckboxField ):
                # We need to check the value from kwd since util.Params would have munged the list if
                # the checkbox is checked.
                #value = kwd.get( 'field_%i' % index, '' )
                value = kwd.get( widget.name, '' )
                if CheckboxField.is_checked( value ):
                    widget.value = 'true'
            else:
                #widget.value = util.restore_text( params.get( 'field_%i' % index, '' ) )
                widget.value = util.restore_text( params.get( widget.name, '' ) )
        # Save updated template field contents
        field_contents = self.clean_field_contents( widgets, **kwd )
        if field_contents:
            if in_library:
                # In in a library, since information templates are inherited, the template fields can be displayed
                # on the information page for a folder or ldda when it has no info_association object.  If the user
                #  has added field contents on an inherited template via a parent's info_association, we'll need to
                # create a new form_values and info_association for the current object.  The value for the returned
                # inherited variable is not applicable at this level.
                info_association, inherited = item.get_info_association( restrict=True )
            elif in_sample_tracking:
                assoc = item.run_details
                if item_type == 'request_type' and assoc:
                    # If we're dealing with a RequestType, assoc will be a ReuqestTypeRunAssociation.
                    info_association = assoc.run
                elif item_type == 'sample' and assoc:
                    # If we're dealing with a Sample, assoc will be a SampleRunAssociation if the
                    # Sample has one.  If the Sample does not have a SampleRunAssociation, assoc will
                    # be the Sample's RequestType RequestTypeRunAssociation, in which case we need to
                    # create a SampleRunAssociation using the inherited template from the RequestType.
                    if isinstance( assoc, trans.model.RequestTypeRunAssociation ):
                        form_definition = assoc.run.template
                        new_form_values = trans.model.FormValues( form_definition, {} )
                        trans.sa_session.add( new_form_values )
                        trans.sa_session.flush()
                        new_run = trans.model.Run( form_definition, new_form_values )
                        trans.sa_session.add( new_run )
                        trans.sa_session.flush()
                        sra = trans.model.SampleRunAssociation( item, new_run )
                        trans.sa_session.add( sra )
                        trans.sa_session.flush()
                        info_association = sra.run
                    else:
                       info_association = assoc.run 
                else:
                    info_association = None
            if info_association:
                template = info_association.template
                info = info_association.info
                form_values = trans.sa_session.query( trans.app.model.FormValues ).get( info.id )
                # Update existing content only if it has changed
                flush_required = False
                for field_contents_key, field_contents_value in field_contents.items():
                    if field_contents_key in form_values.content:
                        if form_values.content[ field_contents_key ] != field_contents_value:
                            flush_required = True
                            form_values.content[ field_contents_key ] = field_contents_value
                    else:
                        flush_required = True
                        form_values.content[ field_contents_key ] = field_contents_value
                if flush_required:
                    trans.sa_session.add( form_values )
                    trans.sa_session.flush()
            else:
                if in_library:
                    # Inherit the next available info_association so we can get the template
                    info_association, inherited = item.get_info_association()
                    template = info_association.template
                    # Create a new FormValues object
                    form_values = trans.app.model.FormValues( template, field_contents )
                    trans.sa_session.add( form_values )
                    trans.sa_session.flush()
                    # Create a new info_association between the current library item and form_values
                    if item_type == 'folder':
                        # A LibraryFolder is a special case because if it inherited the template from it's parent,
                        # we want to set inheritable to True for it's info_association.  This allows for the default
                        # inheritance to be False for each level in the Library hierarchy unless we're creating a new
                        # level in the hierarchy, in which case we'll inherit the "inheritable" setting from the parent
                        # level.
                        info_association = trans.app.model.LibraryFolderInfoAssociation( item, template, form_values, inheritable=inherited )
                        trans.sa_session.add( info_association )
                        trans.sa_session.flush()
                    elif item_type == 'ldda':
                        info_association = trans.app.model.LibraryDatasetDatasetInfoAssociation( item, template, form_values )
                        trans.sa_session.add( info_association )
                        trans.sa_session.flush()
        message = 'The information has been updated.'
        new_kwd = dict( action=action,
                        cntrller=cntrller,
                        id=id,
                        message=util.sanitize_text( message ),
                        status='done' )
        if in_library:
            new_kwd.update( dict( controller='library_common',
                                  use_panels=use_panels,
                                  library_id=library_id,
                                  folder_id=folder_id,
                                  show_deleted=show_deleted ) )
            return trans.response.send_redirect( web.url_for( **new_kwd ) )
        if in_sample_tracking:
            new_kwd.update( dict( controller='requests_common',
                                  cntrller='requests_admin',
                                  id=trans.security.encode_id( sample.request.id ),
                                  sample_id=sample_id ) )
            return trans.response.send_redirect( web.url_for( **new_kwd ) )
    @web.expose
    def delete_template( self, trans, cntrller, item_type, form_type, **kwd ):
        params = util.Params( kwd )
        # form_type must be one of: RUN_DETAILS_TEMPLATE, LIBRARY_INFO_TEMPLATE
        in_library = form_type == trans.model.FormDefinition.types.LIBRARY_INFO_TEMPLATE
        in_sample_tracking = form_type == trans.model.FormDefinition.types.RUN_DETAILS_TEMPLATE
        if in_library:
            is_admin = ( trans.user_is_admin() and cntrller == 'library_admin' )
            current_user_roles = trans.get_current_user_roles()
            show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
            use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
            library_id = params.get( 'library_id', None )
            folder_id = params.get( 'folder_id', None )
            ldda_id = params.get( 'ldda_id', None )
        elif in_sample_tracking:
            request_type_id = params.get( 'request_type_id', None )
            sample_id = params.get( 'sample_id', None )
        #id = params.get( 'id', None )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        try:
            if in_library:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       library_id=library_id,
                                                                       folder_id=folder_id,
                                                                       ldda_id=ldda_id,
                                                                       is_admin=is_admin )
            elif in_sample_tracking:
                item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                       item_type=item_type,
                                                                       request_type_id=request_type_id,
                                                                       sample_id=sample_id )
        except ValueError:
            return None
        if in_library:
            if not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, item ) ):
                message = "You are not authorized to modify %s '%s'." % ( item_desc, item.name )
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='browse_library',
                                                                  cntrller=cntrller,
                                                                  id=library_id,
                                                                  show_deleted=show_deleted,
                                                                  message=util.sanitize_text( message ),
                                                                  status='error' ) )
        if in_library:
            info_association, inherited = item.get_info_association()
        elif in_sample_tracking:
            info_association = item.run_details
        if not info_association:
            message = "There is no template for this %s" % item_type
            status = 'error'
        else:
            if in_library:
                info_association.deleted = True
                trans.sa_session.add( info_association )
                trans.sa_session.flush()
            elif in_sample_tracking:
                trans.sa_session.delete( info_association )
                trans.sa_session.flush()
            message = 'The template for this %s has been deleted.' % item_type
            status = 'done'
        new_kwd = dict( action=action,
                        cntrller=cntrller,
                        id=id,
                        message=util.sanitize_text( message ),
                        status='done' )
        if in_library:
            new_kwd.update( dict( controller='library_common',
                                  use_panels=use_panels,
                                  library_id=library_id,
                                  folder_id=folder_id,
                                  show_deleted=show_deleted ) )
            return trans.response.send_redirect( web.url_for( **new_kwd ) )
        if in_sample_tracking:
            new_kwd.update( dict( controller='request_type',
                                  request_type_id=request_type_id,
                                  sample_id=sample_id ) )
            return trans.response.send_redirect( web.url_for( **new_kwd ) )
    def widget_fields_have_contents( self, widgets ):
        # Return True if any of the fields in widgets contain contents, widgets is a list of dictionaries that looks something like:
        # [{'widget': <galaxy.web.form_builder.TextField object at 0x10867aa10>, 'helptext': 'Field 0 help (Optional)', 'label': 'Field 0'}]
        for i, field in enumerate( widgets ):
            if ( isinstance( field[ 'widget' ], TextArea ) or isinstance( field[ 'widget' ], TextField ) ) and field[ 'widget' ].value:
                return True
            if isinstance( field[ 'widget' ], SelectField ) and field[ 'widget' ].options:
                for option_label, option_value, selected in field[ 'widget' ].options:
                    if selected:
                        return True
            if isinstance( field[ 'widget' ], CheckboxField ) and field[ 'widget' ].checked:
                return True
            if isinstance( field[ 'widget' ], WorkflowField ) and str( field[ 'widget' ].value ).lower() not in [ 'none' ]:
                return True
            if isinstance( field[ 'widget' ], HistoryField ) and str( field[ 'widget' ].value ).lower() not in [ 'none' ]:
                return True
            if isinstance( field[ 'widget' ], AddressField ) and str( field[ 'widget' ].value ).lower() not in [ 'none' ]:
                return True
        return False
    def clean_field_contents( self, widgets, **kwd ):
        field_contents = {}
        for index, widget_dict in enumerate( widgets ):
            widget = widget_dict[ 'widget' ]
            value = kwd.get( widget.name, ''  )
            if isinstance( widget, CheckboxField ):
                # CheckboxField values are lists if the checkbox is checked
                value = str( widget.is_checked( value ) ).lower()
            elif isinstance( widget, AddressField ):
                # If the address was new, is has already been saved and widget.value is the new address.id
                value = widget.value
            field_contents[ widget.name ] = util.restore_text( value )
        return field_contents
    def field_param_values_ok( self, widget_name, widget_type, **kwd ):
        # Make sure required fields have contents, etc
        params = util.Params( kwd )
        if widget_type == 'AddressField':
            if not util.restore_text( params.get( '%s_short_desc' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_name' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_institution' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_address' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_city' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_state' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_postal_code' % widget_name, '' ) ) \
                or not util.restore_text( params.get( '%s_country' % widget_name, '' ) ):
                return False
        return True
    def save_widget_field( self, trans, field_obj, widget_name, **kwd ):
        # Save a form_builder field object
        params = util.Params( kwd )
        if isinstance( field_obj, trans.model.UserAddress ):
            field_obj.desc = util.restore_text( params.get( '%s_short_desc' % widget_name, '' ) )
            field_obj.name = util.restore_text( params.get( '%s_name' % widget_name, '' ) )
            field_obj.institution = util.restore_text( params.get( '%s_institution' % widget_name, '' ) )
            field_obj.address = util.restore_text( params.get( '%s_address' % widget_name, '' ) )
            field_obj.city = util.restore_text( params.get( '%s_city' % widget_name, '' ) )
            field_obj.state = util.restore_text( params.get( '%s_state' % widget_name, '' ) )
            field_obj.postal_code = util.restore_text( params.get( '%s_postal_code' % widget_name, '' ) )
            field_obj.country = util.restore_text( params.get( '%s_country' % widget_name, '' ) )
            field_obj.phone = util.restore_text( params.get( '%s_phone' % widget_name, '' ) )
            trans.sa_session.add( field_obj )
            trans.sa_session.flush()
    def populate_widgets_from_kwd( self, trans, widgets, **kwd ):
        # A form submitted via refresh_on_change requires us to populate the widgets with the contents of
        # the form fields the user may have entered so that when the form refreshes the contents are retained.
        params = util.Params( kwd )
        populated_widgets = []
        for widget_dict in widgets:
            widget = widget_dict[ 'widget' ]
            if params.get( widget.name, False ):
                # The form included a field whose contents should be used to set the
                # value of the current widget (widget.name is field_0, field_1, etc).
                if isinstance( widget, AddressField ):
                    value = util.restore_text( params.get( widget.name, '' ) )
                    if value == 'none':
                        value = ''
                    widget.value = value
                    widget_dict[ 'widget' ] = widget
                    # Populate the AddressField params with the form field contents
                    widget_params_dict = {}
                    for field_name, label, help_text in widget.fields():
                        form_param_name = '%s_%s' % ( widget.name, field_name )
                        widget_params_dict[ form_param_name ] = util.restore_text( params.get( form_param_name, '' ) )
                    widget.params = widget_params_dict
                elif isinstance( widget, CheckboxField ):
                    # Check the value from kwd since util.Params would have
                    # stringify'd the list if the checkbox is checked.
                    value = kwd.get( widget.name, '' )
                    if CheckboxField.is_checked( value ):
                        widget.value = 'true'
                        widget_dict[ 'widget' ] = widget
                elif isinstance( widget, SelectField ):
                    # Ensure the selected option remains selected.
                    value = util.restore_text( params.get( widget.name, '' ) )
                    processed_options = []
                    for option_label, option_value, option_selected in widget.options:
                        selected = value == option_value
                        processed_options.append( ( option_label, option_value, selected ) )
                    widget.options = processed_options
                else:
                    widget.value = util.restore_text( params.get( widget.name, '' ) )
                    widget_dict[ 'widget' ] = widget
            populated_widgets.append( widget_dict )
        return populated_widgets
    def get_item_and_stuff( self, trans, item_type, **kwd ):
        # Return an item, description, action and an id based on the item_type.  Valid item_types are
        # library, folder, ldda, request_type, sample.
        is_admin = kwd.get( 'is_admin', False )
        #message = None
        current_user_roles = trans.get_current_user_roles()
        if item_type == 'library':
            library_id = kwd.get( 'library_id', None )
            id = library_id
            try:
                item = trans.sa_session.query( trans.app.model.Library ).get( trans.security.decode_id( library_id ) )
            except:
                item = None
            item_desc = 'data library'
            action = 'library_info'
        elif item_type == 'folder':
            folder_id = kwd.get( 'folder_id', None )
            id = folder_id
            try:
                item = trans.sa_session.query( trans.app.model.LibraryFolder ).get( trans.security.decode_id( folder_id ) )
            except:
                item = None
            item_desc = 'folder'
            action = 'folder_info'
        elif item_type == 'ldda':
            ldda_id = kwd.get( 'ldda_id', None )
            id = ldda_id
            try:
                item = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( ldda_id ) )
            except:
                item = None
            item_desc = 'dataset'
            action = 'ldda_edit_info'
        elif item_type == 'request_type':
            request_type_id = kwd.get( 'request_type_id', None )
            id = request_type_id
            try:
                item = trans.sa_session.query( trans.app.model.RequestType ).get( trans.security.decode_id( request_type_id ) )
            except:
                item = None
            item_desc = 'sequencer configuration'
            action = 'edit_request_type'
        elif item_type == 'sample':
            sample_id = kwd.get( 'sample_id', None )
            id = sample_id
            try:
                item = trans.sa_session.query( trans.app.model.Sample ).get( trans.security.decode_id( sample_id ) )
            except:
                item = None
            item_desc = 'sample'
            action = 'edit_samples'
        else:
            item = None
            #message = "Invalid item type ( %s )" % str( item_type )
            item_desc = None
            action = None
            id = None
        return item, item_desc, action, id
    def build_form_id_select_field( self, trans, forms, selected_value='none' ):
        return build_select_field( trans,
                                   objs=forms,
                                   label_attr='name',
                                   select_field_name='form_id',
                                   selected_value=selected_value,
                                   refresh_on_change=True )

class Sharable:
    """ Mixin for a controller that manages an item that can be shared. """
    # Implemented methods.
    @web.expose
    @web.require_login( "share Galaxy items" )
    def set_public_username( self, trans, id, username, **kwargs ):
        """ Set user's public username and delegate to sharing() """
        trans.get_user().username = username
        trans.sa_session.flush
        return self.sharing( trans, id, **kwargs )
    # Abstract methods.
    @web.expose
    @web.require_login( "modify Galaxy items" )
    def set_slug_async( self, trans, id, new_slug ):
        """ Set item slug asynchronously. """
        pass  
    @web.expose
    @web.require_login( "share Galaxy items" )
    def sharing( self, trans, id, **kwargs ):
        """ Handle item sharing. """
        pass
    @web.expose
    @web.require_login( "share Galaxy items" )
    def share( self, trans, id=None, email="", **kwd ):
        """ Handle sharing an item with a particular user. """
        pass
    @web.expose
    def display_by_username_and_slug( self, trans, username, slug ):
        """ Display item by username and slug. """
        pass
    @web.expose
    @web.json
    @web.require_login( "get item name and link" )
    def get_name_and_link_async( self, trans, id=None ):
        """ Returns item's name and link. """
        pass
    @web.expose
    @web.require_login("get item content asynchronously")
    def get_item_content_async( self, trans, id ):
        """ Returns item content in HTML format. """
        pass
    # Helper methods.
    def _make_item_accessible( self, sa_session, item ):
        """ Makes item accessible--viewable and importable--and sets item's slug. Does not flush/commit changes, however. Item must have name, user, importable, and slug attributes. """
        item.importable = True
        self.create_item_slug( sa_session, item )
    def create_item_slug( self, sa_session, item ):
        """ Create item slug. Slug is unique among user's importable items for item's class. Returns true if item's slug was set; false otherwise. """
        if item.slug is None or item.slug == "":
            # Item can have either a name or a title.
            if hasattr( item, 'name' ):
                item_name = item.name
            elif hasattr( item, 'title' ):
                item_name = item.title
            # Replace whitespace with '-'
            slug_base = re.sub( "\s+", "-", item_name.lower() )
            # Remove all non-alphanumeric characters.
            slug_base = re.sub( "[^a-zA-Z0-9\-]", "", slug_base )
            # Remove trailing '-'.
            if slug_base.endswith('-'):
                slug_base = slug_base[:-1]
            # Make sure that slug is not taken; if it is, add a number to it.
            slug = slug_base
            count = 1
            while sa_session.query( item.__class__ ).filter_by( user=item.user, slug=slug, importable=True ).count() != 0:
                # Slug taken; choose a new slug based on count. This approach can handle numerous histories with the same name gracefully.
                slug = '%s-%i' % ( slug_base, count )
                count += 1
            item.slug = slug
            return True
        return False
        
"""
Deprecated: `BaseController` used to be available under the name `Root`
"""
class ControllerUnavailable( Exception ):
    pass

class Admin( object ):
    # Override these
    user_list_grid = None
    role_list_grid = None
    group_list_grid = None
    
    @web.expose
    @web.require_admin
    def index( self, trans, **kwd ):
        webapp = kwd.get( 'webapp', 'galaxy' )
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        if webapp == 'galaxy':
            return trans.fill_template( '/webapps/galaxy/admin/index.mako',
                                        webapp=webapp,
                                        message=message,
                                        status=status )
        else:
            return trans.fill_template( '/webapps/community/admin/index.mako',
                                        webapp=webapp,
                                        message=message,
                                        status=status )
    @web.expose
    @web.require_admin
    def center( self, trans, **kwd ):
        webapp = kwd.get( 'webapp', 'galaxy' )
        if webapp == 'galaxy':
            return trans.fill_template( '/webapps/galaxy/admin/center.mako' )
        else:
            return trans.fill_template( '/webapps/community/admin/center.mako' )
    @web.expose
    @web.require_admin
    def reload_tool( self, trans, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        return trans.fill_template( '/admin/reload_tool.mako',
                                    toolbox=self.app.toolbox,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def tool_reload( self, trans, tool_version=None, **kwd ):
        params = util.Params( kwd )
        tool_id = params.tool_id
        self.app.toolbox.reload( tool_id )
        message = 'Reloaded tool: ' + tool_id
        return trans.fill_template( '/admin/reload_tool.mako',
                                    toolbox=self.app.toolbox,
                                    message=message,
                                    status='done' )
    
    # Galaxy Role Stuff
    @web.expose
    @web.require_admin
    def roles( self, trans, **kwargs ):
        if 'operation' in kwargs:
            operation = kwargs['operation'].lower()
            if operation == "roles":
                return self.role( trans, **kwargs )
            if operation == "create":
                return self.create_role( trans, **kwargs )
            if operation == "delete":
                return self.mark_role_deleted( trans, **kwargs )
            if operation == "undelete":
                return self.undelete_role( trans, **kwargs )
            if operation == "purge":
                return self.purge_role( trans, **kwargs )
            if operation == "manage users and groups":
                return self.manage_users_and_groups_for_role( trans, **kwargs )
            if operation == "rename":
                return self.rename_role( trans, **kwargs )
        # Render the list view
        return self.role_list_grid( trans, **kwargs )
    @web.expose
    @web.require_admin
    def create_role( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        if params.get( 'create_role_button', False ):
            name = util.restore_text( params.name )
            description = util.restore_text( params.description )
            in_users = util.listify( params.get( 'in_users', [] ) )
            in_groups = util.listify( params.get( 'in_groups', [] ) )
            create_group_for_role = params.get( 'create_group_for_role', 'no' )
            if not name or not description:
                message = "Enter a valid name and a description"
            elif trans.sa_session.query( trans.app.model.Role ).filter( trans.app.model.Role.table.c.name==name ).first():
                message = "A role with that name already exists"
            else:
                # Create the role
                role = trans.app.model.Role( name=name, description=description, type=trans.app.model.Role.types.ADMIN )
                trans.sa_session.add( role )
                # Create the UserRoleAssociations
                for user in [ trans.sa_session.query( trans.app.model.User ).get( x ) for x in in_users ]:
                    ura = trans.app.model.UserRoleAssociation( user, role )
                    trans.sa_session.add( ura )
                # Create the GroupRoleAssociations
                for group in [ trans.sa_session.query( trans.app.model.Group ).get( x ) for x in in_groups ]:
                    gra = trans.app.model.GroupRoleAssociation( group, role )
                    trans.sa_session.add( gra )
                if create_group_for_role == 'yes':
                    # Create the group
                    group = trans.app.model.Group( name=name )
                    trans.sa_session.add( group )
                    message = "Group '%s' has been created, and role '%s' has been created with %d associated users and %d associated groups" % \
                    ( group.name, role.name, len( in_users ), len( in_groups ) )
                else:
                    message = "Role '%s' has been created with %d associated users and %d associated groups" % ( role.name, len( in_users ), len( in_groups ) )
                trans.sa_session.flush()
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='roles',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='done' ) )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='create_role',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        out_users = []
        for user in trans.sa_session.query( trans.app.model.User ) \
                                    .filter( trans.app.model.User.table.c.deleted==False ) \
                                    .order_by( trans.app.model.User.table.c.email ):
            out_users.append( ( user.id, user.email ) )
        out_groups = []
        for group in trans.sa_session.query( trans.app.model.Group ) \
                                     .filter( trans.app.model.Group.table.c.deleted==False ) \
                                     .order_by( trans.app.model.Group.table.c.name ):
            out_groups.append( ( group.id, group.name ) )
        return trans.fill_template( '/admin/dataset_security/role/role_create.mako',
                                    in_users=[],
                                    out_users=out_users,
                                    in_groups=[],
                                    out_groups=out_groups,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def rename_role( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            message = "No role ids received for renaming"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='roles',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        role = get_role( trans, id )
        if params.get( 'rename_role_button', False ):
            old_name = role.name
            new_name = util.restore_text( params.name )
            new_description = util.restore_text( params.description )
            if not new_name:
                message = 'Enter a valid name'
                status='error'
            elif trans.sa_session.query( trans.app.model.Role ).filter( trans.app.model.Role.table.c.name==new_name ).first():
                message = 'A role with that name already exists'
                status = 'error'
            else:
                role.name = new_name
                role.description = new_description
                trans.sa_session.add( role )
                trans.sa_session.flush()
                message = "Role '%s' has been renamed to '%s'" % ( old_name, new_name )
                return trans.response.send_redirect( web.url_for( controller='admin',
                                                                  action='roles',
                                                                  webapp=webapp,
                                                                  message=util.sanitize_text( message ),
                                                                  status='done' ) )
        return trans.fill_template( '/admin/dataset_security/role/role_rename.mako',
                                    role=role,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def manage_users_and_groups_for_role( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            message = "No role ids received for managing users and groups"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='roles',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        role = get_role( trans, id )
        if params.get( 'role_members_edit_button', False ):
            in_users = [ trans.sa_session.query( trans.app.model.User ).get( x ) for x in util.listify( params.in_users ) ]
            for ura in role.users:
                user = trans.sa_session.query( trans.app.model.User ).get( ura.user_id )
                if user not in in_users:
                    # Delete DefaultUserPermissions for previously associated users that have been removed from the role
                    for dup in user.default_permissions:
                        if role == dup.role:
                            trans.sa_session.delete( dup )
                    # Delete DefaultHistoryPermissions for previously associated users that have been removed from the role
                    for history in user.histories:
                        for dhp in history.default_permissions:
                            if role == dhp.role:
                                trans.sa_session.delete( dhp )
                    trans.sa_session.flush()
            in_groups = [ trans.sa_session.query( trans.app.model.Group ).get( x ) for x in util.listify( params.in_groups ) ]
            trans.app.security_agent.set_entity_role_associations( roles=[ role ], users=in_users, groups=in_groups )
            trans.sa_session.refresh( role )
            message = "Role '%s' has been updated with %d associated users and %d associated groups" % ( role.name, len( in_users ), len( in_groups ) )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='roles',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status=status ) )            
        in_users = []
        out_users = []
        in_groups = []
        out_groups = []
        for user in trans.sa_session.query( trans.app.model.User ) \
                                    .filter( trans.app.model.User.table.c.deleted==False ) \
                                    .order_by( trans.app.model.User.table.c.email ):
            if user in [ x.user for x in role.users ]:
                in_users.append( ( user.id, user.email ) )
            else:
                out_users.append( ( user.id, user.email ) )
        for group in trans.sa_session.query( trans.app.model.Group ) \
                                     .filter( trans.app.model.Group.table.c.deleted==False ) \
                                     .order_by( trans.app.model.Group.table.c.name ):
            if group in [ x.group for x in role.groups ]:
                in_groups.append( ( group.id, group.name ) )
            else:
                out_groups.append( ( group.id, group.name ) )
        library_dataset_actions = {}
        if webapp == 'galaxy':
            # Build a list of tuples that are LibraryDatasetDatasetAssociationss followed by a list of actions
            # whose DatasetPermissions is associated with the Role
            # [ ( LibraryDatasetDatasetAssociation [ action, action ] ) ]
            for dp in role.dataset_actions:
                for ldda in trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ) \
                                            .filter( trans.app.model.LibraryDatasetDatasetAssociation.dataset_id==dp.dataset_id ):
                    root_found = False
                    folder_path = ''
                    folder = ldda.library_dataset.folder
                    while not root_found:
                        folder_path = '%s / %s' % ( folder.name, folder_path )
                        if not folder.parent:
                            root_found = True
                        else:
                            folder = folder.parent
                    folder_path = '%s %s' % ( folder_path, ldda.name )
                    library = trans.sa_session.query( trans.app.model.Library ) \
                                              .filter( trans.app.model.Library.table.c.root_folder_id == folder.id ) \
                                              .first()
                    if library not in library_dataset_actions:
                        library_dataset_actions[ library ] = {}
                    try:
                        library_dataset_actions[ library ][ folder_path ].append( dp.action )
                    except:
                        library_dataset_actions[ library ][ folder_path ] = [ dp.action ]
        return trans.fill_template( '/admin/dataset_security/role/role.mako',
                                    role=role,
                                    in_users=in_users,
                                    out_users=out_users,
                                    in_groups=in_groups,
                                    out_groups=out_groups,
                                    library_dataset_actions=library_dataset_actions,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def mark_role_deleted( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No role ids received for deleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='roles',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Deleted %d roles: " % len( ids )
        for role_id in ids:
            role = get_role( trans, role_id )
            role.deleted = True
            trans.sa_session.add( role )
            trans.sa_session.flush()
            message += " %s " % role.name
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='roles',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def undelete_role( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No role ids received for undeleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='roles',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        count = 0
        undeleted_roles = ""
        for role_id in ids:
            role = get_role( trans, role_id )
            if not role.deleted:
                message = "Role '%s' has not been deleted, so it cannot be undeleted." % role.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='roles',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            role.deleted = False
            trans.sa_session.add( role )
            trans.sa_session.flush()
            count += 1
            undeleted_roles += " %s" % role.name
        message = "Undeleted %d roles: %s" % ( count, undeleted_roles )
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='roles',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def purge_role( self, trans, **kwd ):
        # This method should only be called for a Role that has previously been deleted.
        # Purging a deleted Role deletes all of the following from the database:
        # - UserRoleAssociations where role_id == Role.id
        # - DefaultUserPermissions where role_id == Role.id
        # - DefaultHistoryPermissions where role_id == Role.id
        # - GroupRoleAssociations where role_id == Role.id
        # - DatasetPermissionss where role_id == Role.id
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No role ids received for purging"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='roles',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Purged %d roles: " % len( ids )
        for role_id in ids:
            role = get_role( trans, role_id )
            if not role.deleted:
                message = "Role '%s' has not been deleted, so it cannot be purged." % role.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='roles',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            # Delete UserRoleAssociations
            for ura in role.users:
                user = trans.sa_session.query( trans.app.model.User ).get( ura.user_id )
                # Delete DefaultUserPermissions for associated users
                for dup in user.default_permissions:
                    if role == dup.role:
                        trans.sa_session.delete( dup )
                # Delete DefaultHistoryPermissions for associated users
                for history in user.histories:
                    for dhp in history.default_permissions:
                        if role == dhp.role:
                            trans.sa_session.delete( dhp )
                trans.sa_session.delete( ura )
            # Delete GroupRoleAssociations
            for gra in role.groups:
                trans.sa_session.delete( gra )
            # Delete DatasetPermissionss
            for dp in role.dataset_actions:
                trans.sa_session.delete( dp )
            trans.sa_session.flush()
            message += " %s " % role.name
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='roles',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )

    # Galaxy Group Stuff
    @web.expose
    @web.require_admin
    def groups( self, trans, **kwargs ):
        if 'operation' in kwargs:
            operation = kwargs['operation'].lower()
            if operation == "groups":
                return self.group( trans, **kwargs )
            if operation == "create":
                return self.create_group( trans, **kwargs )
            if operation == "delete":
                return self.mark_group_deleted( trans, **kwargs )
            if operation == "undelete":
                return self.undelete_group( trans, **kwargs )
            if operation == "purge":
                return self.purge_group( trans, **kwargs )
            if operation == "manage users and roles":
                return self.manage_users_and_roles_for_group( trans, **kwargs )
            if operation == "rename":
                return self.rename_group( trans, **kwargs )
        # Render the list view
        return self.group_list_grid( trans, **kwargs )
    @web.expose
    @web.require_admin
    def rename_group( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        id = params.get( 'id', None )
        if not id:
            message = "No group ids received for renaming"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='groups',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        group = get_group( trans, id )
        if params.get( 'rename_group_button', False ):
            old_name = group.name
            new_name = util.restore_text( params.name )
            if not new_name:
                message = 'Enter a valid name'
                status = 'error'
            elif trans.sa_session.query( trans.app.model.Group ).filter( trans.app.model.Group.table.c.name==new_name ).first():
                message = 'A group with that name already exists'
                status = 'error'
            else:
                group.name = new_name
                trans.sa_session.add( group )
                trans.sa_session.flush()
                message = "Group '%s' has been renamed to '%s'" % ( old_name, new_name )
                return trans.response.send_redirect( web.url_for( controller='admin',
                                                                  action='groups',
                                                                  webapp=webapp,
                                                                  message=util.sanitize_text( message ),
                                                                  status='done' ) )
        return trans.fill_template( '/admin/dataset_security/group/group_rename.mako',
                                    group=group,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def manage_users_and_roles_for_group( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        group = get_group( trans, params.id )
        if params.get( 'group_roles_users_edit_button', False ):
            in_roles = [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in util.listify( params.in_roles ) ]
            in_users = [ trans.sa_session.query( trans.app.model.User ).get( x ) for x in util.listify( params.in_users ) ]
            trans.app.security_agent.set_entity_group_associations( groups=[ group ], roles=in_roles, users=in_users )
            trans.sa_session.refresh( group )
            message += "Group '%s' has been updated with %d associated roles and %d associated users" % ( group.name, len( in_roles ), len( in_users ) )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='groups',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status=status ) )
        in_roles = []
        out_roles = []
        in_users = []
        out_users = []
        for role in trans.sa_session.query(trans.app.model.Role ) \
                                    .filter( trans.app.model.Role.table.c.deleted==False ) \
                                    .order_by( trans.app.model.Role.table.c.name ):
            if role in [ x.role for x in group.roles ]:
                in_roles.append( ( role.id, role.name ) )
            else:
                out_roles.append( ( role.id, role.name ) )
        for user in trans.sa_session.query( trans.app.model.User ) \
                                    .filter( trans.app.model.User.table.c.deleted==False ) \
                                    .order_by( trans.app.model.User.table.c.email ):
            if user in [ x.user for x in group.users ]:
                in_users.append( ( user.id, user.email ) )
            else:
                out_users.append( ( user.id, user.email ) )
        message += 'Group %s is currently associated with %d roles and %d users' % ( group.name, len( in_roles ), len( in_users ) )
        return trans.fill_template( '/admin/dataset_security/group/group.mako',
                                    group=group,
                                    in_roles=in_roles,
                                    out_roles=out_roles,
                                    in_users=in_users,
                                    out_users=out_users,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def create_group( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        if params.get( 'create_group_button', False ):
            name = util.restore_text( params.name )
            in_users = util.listify( params.get( 'in_users', [] ) )
            in_roles = util.listify( params.get( 'in_roles', [] ) )
            if not name:
                message = "Enter a valid name"
            elif trans.sa_session.query( trans.app.model.Group ).filter( trans.app.model.Group.table.c.name==name ).first():
                message = "A group with that name already exists"
            else:
                # Create the group
                group = trans.app.model.Group( name=name )
                trans.sa_session.add( group )
                trans.sa_session.flush()
                # Create the UserRoleAssociations
                for user in [ trans.sa_session.query( trans.app.model.User ).get( x ) for x in in_users ]:
                    uga = trans.app.model.UserGroupAssociation( user, group )
                    trans.sa_session.add( uga )
                    trans.sa_session.flush()
                # Create the GroupRoleAssociations
                for role in [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in in_roles ]:
                    gra = trans.app.model.GroupRoleAssociation( group, role )
                    trans.sa_session.add( gra )
                    trans.sa_session.flush()
                message = "Group '%s' has been created with %d associated users and %d associated roles" % ( name, len( in_users ), len( in_roles ) )
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='groups',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='done' ) )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='create_group',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        out_users = []
        for user in trans.sa_session.query( trans.app.model.User ) \
                                    .filter( trans.app.model.User.table.c.deleted==False ) \
                                    .order_by( trans.app.model.User.table.c.email ):
            out_users.append( ( user.id, user.email ) )
        out_roles = []
        for role in trans.sa_session.query( trans.app.model.Role ) \
                                    .filter( trans.app.model.Role.table.c.deleted==False ) \
                                    .order_by( trans.app.model.Role.table.c.name ):
            out_roles.append( ( role.id, role.name ) )
        return trans.fill_template( '/admin/dataset_security/group/group_create.mako',
                                    in_users=[],
                                    out_users=out_users,
                                    in_roles=[],
                                    out_roles=out_roles,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def mark_group_deleted( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        id = params.get( 'id', None )
        if not id:
            message = "No group ids received for marking deleted"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='groups',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Deleted %d groups: " % len( ids )
        for group_id in ids:
            group = get_group( trans, group_id )
            group.deleted = True
            trans.sa_session.add( group )
            trans.sa_session.flush()
            message += " %s " % group.name
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='groups',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def undelete_group( self, trans, **kwd ):
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No group ids received for undeleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='groups',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        count = 0
        undeleted_groups = ""
        for group_id in ids:
            group = get_group( trans, group_id )
            if not group.deleted:
                message = "Group '%s' has not been deleted, so it cannot be undeleted." % group.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='groups',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            group.deleted = False
            trans.sa_session.add( group )
            trans.sa_session.flush()
            count += 1
            undeleted_groups += " %s" % group.name
        message = "Undeleted %d groups: %s" % ( count, undeleted_groups )
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='groups',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def purge_group( self, trans, **kwd ):
        # This method should only be called for a Group that has previously been deleted.
        # Purging a deleted Group simply deletes all UserGroupAssociations and GroupRoleAssociations.
        params = util.Params( kwd )
        webapp = params.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No group ids received for purging"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='groups',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Purged %d groups: " % len( ids )
        for group_id in ids:
            group = get_group( trans, group_id )
            if not group.deleted:
                # We should never reach here, but just in case there is a bug somewhere...
                message = "Group '%s' has not been deleted, so it cannot be purged." % group.name
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='groups',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            # Delete UserGroupAssociations
            for uga in group.users:
                trans.sa_session.delete( uga )
            # Delete GroupRoleAssociations
            for gra in group.roles:
                trans.sa_session.delete( gra )
            trans.sa_session.flush()
            message += " %s " % group.name
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='groups',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )

    # Galaxy User Stuff
    @web.expose
    @web.require_admin
    def create_new_user( self, trans, **kwargs ):
        webapp = kwargs.get( 'webapp', 'galaxy' )
        return trans.response.send_redirect( web.url_for( controller='user',
                                                          action='create',
                                                          webapp=webapp,
                                                          admin_view=True ) )
    @web.expose
    @web.require_admin
    def reset_user_password( self, trans, **kwd ):
        webapp = kwd.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No user ids received for resetting passwords"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        if 'reset_user_password_button' in kwd:
            message = ''
            status = ''
            for user_id in ids:
                user = get_user( trans, user_id )
                password = kwd.get( 'password', None )
                confirm = kwd.get( 'confirm' , None )
                if len( password ) < 6:
                    message = "Please use a password of at least 6 characters"
                    status = 'error'
                    break
                elif password != confirm:
                    message = "Passwords do not match"
                    status = 'error'
                    break
                else:
                    user.set_password_cleartext( password )
                    trans.sa_session.add( user )
                    trans.sa_session.flush()
            if not message and not status:
                message = "Passwords reset for %d users" % len( ids )
                status = 'done'
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status=status ) )
        users = [ get_user( trans, user_id ) for user_id in ids ]
        if len( ids ) > 1:
            id=','.join( id )
        return trans.fill_template( '/admin/user/reset_password.mako',
                                    id=id,
                                    users=users,
                                    password='',
                                    confirm='',
                                    webapp=webapp )
    @web.expose
    @web.require_admin
    def mark_user_deleted( self, trans, **kwd ):
        webapp = kwd.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No user ids received for deleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Deleted %d users: " % len( ids )
        for user_id in ids:
            user = get_user( trans, user_id )
            user.deleted = True
            trans.sa_session.add( user )
            trans.sa_session.flush()
            message += " %s " % user.email
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='users',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def undelete_user( self, trans, **kwd ):
        webapp = kwd.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No user ids received for undeleting"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=message,
                                                       status='error' ) )
        ids = util.listify( id )
        count = 0
        undeleted_users = ""
        for user_id in ids:
            user = get_user( trans, user_id )
            if not user.deleted:
                message = "User '%s' has not been deleted, so it cannot be undeleted." % user.email
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='users',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            user.deleted = False
            trans.sa_session.add( user )
            trans.sa_session.flush()
            count += 1
            undeleted_users += " %s" % user.email
        message = "Undeleted %d users: %s" % ( count, undeleted_users )
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='users',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def purge_user( self, trans, **kwd ):
        # This method should only be called for a User that has previously been deleted.
        # We keep the User in the database ( marked as purged ), and stuff associated
        # with the user's private role in case we want the ability to unpurge the user 
        # some time in the future.
        # Purging a deleted User deletes all of the following:
        # - History where user_id = User.id
        #    - HistoryDatasetAssociation where history_id = History.id
        #    - Dataset where HistoryDatasetAssociation.dataset_id = Dataset.id
        # - UserGroupAssociation where user_id == User.id
        # - UserRoleAssociation where user_id == User.id EXCEPT FOR THE PRIVATE ROLE
        # - UserAddress where user_id == User.id
        # Purging Histories and Datasets must be handled via the cleanup_datasets.py script
        webapp = kwd.get( 'webapp', 'galaxy' )
        id = kwd.get( 'id', None )
        if not id:
            message = "No user ids received for purging"
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        ids = util.listify( id )
        message = "Purged %d users: " % len( ids )
        for user_id in ids:
            user = get_user( trans, user_id )
            if not user.deleted:
                # We should never reach here, but just in case there is a bug somewhere...
                message = "User '%s' has not been deleted, so it cannot be purged." % user.email
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='users',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )
            private_role = trans.app.security_agent.get_private_user_role( user )
            # Delete History
            for h in user.active_histories:
                trans.sa_session.refresh( h )
                for hda in h.active_datasets:
                    # Delete HistoryDatasetAssociation
                    d = trans.sa_session.query( trans.app.model.Dataset ).get( hda.dataset_id )
                    # Delete Dataset
                    if not d.deleted:
                        d.deleted = True
                        trans.sa_session.add( d )
                    hda.deleted = True
                    trans.sa_session.add( hda )
                h.deleted = True
                trans.sa_session.add( h )
            # Delete UserGroupAssociations
            for uga in user.groups:
                trans.sa_session.delete( uga )
            # Delete UserRoleAssociations EXCEPT FOR THE PRIVATE ROLE
            for ura in user.roles:
                if ura.role_id != private_role.id:
                    trans.sa_session.delete( ura )
            # Delete UserAddresses
            for address in user.addresses:
                trans.sa_session.delete( address )
            # Purge the user
            user.purged = True
            trans.sa_session.add( user )
            trans.sa_session.flush()
            message += "%s " % user.email
        trans.response.send_redirect( web.url_for( controller='admin',
                                                   action='users',
                                                   webapp=webapp,
                                                   message=util.sanitize_text( message ),
                                                   status='done' ) )
    @web.expose
    @web.require_admin
    def users( self, trans, **kwargs ):
        if 'operation' in kwargs:
            operation = kwargs['operation'].lower()
            if operation == "roles":
                return self.user( trans, **kwargs )
            if operation == "reset password":
                return self.reset_user_password( trans, **kwargs )
            if operation == "delete":
                return self.mark_user_deleted( trans, **kwargs )
            if operation == "undelete":
                return self.undelete_user( trans, **kwargs )
            if operation == "purge":
                return self.purge_user( trans, **kwargs )
            if operation == "create":
                return self.create_new_user( trans, **kwargs )
            if operation == "information":
                return self.user_info( trans, **kwargs )
            if operation == "manage roles and groups":
                return self.manage_roles_and_groups_for_user( trans, **kwargs )
            if operation == "tools_by_user":
                # This option is called via the ToolsColumn link in a grid subclass,
                # so we need to add user_id to kwargs since id in the subclass is tool.id,
                # and update the current sort filter, using the grid subclass's default
                # sort filter instead of this class's.
                kwargs[ 'user_id' ] = kwargs[ 'id' ]
                kwargs[ 'sort' ] = 'name'
                return trans.response.send_redirect( web.url_for( controller='admin',
                                                                  action='browse_tools',
                                                                  **kwargs ) )
        # Render the list view
        return self.user_list_grid( trans, **kwargs )
    @web.expose
    @web.require_admin
    def user_info( self, trans, **kwd ):
        '''
        This method displays the user information page which consists of login 
        information, public username, reset password & other user information 
        obtained during registration
        '''
        webapp = kwd.get( 'webapp', 'galaxy' )
        user_id = kwd.get( 'id', None )
        if not user_id:
            message += "Invalid user id (%s) received" % str( user_id )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        user = get_user( trans, user_id )
        return trans.response.send_redirect( web.url_for( controller='user',
                                                          action='show_info',
                                                          user_id=user.id,
                                                          admin_view=True,
                                                          **kwd ) )
    @web.expose
    @web.require_admin
    def name_autocomplete_data( self, trans, q=None, limit=None, timestamp=None ):
        """Return autocomplete data for user emails"""
        ac_data = ""
        for user in trans.sa_session.query( User ).filter_by( deleted=False ).filter( func.lower( User.email ).like( q.lower() + "%" ) ):
            ac_data = ac_data + user.email + "\n"
        return ac_data
    @web.expose
    @web.require_admin
    def manage_roles_and_groups_for_user( self, trans, **kwd ):
        webapp = kwd.get( 'webapp', 'galaxy' )
        user_id = kwd.get( 'id', None )
        message = ''
        status = ''
        if not user_id:
            message += "Invalid user id (%s) received" % str( user_id )
            trans.response.send_redirect( web.url_for( controller='admin',
                                                       action='users',
                                                       webapp=webapp,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        user = get_user( trans, user_id )
        private_role = trans.app.security_agent.get_private_user_role( user )
        if kwd.get( 'user_roles_groups_edit_button', False ):
            # Make sure the user is not dis-associating himself from his private role
            out_roles = kwd.get( 'out_roles', [] )
            if out_roles:
                out_roles = [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in util.listify( out_roles ) ]
            if private_role in out_roles:
                message += "You cannot eliminate a user's private role association.  "
                status = 'error'
            in_roles = kwd.get( 'in_roles', [] )
            if in_roles:
                in_roles = [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in util.listify( in_roles ) ]
            out_groups = kwd.get( 'out_groups', [] )
            if out_groups:
                out_groups = [ trans.sa_session.query( trans.app.model.Group ).get( x ) for x in util.listify( out_groups ) ]
            in_groups = kwd.get( 'in_groups', [] )
            if in_groups:
                in_groups = [ trans.sa_session.query( trans.app.model.Group ).get( x ) for x in util.listify( in_groups ) ]
            if in_roles:
                trans.app.security_agent.set_entity_user_associations( users=[ user ], roles=in_roles, groups=in_groups )
                trans.sa_session.refresh( user )
                message += "User '%s' has been updated with %d associated roles and %d associated groups (private roles are not displayed)" % \
                    ( user.email, len( in_roles ), len( in_groups ) )
                trans.response.send_redirect( web.url_for( controller='admin',
                                                           action='users',
                                                           webapp=webapp,
                                                           message=util.sanitize_text( message ),
                                                           status='done' ) )
        in_roles = []
        out_roles = []
        in_groups = []
        out_groups = []
        for role in trans.sa_session.query( trans.app.model.Role ).filter( trans.app.model.Role.table.c.deleted==False ) \
                                                                  .order_by( trans.app.model.Role.table.c.name ):
            if role in [ x.role for x in user.roles ]:
                in_roles.append( ( role.id, role.name ) )
            elif role.type != trans.app.model.Role.types.PRIVATE:
                # There is a 1 to 1 mapping between a user and a PRIVATE role, so private roles should
                # not be listed in the roles form fields, except for the currently selected user's private
                # role, which should always be in in_roles.  The check above is added as an additional
                # precaution, since for a period of time we were including private roles in the form fields.
                out_roles.append( ( role.id, role.name ) )
        for group in trans.sa_session.query( trans.app.model.Group ).filter( trans.app.model.Group.table.c.deleted==False ) \
                                                                    .order_by( trans.app.model.Group.table.c.name ):
            if group in [ x.group for x in user.groups ]:
                in_groups.append( ( group.id, group.name ) )
            else:
                out_groups.append( ( group.id, group.name ) )
        message += "User '%s' is currently associated with %d roles and is a member of %d groups" % \
            ( user.email, len( in_roles ), len( in_groups ) )
        if not status:
            status = 'done'
        return trans.fill_template( '/admin/user/user.mako',
                                    user=user,
                                    in_roles=in_roles,
                                    out_roles=out_roles,
                                    in_groups=in_groups,
                                    out_groups=out_groups,
                                    webapp=webapp,
                                    message=message,
                                    status=status )
    @web.expose
    @web.require_admin
    def memdump( self, trans, ids = 'None', sorts = 'None', pages = 'None', new_id = None, new_sort = None, **kwd ):
        if self.app.memdump is None:
            return trans.show_error_message( "Memdump is not enabled (set <code>use_memdump = True</code> in universe_wsgi.ini)" )
        heap = self.app.memdump.get()
        p = util.Params( kwd )
        msg = None
        if p.dump:
            heap = self.app.memdump.get( update = True )
            msg = "Heap dump complete"
        elif p.setref:
            self.app.memdump.setref()
            msg = "Reference point set (dump to see delta from this point)"
        ids = ids.split( ',' )
        sorts = sorts.split( ',' )
        if new_id is not None:
            ids.append( new_id )
            sorts.append( 'None' )
        elif new_sort is not None:
            sorts[-1] = new_sort
        breadcrumb = "<a href='%s' class='breadcrumb'>heap</a>" % web.url_for()
        # new lists so we can assemble breadcrumb links
        new_ids = []
        new_sorts = []
        for id, sort in zip( ids, sorts ):
            new_ids.append( id )
            if id != 'None':
                breadcrumb += "<a href='%s' class='breadcrumb'>[%s]</a>" % ( web.url_for( ids=','.join( new_ids ), sorts=','.join( new_sorts ) ), id )
                heap = heap[int(id)]
            new_sorts.append( sort )
            if sort != 'None':
                breadcrumb += "<a href='%s' class='breadcrumb'>.by('%s')</a>" % ( web.url_for( ids=','.join( new_ids ), sorts=','.join( new_sorts ) ), sort )
                heap = heap.by( sort )
        ids = ','.join( new_ids )
        sorts = ','.join( new_sorts )
        if p.theone:
            breadcrumb += ".theone"
            heap = heap.theone
        return trans.fill_template( '/admin/memdump.mako', heap = heap, ids = ids, sorts = sorts, breadcrumb = breadcrumb, msg = msg )

    @web.expose
    @web.require_admin
    def jobs( self, trans, stop = [], stop_msg = None, cutoff = 180, job_lock = None, **kwd ):
        deleted = []
        msg = None
        status = None
        if not trans.app.config.get_bool( "enable_job_running", True ):
            return trans.show_error_message( 'This Galaxy instance is not configured to run jobs.  If using multiple servers, please directly access the job running instance to manage jobs.' )
        job_ids = util.listify( stop )
        if job_ids and stop_msg in [ None, '' ]:
            msg = 'Please enter an error message to display to the user describing why the job was terminated'
            status = 'error'
        elif job_ids:
            if stop_msg[-1] not in string.punctuation:
                stop_msg += '.'
            for job_id in job_ids:
                trans.app.job_manager.job_stop_queue.put( job_id, error_msg="This job was stopped by an administrator: %s  For more information or help" % stop_msg )
                deleted.append( str( job_id ) )
        if deleted:
            msg = 'Queued job'
            if len( deleted ) > 1:
                msg += 's'
            msg += ' for deletion: '
            msg += ', '.join( deleted )
            status = 'done'
        if job_lock == 'lock':
            trans.app.job_manager.job_queue.job_lock = True
        elif job_lock == 'unlock':
            trans.app.job_manager.job_queue.job_lock = False
        cutoff_time = datetime.utcnow() - timedelta( seconds=int( cutoff ) )
        jobs = trans.sa_session.query( trans.app.model.Job ) \
                               .filter( and_( trans.app.model.Job.table.c.update_time < cutoff_time,
                                              or_( trans.app.model.Job.state == trans.app.model.Job.states.NEW,
                                                   trans.app.model.Job.state == trans.app.model.Job.states.QUEUED,
                                                   trans.app.model.Job.state == trans.app.model.Job.states.RUNNING,
                                                   trans.app.model.Job.state == trans.app.model.Job.states.UPLOAD ) ) ) \
                               .order_by( trans.app.model.Job.table.c.update_time.desc() )
        last_updated = {}
        for job in jobs:
            delta = datetime.utcnow() - job.update_time
            if delta > timedelta( minutes=60 ):
                last_updated[job.id] = '%s hours' % int( delta.seconds / 60 / 60 )
            else:
                last_updated[job.id] = '%s minutes' % int( delta.seconds / 60 )
        return trans.fill_template( '/admin/jobs.mako',
                                    jobs = jobs,
                                    last_updated = last_updated,
                                    cutoff = cutoff,
                                    msg = msg,
                                    status = status,
                                    job_lock = trans.app.job_manager.job_queue.job_lock )

## ---- Utility methods -------------------------------------------------------
        
def get_user( trans, id ):
    """Get a User from the database by id."""
    # Load user from database
    id = trans.security.decode_id( id )
    user = trans.sa_session.query( trans.model.User ).get( id )
    if not user:
        return trans.show_error_message( "User not found for id (%s)" % str( id ) )
    return user
def get_role( trans, id ):
    """Get a Role from the database by id."""
    # Load user from database
    id = trans.security.decode_id( id )
    role = trans.sa_session.query( trans.model.Role ).get( id )
    if not role:
        return trans.show_error_message( "Role not found for id (%s)" % str( id ) )
    return role
def get_group( trans, id ):
    """Get a Group from the database by id."""
    # Load user from database
    id = trans.security.decode_id( id )
    group = trans.sa_session.query( trans.model.Group ).get( id )
    if not group:
        return trans.show_error_message( "Group not found for id (%s)" % str( id ) )
    return group
