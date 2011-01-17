import os, os.path, shutil, urllib, StringIO, re, gzip, tempfile, shutil, zipfile, copy, glob, string
from galaxy.web.base.controller import *
from galaxy import util, jobs
from galaxy.datatypes import sniff
from galaxy.security import RBACAgent
from galaxy.util.json import to_json_string
from galaxy.tools.actions import upload_common
from galaxy.model.orm import *
from galaxy.util.streamball import StreamBall
from galaxy.web.form_builder import AddressField, CheckboxField, SelectField, TextArea, TextField, WorkflowField, WorkflowMappingField, HistoryField
import logging, tempfile, zipfile, tarfile, os, sys

if sys.version_info[:2] < ( 2, 6 ):
    zipfile.BadZipFile = zipfile.error
if sys.version_info[:2] < ( 2, 5 ):
    zipfile.LargeZipFile = zipfile.error

log = logging.getLogger( __name__ )

# Test for available compression types
tmpd = tempfile.mkdtemp()
comptypes = []
for comptype in ( 'gz', 'bz2' ):
    tmpf = os.path.join( tmpd, 'compression_test.tar.' + comptype )
    try:
        archive = tarfile.open( tmpf, 'w:' + comptype )
        archive.close()
        comptypes.append( comptype )
    except tarfile.CompressionError:
        log.exception( "Compression error when testing %s compression.  This option will be disabled for library downloads." % comptype )
    try:
        os.unlink( tmpf )
    except OSError:
        pass
ziptype = '32'
tmpf = os.path.join( tmpd, 'compression_test.zip' )
try:
    archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_DEFLATED, True )
    archive.close()
    comptypes.append( 'zip' )
    ziptype = '64'
except RuntimeError:
    log.exception( "Compression error when testing zip compression. This option will be disabled for library downloads." )
except (TypeError, zipfile.LargeZipFile):
    # ZIP64 is only in Python2.5+.  Remove TypeError when 2.4 support is dropped
    log.warning( 'Max zip file size is 2GB, ZIP64 not supported' )
    comptypes.append( 'zip' )
try:
    os.unlink( tmpf )
except OSError:
    pass
os.rmdir( tmpd )

class LibraryCommon( BaseController, UsesFormDefinitions ):
    @web.json
    def library_item_updates( self, trans, ids=None, states=None ):
        # Avoid caching
        trans.response.headers['Pragma'] = 'no-cache'
        trans.response.headers['Expires'] = '0'
        # Create new HTML for any that have changed
        rval = {}
        if ids is not None and states is not None:
            ids = map( int, ids.split( "," ) )
            states = states.split( "," )
            for id, state in zip( ids, states ):
                data = trans.sa_session.query( self.app.model.LibraryDatasetDatasetAssociation ).get( id )
                if data.state != state:
                    job_ldda = data
                    while job_ldda.copied_from_library_dataset_dataset_association:
                        job_ldda = job_ldda.copied_from_library_dataset_dataset_association
                    force_history_refresh = False
                    rval[id] = {
                        "state": data.state,
                        "html": unicode( trans.fill_template( "library/common/library_item_info.mako", ldda=data ), 'utf-8' )
                        #"force_history_refresh": force_history_refresh
                    }
        return rval
    @web.expose
    def browse_library( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        # If use_panels is True, the library is being accessed via an external link
        # which did not originate from within the Galaxy instance, and the library will
        # be displayed correctly with the mast head.
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        library_id = params.get( 'id', None )
        if not library_id:
            # To handle bots
            message = "You must specify a library id."
            status = 'error'
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            library = trans.sa_session.query( trans.app.model.Library ).get( trans.security.decode_id( library_id ) )
        except:
            # Protect against attempts to phish for valid keys that return libraries
            library = None
        # Most security for browsing libraries is handled in the template, but do a basic check here.
        if not library or not ( is_admin or trans.app.security_agent.can_access_library( current_user_roles, library ) ):
            message = "Invalid library id ( %s ) specified." % str( library_id )
            status = 'error'
        else:
            show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
            created_ldda_ids = params.get( 'created_ldda_ids', '' )
            hidden_folder_ids = util.listify( params.get( 'hidden_folder_ids', '' ) )
            if created_ldda_ids and not message:
                message = "%d datasets are uploading in the background to the library '%s' (each is selected).  "  % \
                    ( len( created_ldda_ids.split( ',' ) ), library.name )
                message += "Don't navigate away from Galaxy or use the browser's \"stop\" or \"reload\" buttons (on this tab) until the "
                message += "message \"This job is running\" is cleared from the \"Information\" column below for each selected dataset."
                status = "info"
            comptypes_t = comptypes
            if trans.app.config.nginx_x_archive_files_base:
                comptypes_t = ['ngxzip']
            for comptype in trans.app.config.disable_library_comptypes:
                # TODO: do this once, not every time (we're gonna raise an
                # exception every time after the first time)
                try:
                    comptypes_t.remove( comptype )
                except:
                    pass
            try:
                return trans.fill_template( '/library/common/browse_library.mako',
                                            cntrller=cntrller,
                                            use_panels=use_panels,
                                            library=library,
                                            created_ldda_ids=created_ldda_ids,
                                            hidden_folder_ids=hidden_folder_ids,
                                            show_deleted=show_deleted,
                                            comptypes=comptypes_t,
                                            current_user_roles=current_user_roles,
                                            message=message,
                                            status=status )
            except Exception, e:
                message = 'Error attempting to display contents of library (%s): %s.' % ( str( library.name ), str( e ) )
                status = 'error'
        return trans.response.send_redirect( web.url_for( use_panels=use_panels,
                                                          controller=cntrller,
                                                          action='browse_libraries',
                                                          default_action=params.get( 'default_action', None ),
                                                          message=util.sanitize_text( message ),
                                                          status=status ) )
    @web.expose
    def library_info( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        library_id = params.get( 'id', None )
        try:
            library = trans.sa_session.query( trans.app.model.Library ).get( trans.security.decode_id( library_id ) )
        except:
            library = None
        self._check_access( trans, cntrller, is_admin, library, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'library_info_button', False ):
            self._check_modify( trans, cntrller, is_admin, library, current_user_roles, use_panels, library_id, show_deleted )
            old_name = library.name
            new_name = util.restore_text( params.get( 'name', 'No name' ) )
            if not new_name:
                message = 'Enter a valid name'
                status='error'
            else:
                new_description = util.restore_text( params.get( 'description', '' ) )
                new_synopsis = util.restore_text( params.get( 'synopsis', '' ) )
                if new_synopsis in [ None, 'None' ]:
                    new_synopsis = ''
                library.name = new_name
                library.description = new_description
                library.synopsis = new_synopsis
                # Rename the root_folder
                library.root_folder.name = new_name
                library.root_folder.description = new_description
                trans.sa_session.add_all( ( library, library.root_folder ) )
                trans.sa_session.flush()
                message = "Information updated for library '%s'." % library.name
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='library_info',
                                                                  cntrller=cntrller,
                                                                  use_panels=use_panels,
                                                                  id=trans.security.encode_id( library.id ),
                                                                  show_deleted=show_deleted,
                                                                  message=util.sanitize_text( message ),
                                                                  status='done' ) )
        # See if we have any associated templates
        info_association, inherited = library.get_info_association()
        widgets = library.get_template_widgets( trans )
        widget_fields_have_contents = self.widget_fields_have_contents( widgets )
        return trans.fill_template( '/library/common/library_info.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    library=library,
                                    widgets=widgets,
                                    widget_fields_have_contents=widget_fields_have_contents,
                                    current_user_roles=current_user_roles,
                                    show_deleted=show_deleted,
                                    info_association=info_association,
                                    inherited=inherited,
                                    message=message,
                                    status=status )
    @web.expose
    def library_permissions( self, trans, cntrller, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        library_id = params.get( 'id', None )
        try:
            library = trans.sa_session.query( trans.app.model.Library ).get( trans.security.decode_id( library_id ) )
        except:
            library = None
        self._check_access( trans, cntrller, is_admin, library, current_user_roles, use_panels, library_id, show_deleted )
        self._check_manage( trans, cntrller, is_admin, library, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'update_roles_button', False ):
            # The user clicked the Save button on the 'Associate With Roles' form
            permissions = {}
            for k, v in trans.app.model.Library.permitted_actions.items():
                in_roles = [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in util.listify( params.get( k + '_in', [] ) ) ]
                permissions[ trans.app.security_agent.get_action( v.action ) ] = in_roles
            trans.app.security_agent.set_all_library_permissions( library, permissions )
            trans.sa_session.refresh( library )
            # Copy the permissions to the root folder
            trans.app.security_agent.copy_library_permissions( library, library.root_folder )
            message = "Permissions updated for library '%s'." % library.name
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='library_permissions',
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              id=trans.security.encode_id( library.id ),
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='done' ) )
        roles = trans.app.security_agent.get_legitimate_roles( trans, library, cntrller )
        return trans.fill_template( '/library/common/library_permissions.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    library=library,
                                    current_user_roles=current_user_roles,
                                    roles=roles,
                                    show_deleted=show_deleted,
                                    message=message,
                                    status=status )
    @web.expose
    def create_folder( self, trans, cntrller, parent_id, library_id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller in ( 'library_admin', 'api' )
        current_user_roles = trans.get_current_user_roles()
        try:
            parent_folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( trans.security.decode_id( parent_id ) )
        except:
            parent_folder = None
        # Check the library which actually contains the user-supplied parent folder, not the user-supplied
        # library, which could be anything.
        if parent_folder:
            parent_library = parent_folder.parent_library
        self._check_access( trans, cntrller, is_admin, parent_folder, current_user_roles, use_panels, library_id, show_deleted )
        self._check_add( trans, cntrller, is_admin, parent_folder, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'new_folder_button', False ) or cntrller == 'api':
            new_folder = trans.app.model.LibraryFolder( name=util.restore_text( params.name ),
                                                        description=util.restore_text( params.description ) )
            # We are associating the last used genome build with folders, so we will always
            # initialize a new folder with the first dbkey in util.dbnames which is currently
            # ?    unspecified (?)
            new_folder.genome_build = util.dbnames.default_value
            parent_folder.add_folder( new_folder )
            trans.sa_session.add( new_folder )
            trans.sa_session.flush()
            # New folders default to having the same permissions as their parent folder
            trans.app.security_agent.copy_library_permissions( parent_folder, new_folder )
            # If we're creating in the API, we're done
            if cntrller == 'api':
                return 200, dict( created=new_folder )
            # If we have an inheritable template, redirect to the folder_info page so information
            # can be filled in immediately.
            widgets = []
            info_association, inherited = new_folder.get_info_association()
            if info_association and ( not( inherited ) or info_association.inheritable ):
                widgets = new_folder.get_template_widgets( trans )
            if info_association:
                message = "The new folder named '%s' has been added to the data library.  " % new_folder.name
                message += "Additional information about this folder may be added using the inherited template."
                return trans.fill_template( '/library/common/folder_info.mako',
                                            cntrller=cntrller,
                                            use_panels=use_panels,
                                            folder=new_folder,
                                            library_id=library_id,
                                            widgets=widgets,
                                            current_user_roles=current_user_roles,
                                            show_deleted=show_deleted,
                                            info_association=info_association,
                                            inherited=inherited,
                                            message=message,
                                            status='done' )
            # If not inheritable info_association, redirect to the library.
            message = "The new folder named '%s' has been added to the data library." % new_folder.name
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='done' ) )
        # We do not render any template widgets on creation pages since saving the info_association
        # cannot occur before the associated item is saved.
        return trans.fill_template( '/library/common/new_folder.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    library_id=library_id,
                                    folder=parent_folder,
                                    show_deleted=show_deleted,
                                    message=message,
                                    status=status )
    @web.expose
    def folder_info( self, trans, cntrller, id, library_id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( trans.security.decode_id( id ) )
        except:
            folder = None
        self._check_access( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'rename_folder_button', False ):
            self._check_modify( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            old_name = folder.name
            new_name = util.restore_text( params.name )
            new_description = util.restore_text( params.description )
            if not new_name:
                message = 'Enter a valid name'
                status='error'
            else:
                folder.name = new_name
                folder.description = new_description
                trans.sa_session.add( folder )
                trans.sa_session.flush()
                message = "Information updated for folder '%s'." % folder.name
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='folder_info',
                                                                  cntrller=cntrller,
                                                                  use_panels=use_panels,
                                                                  id=id,
                                                                  library_id=library_id,
                                                                  show_deleted=show_deleted,
                                                                  message=util.sanitize_text( message ),
                                                                  status='done' ) )
        # See if we have any associated templates
        widgets = []
        widget_fields_have_contents = False
        info_association, inherited = folder.get_info_association()
        if info_association and ( not( inherited ) or info_association.inheritable ):
            widgets = folder.get_template_widgets( trans )
            widget_fields_have_contents = self.widget_fields_have_contents( widgets )
        return trans.fill_template( '/library/common/folder_info.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    folder=folder,
                                    library_id=library_id,
                                    widgets=widgets,
                                    widget_fields_have_contents=widget_fields_have_contents,
                                    current_user_roles=current_user_roles,
                                    show_deleted=show_deleted,
                                    info_association=info_association,
                                    inherited=inherited,
                                    message=message,
                                    status=status )
    @web.expose
    def folder_permissions( self, trans, cntrller, id, library_id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( trans.security.decode_id( id ) )
        except:
            folder = None
        self._check_access( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
        self._check_manage( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'update_roles_button', False ):
            # The user clicked the Save button on the 'Associate With Roles' form
            permissions = {}
            for k, v in trans.app.model.Library.permitted_actions.items():
                if k != 'LIBRARY_ACCESS':
                    # LIBRARY_ACCESS is a special permission set only at the library level
                    # and it is not inherited.
                    in_roles = [ trans.sa_session.query( trans.app.model.Role ).get( int( x ) ) for x in util.listify( params.get( k + '_in', [] ) ) ]
                    permissions[ trans.app.security_agent.get_action( v.action ) ] = in_roles
            trans.app.security_agent.set_all_library_permissions( folder, permissions )
            trans.sa_session.refresh( folder )
            message = "Permissions updated for folder '%s'." % folder.name
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='folder_permissions',
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              id=trans.security.encode_id( folder.id ),
                                                              library_id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='done' ) )
        # If the library is public all roles are legitimate, but if the library
        # is restricted, only those roles associated with the LIBRARY_ACCESS
        # permission are legitimate.
        roles = trans.app.security_agent.get_legitimate_roles( trans, folder.parent_library, cntrller )
        return trans.fill_template( '/library/common/folder_permissions.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    folder=folder,
                                    library_id=library_id,
                                    current_user_roles=current_user_roles,
                                    roles=roles,
                                    show_deleted=show_deleted,
                                    message=message,
                                    status=status )
    @web.expose
    def ldda_edit_info( self, trans, cntrller, library_id, folder_id, id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( id ) )
        except:
            ldda = None
        self._check_access( trans, cntrller, is_admin, ldda, current_user_roles, use_panels, library_id, show_deleted )
        self._check_modify( trans, cntrller, is_admin, ldda, current_user_roles, use_panels, library_id, show_deleted )
        dbkey = params.get( 'dbkey', '?' )
        if isinstance( dbkey, list ):
            dbkey = dbkey[0]
        file_formats = [ dtype_name for dtype_name, dtype_value in trans.app.datatypes_registry.datatypes_by_extension.iteritems() if dtype_value.allow_datatype_change ]
        file_formats.sort()
        # See if we have any associated templates
        widgets = []
        info_association, inherited = ldda.get_info_association()
        if info_association and ( not( inherited ) or info_association.inheritable ):
            widgets = ldda.get_template_widgets( trans )
        if params.get( 'change', False ):
            # The user clicked the Save button on the 'Change data type' form
            if ldda.datatype.allow_datatype_change and trans.app.datatypes_registry.get_datatype_by_extension( params.datatype ).allow_datatype_change:
                trans.app.datatypes_registry.change_datatype( ldda, params.datatype )
                trans.sa_session.flush()
                message = "Data type changed for library dataset '%s'." % ldda.name
                status = 'done'
            else:
                message = "You are unable to change datatypes in this manner. Changing %s to %s is not allowed." % ( ldda.extension, params.datatype )
                status = 'error'
        elif params.get( 'save', False ):
            # The user clicked the Save button on the 'Edit Attributes' form
            old_name = ldda.name
            new_name = util.restore_text( params.get( 'name', '' ) )
            new_info = util.restore_text( params.get( 'info', '' ) )
            new_message = util.restore_text( params.get( 'message', '' ) )
            if not new_name:
                message = 'Enter a valid name'
                status = 'error'
            else:
                ldda.name = new_name
                ldda.info = new_info
                ldda.message = new_message
                # The following for loop will save all metadata_spec items
                for name, spec in ldda.datatype.metadata_spec.items():
                    if spec.get("readonly"):
                        continue
                    optional = params.get( "is_" + name, None )
                    if optional and optional == 'true':
                        # optional element... == 'true' actually means it is NOT checked (and therefore ommitted)
                        setattr( ldda.metadata, name, None )
                    else:
                        setattr( ldda.metadata, name, spec.unwrap( params.get ( name, None ) ) )
                ldda.metadata.dbkey = dbkey
                ldda.datatype.after_setting_metadata( ldda )
                trans.sa_session.flush()
                message = "Attributes updated for library dataset '%s'." % ldda.name
                status = 'done'
        elif params.get( 'detect', False ):
            # The user clicked the Auto-detect button on the 'Edit Attributes' form
            for name, spec in ldda.datatype.metadata_spec.items():
                # We need to be careful about the attributes we are resetting
                if name not in [ 'name', 'info', 'dbkey' ]:
                    if spec.get( 'default' ):
                        setattr( ldda.metadata, name, spec.unwrap( spec.get( 'default' ) ) )
            ldda.datatype.set_meta( ldda )
            ldda.datatype.after_setting_metadata( ldda )
            trans.sa_session.flush()
            message = "Information updated for library dataset '%s'." % ldda.name
            status = 'done'
        if "dbkey" in ldda.datatype.metadata_spec and not ldda.metadata.dbkey:
            # Copy dbkey into metadata, for backwards compatability
            # This looks like it does nothing, but getting the dbkey
            # returns the metadata dbkey unless it is None, in which
            # case it resorts to the old dbkey.  Setting the dbkey
            # sets it properly in the metadata
            ldda.metadata.dbkey = ldda.dbkey
        return trans.fill_template( "/library/common/ldda_edit_info.mako",
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    ldda=ldda,
                                    library_id=library_id,
                                    file_formats=file_formats,
                                    widgets=widgets,
                                    current_user_roles=current_user_roles,
                                    show_deleted=show_deleted,
                                    info_association=info_association,
                                    inherited=inherited,
                                    message=message,
                                    status=status )
    @web.expose
    def ldda_info( self, trans, cntrller, library_id, folder_id, id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        show_associated_hdas_and_lddas = util.string_as_bool( params.get( 'show_associated_hdas_and_lddas', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( id ) )
        self._check_access( trans, cntrller, is_admin, ldda, current_user_roles, use_panels, library_id, show_deleted )
        if is_admin and show_associated_hdas_and_lddas:
            # Get all associated hdas and lddas that use the same disk file.
            associated_hdas = trans.sa_session.query( trans.model.HistoryDatasetAssociation ) \
                                              .filter( and_( trans.model.HistoryDatasetAssociation.deleted == False,
                                                             trans.model.HistoryDatasetAssociation.dataset_id == ldda.dataset_id ) ) \
                                              .all()
            associated_lddas = trans.sa_session.query( trans.model.LibraryDatasetDatasetAssociation ) \
                                               .filter( and_( trans.model.LibraryDatasetDatasetAssociation.deleted == False,
                                                              trans.model.LibraryDatasetDatasetAssociation.dataset_id == ldda.dataset_id,
                                                              trans.model.LibraryDatasetDatasetAssociation.id != ldda.id ) ) \
                                               .all()
        else:
            associated_hdas = []
            associated_lddas = [] 
        # See if we have any associated templates
        widgets = []
        widget_fields_have_contents = False
        info_association, inherited = ldda.get_info_association()
        if info_association and ( not( inherited ) or info_association.inheritable ):
            widgets = ldda.get_template_widgets( trans )
            widget_fields_have_contents = self.widget_fields_have_contents( widgets )
        return trans.fill_template( '/library/common/ldda_info.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    ldda=ldda,
                                    library=ldda.library_dataset.folder.parent_library,
                                    show_associated_hdas_and_lddas=show_associated_hdas_and_lddas,
                                    associated_hdas=associated_hdas,
                                    associated_lddas=associated_lddas,
                                    show_deleted=show_deleted,
                                    widgets=widgets,
                                    widget_fields_have_contents=widget_fields_have_contents,
                                    current_user_roles=current_user_roles,
                                    info_association=info_association,
                                    inherited=inherited,
                                    message=message,
                                    status=status )
    @web.expose
    def ldda_permissions( self, trans, cntrller, library_id, folder_id, id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        ids = util.listify( id )
        lddas = []
        libraries = []
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        for id in ids:
            try:
                ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( id ) )
            except:
                ldda = None
            if ldda:
                library = ldda.library_dataset.folder.parent_library
            self._check_access( trans, cntrller, is_admin, ldda, current_user_roles, use_panels, library_id, show_deleted )
            lddas.append( ldda )
            libraries.append( library )
        library = libraries[0]
        if filter( lambda x: x != library, libraries ):
            message = "Library datasets specified span multiple libraries."
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              id=library_id,
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
        # If access to the dataset is restricted, then use the roles associated with the DATASET_ACCESS permission to
        # determine the legitimate roles.  If the dataset is public, see if access to the library is restricted.  If
        # it is, use the roles associated with the LIBRARY_ACCESS permission to determine the legitimate roles.  If both
        # the dataset and the library are public, all roles are legitimate.  All of the datasets will have the same
        # permissions at this point.
        ldda = lddas[0]
        if trans.app.security_agent.dataset_is_public( ldda.dataset ):
            # The dataset is public, so check access to the library
            roles = trans.app.security_agent.get_legitimate_roles( trans, library, cntrller )
        else:
            roles = trans.app.security_agent.get_legitimate_roles( trans, ldda.dataset, cntrller )
        if params.get( 'update_roles_button', False ):
            a = trans.app.security_agent.get_action( trans.app.security_agent.permitted_actions.DATASET_ACCESS.action )
            permissions, in_roles, error, message = \
                trans.app.security_agent.derive_roles_from_access( trans, trans.app.security.decode_id( library_id ), cntrller, library=True, **kwd )
            for ldda in lddas:
                # Set the DATASET permissions on the Dataset.
                if error:
                    # Keep the original role associations for the DATASET_ACCESS permission on the ldda.
                    permissions[ a ] = ldda.get_access_roles( trans )
                trans.app.security_agent.set_all_dataset_permissions( ldda.dataset, permissions )
                trans.sa_session.refresh( ldda.dataset )
            # Set the LIBRARY permissions on the LibraryDataset.  The LibraryDataset and
            # LibraryDatasetDatasetAssociation will be set with the same permissions.
            permissions = {}
            for k, v in trans.app.model.Library.permitted_actions.items():
                if k != 'LIBRARY_ACCESS':
                    # LIBRARY_ACCESS is a special permission set only at the library level and it is not inherited.
                    in_roles = [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in util.listify( kwd.get( k + '_in', [] ) ) ]
                    permissions[ trans.app.security_agent.get_action( v.action ) ] = in_roles
            for ldda in lddas:
                trans.app.security_agent.set_all_library_permissions( ldda.library_dataset, permissions )
                trans.sa_session.refresh( ldda.library_dataset )
                # Set the LIBRARY permissions on the LibraryDatasetDatasetAssociation
                trans.app.security_agent.set_all_library_permissions( ldda, permissions )
                trans.sa_session.refresh( ldda )
            if error:
                status = 'error'
            else:
                if len( lddas ) == 1:
                    message = "Permissions updated for dataset '%s'." % ldda.name
                else:
                    message = 'Permissions updated for %d datasets.' % len( lddas )
                status= 'done'
            return trans.fill_template( "/library/common/ldda_permissions.mako",
                                        cntrller=cntrller,
                                        use_panels=use_panels,
                                        lddas=lddas,
                                        library_id=library_id,
                                        roles=roles,
                                        show_deleted=show_deleted,
                                        message=message,
                                        status=status )
        if len( ids ) > 1:
            # Ensure that the permissions across all library items are identical, otherwise we can't update them together.
            check_list = []
            for ldda in lddas:
                permissions = []
                # Check the library level permissions - the permissions on the LibraryDatasetDatasetAssociation
                # will always be the same as the permissions on the associated LibraryDataset.
                for library_permission in trans.app.security_agent.get_permissions( ldda.library_dataset ):
                    if library_permission.action not in permissions:
                        permissions.append( library_permission.action )
                for dataset_permission in trans.app.security_agent.get_permissions( ldda.dataset ):
                    if dataset_permission.action not in permissions:
                        permissions.append( dataset_permission.action )
                permissions.sort()
                if not check_list:
                    check_list = permissions
                if permissions != check_list:
                    message = 'The datasets you selected do not have identical permissions, so they can not be updated together'
                    trans.response.send_redirect( web.url_for( controller='library_common',
                                                               action='browse_library',
                                                               cntrller=cntrller,
                                                               use_panels=use_panels,
                                                               id=library_id,
                                                               show_deleted=show_deleted,
                                                               message=util.sanitize_text( message ),
                                                               status='error' ) )
        # Display permission form, permissions will be updated for all lddas simultaneously.
        return trans.fill_template( "/library/common/ldda_permissions.mako",
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    lddas=lddas,
                                    library_id=library_id,
                                    roles=roles,
                                    show_deleted=show_deleted,
                                    message=message,
                                    status=status )
    @web.expose
    def upload_library_dataset( self, trans, cntrller, library_id, folder_id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        ldda_message = util.restore_text( params.get( 'ldda_message', '' ) )
        deleted = util.string_as_bool( params.get( 'deleted', False ) )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        replace_id = params.get( 'replace_id', None )
        replace_dataset = None
        upload_option = params.get( 'upload_option', 'upload_file' )
        if params.get( 'files_0|space_to_tab', False ):
            space_to_tab = params.get( 'files_0|space_to_tab', '' )
        else:
            space_to_tab = params.get( 'space_to_tab', '' )
        link_data_only = params.get( 'link_data_only', '' )
        dbkey = params.get( 'dbkey', '?' )
        if isinstance( dbkey, list ):
            last_used_build = dbkey[0]
        else:
            last_used_build = dbkey
        roles = params.get( 'roles', '' )
        is_admin = trans.user_is_admin() and cntrller in ( 'library_admin', 'api' )
        current_user_roles = trans.get_current_user_roles()
        if replace_id not in [ None, 'None' ]:
            try:
                replace_dataset = trans.sa_session.query( trans.app.model.LibraryDataset ).get( trans.security.decode_id( replace_id ) )
            except:
                replace_dataset = None
            self._check_access( trans, cntrller, is_admin, replace_dataset, current_user_roles, use_panels, library_id, show_deleted )
            self._check_modify( trans, cntrller, is_admin, replace_dataset, current_user_roles, use_panels, library_id, show_deleted )
            library = replace_dataset.folder.parent_library
            folder = replace_dataset.folder
            # The name is stored - by the time the new ldda is created, replace_dataset.name
            # will point to the new ldda, not the one it's replacing.
            replace_dataset_name = replace_dataset.name
            if not last_used_build:
                last_used_build = replace_dataset.library_dataset_dataset_association.dbkey
            # Don't allow multiple datasets to be uploaded when replacing a dataset with a new version
            upload_option = 'upload_file'
        else:
            folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( trans.security.decode_id( folder_id ) )
            self._check_access( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            self._check_add( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            library = folder.parent_library
        if folder and last_used_build in [ 'None', None, '?' ]:
            last_used_build = folder.genome_build
        if params.get( 'runtool_btn', False ) or params.get( 'ajax_upload', False ) or cntrller == 'api':
            error = False
            if upload_option == 'upload_paths' and not trans.app.config.allow_library_path_paste:
                error = True
                message = '"allow_library_path_paste" is not defined in the Galaxy configuration file'
            elif upload_option == 'upload_paths' and not is_admin:
                error = True
                message = 'Uploading files via filesystem paths can only be performed by administrators'
            elif roles:
                # Check to see if the user selected roles to associate with the DATASET_ACCESS permission
                # on the dataset that would cause accessibility issues.
                vars = dict( DATASET_ACCESS_in=roles )
                permissions, in_roles, error, message = \
                    trans.app.security_agent.derive_roles_from_access( trans, library.id, cntrller, library=True, **vars )
            if error:
                if cntrller == 'api':
                    return 400, message
                trans.response.send_redirect( web.url_for( controller='library_common',
                                                           action='upload_library_dataset',
                                                           cntrller=cntrller,
                                                           library_id=library_id,
                                                           folder_id=folder_id,
                                                           replace_id=replace_id,
                                                           upload_option=upload_option,
                                                           show_deleted=show_deleted,
                                                           message=util.sanitize_text( message ),
                                                           status='error' ) )

            else:
                # See if we have any inherited templates.
                info_association, inherited = folder.get_info_association( inherited=True )
                if info_association and info_association.inheritable:
                    template_id = str( info_association.template.id )
                    widgets = folder.get_template_widgets( trans, get_contents=True )
                    processed_widgets = []
                    # The list of widgets may include an AddressField which we need to save if it is new
                    for index, widget_dict in enumerate( widgets ):
                        widget = widget_dict[ 'widget' ]
                        if isinstance( widget, AddressField ):
                            value = util.restore_text( params.get( widget.name, '' ) )
                            if value == 'new':
                                if self.field_param_values_ok( widget.name, 'AddressField', **kwd ):
                                    # Save the new address
                                    address = trans.app.model.UserAddress( user=trans.user )
                                    self.save_widget_field( trans, address, widget.name, **kwd )
                                    widget.value = str( address.id )
                                    widget_dict[ 'widget' ] = widget
                                    processed_widgets.append( widget_dict )
                                    # It is now critical to update the value of 'field_%i', replacing the string
                                    # 'new' with the new address id.  This is necessary because the upload_dataset()
                                    # method below calls the handle_library_params() method, which does not parse the
                                    # widget fields, it instead pulls form values from kwd.  See the FIXME comments in the
                                    # handle_library_params() method, and the CheckboxField code in the next conditional.
                                    kwd[ widget.name ] = str( address.id )
                                else:
                                    # The invalid address won't be saved, but we cannot display error
                                    # messages on the upload form due to the ajax upload already occurring.
                                    # When we re-engineer the upload process ( currently under way ), we
                                    # will be able to check the form values before the ajax upload occurs
                                    # in the background.  For now, we'll do nothing...
                                    pass
                        elif isinstance( widget, CheckboxField ):
                            # We need to check the value from kwd since util.Params would have munged the list if
                            # the checkbox is checked.
                            value = kwd.get( widget.name, '' )
                            if CheckboxField.is_checked( value ):
                                widget.value = 'true'
                                widget_dict[ 'widget' ] = widget
                                processed_widgets.append( widget_dict )
                                kwd[ widget.name ] = 'true'
                        else:
                            processed_widgets.append( widget_dict )
                    widgets = processed_widgets
                else:
                    template_id = 'None'
                    widgets = []
                created_outputs_dict = trans.webapp.controllers[ 'library_common' ].upload_dataset( trans,
                                                                                                    cntrller=cntrller,
                                                                                                    library_id=trans.security.encode_id( library.id ),
                                                                                                    folder_id=trans.security.encode_id( folder.id ),
                                                                                                    template_id=template_id,
                                                                                                    widgets=widgets,
                                                                                                    replace_dataset=replace_dataset,
                                                                                                    **kwd )
                if created_outputs_dict:
                    if cntrller == 'api':
                        # created_outputs_dict can only ever be a string if cntrller == 'api'
                        if type( created_outputs_dict ) == str:
                            return 400, created_outputs_dict
                        return 200, created_outputs_dict
                    total_added = len( created_outputs_dict.keys() )
                    ldda_id_list = [ str( v.id ) for k, v in created_outputs_dict.items() ]
                    created_ldda_ids=",".join( ldda_id_list )
                    if replace_dataset:
                        message = "Added %d dataset versions to the library dataset '%s' in the folder '%s'." % ( total_added, replace_dataset_name, folder.name )
                    else:
                        if not folder.parent:
                            # Libraries have the same name as their root_folder
                            message = "Added %d datasets to the library '%s' (each is selected).  " % ( total_added, folder.name )
                        else:
                            message = "Added %d datasets to the folder '%s' (each is selected).  " % ( total_added, folder.name )
                        if cntrller == 'library_admin':
                            message += "Click the Go button at the bottom of this page to edit the permissions on these datasets if necessary."
                            status='done'
                        else:
                            # Since permissions on all LibraryDatasetDatasetAssociations must be the same at this point, we only need
                            # to check one of them to see if the current user can manage permissions on them.
                            check_ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( ldda_id_list[0] )
                            if trans.app.security_agent.can_manage_library_item( current_user_roles, check_ldda ):
                                if replace_dataset:
                                    default_action = ''
                                else:
                                    message += "Click the Go button at the bottom of this page to edit the permissions on these datasets if necessary."
                                    default_action = 'manage_permissions'
                            else:
                                default_action = 'add'
                            trans.response.send_redirect( web.url_for( controller='library_common',
                                                                       action='browse_library',
                                                                       cntrller=cntrller,
                                                                       id=library_id,
                                                                       default_action=default_action,
                                                                       created_ldda_ids=created_ldda_ids,
                                                                       show_deleted=show_deleted,
                                                                       message=util.sanitize_text( message ), 
                                                                       status='done' ) )
                else:
                    created_ldda_ids = ''
                    message = "Upload failed"
                    status='error'
                    if cntrller == 'api':
                        return 400, message
                    response_code = 400
                trans.response.send_redirect( web.url_for( controller='library_common',
                                                           action='browse_library',
                                                           cntrller=cntrller,
                                                           id=library_id,
                                                           created_ldda_ids=created_ldda_ids,
                                                           show_deleted=show_deleted,
                                                           message=util.sanitize_text( message ),
                                                           status=status ) )
        # Note: if the upload form was submitted due to refresh_on_change for a form field, we cannot re-populate
        # the field for the selected file ( files_0|file_data ) if the user selected one.  This is because the value
        # attribute of the html input file type field is typically ignored by browsers as a security precaution. 
        
        # See if we have any inherited templates.
        info_association, inherited = folder.get_info_association( inherited=True )
        if info_association and info_association.inheritable:
            widgets = folder.get_template_widgets( trans, get_contents=True )
            # Retain contents of widget fields when form was submitted via refresh_on_change.
            widgets = self.populate_widgets_from_kwd( trans, widgets, **kwd )
        else:
            widgets = []
        # Send list of data formats to the upload form so the "extension" select list can be populated dynamically
        file_formats = trans.app.datatypes_registry.upload_file_formats
        # Send list of genome builds to the form so the "dbkey" select list can be populated dynamically
        def get_dbkey_options( last_used_build ):
            for dbkey, build_name in util.dbnames:
                yield build_name, dbkey, ( dbkey==last_used_build )
        dbkeys = get_dbkey_options( last_used_build )
        # Send the current history to the form to enable importing datasets from history to library
        history = trans.get_history()
        trans.sa_session.refresh( history )
        if upload_option == 'upload_file' and trans.app.config.nginx_upload_path:
            # If we're using nginx upload, override the form action -
            # url_for is intentionally not used on the base URL here -
            # nginx_upload_path is expected to include the proxy prefix if the
            # administrator intends for it to be part of the URL.
            action = trans.app.config.nginx_upload_path + '?nginx_redir=' + web.url_for( controller='library_common', action='upload_library_dataset' )
        else:
            action = web.url_for( controller='library_common', action='upload_library_dataset' )
        upload_option_select_list = self._build_upload_option_select_list( trans, upload_option, is_admin )
        roles_select_list = self._build_roles_select_list( trans, cntrller, library, util.listify( roles ) )
        return trans.fill_template( '/library/common/upload.mako',
                                    cntrller=cntrller,
                                    upload_option_select_list=upload_option_select_list,
                                    upload_option=upload_option,
                                    action=action,
                                    library_id=library_id,
                                    folder_id=folder_id,
                                    replace_dataset=replace_dataset,
                                    file_formats=file_formats,
                                    dbkeys=dbkeys,
                                    last_used_build=last_used_build,
                                    roles_select_list=roles_select_list,
                                    history=history,
                                    widgets=widgets,
                                    space_to_tab=space_to_tab,
                                    link_data_only=link_data_only,
                                    show_deleted=show_deleted,
                                    ldda_message=ldda_message,
                                    message=message,
                                    status=status )
    def upload_dataset( self, trans, cntrller, library_id, folder_id, replace_dataset=None, **kwd ):
        # Set up the traditional tool state/params
        tool_id = 'upload1'
        tool = trans.app.toolbox.tools_by_id[ tool_id ]
        state = tool.new_state( trans )
        errors = tool.update_state( trans, tool.inputs_by_page[0], state.inputs, kwd )
        tool_params = state.inputs
        dataset_upload_inputs = []
        for input_name, input in tool.inputs.iteritems():
            if input.type == "upload_dataset":
                dataset_upload_inputs.append( input )
        # Library-specific params
        params = util.Params( kwd ) # is this filetoolparam safe?
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        server_dir = util.restore_text( params.get( 'server_dir', '' ) )
        if replace_dataset not in [ None, 'None' ]:
            replace_id = trans.security.encode_id( replace_dataset.id )
        else:
            replace_id = None
        upload_option = params.get( 'upload_option', 'upload_file' )
        response_code = 200
        if upload_option == 'upload_directory':
            if server_dir in [ None, 'None', '' ]:
                response_code = 400
            if cntrller == 'library_admin' or ( cntrller == 'api' and trans.user_is_admin ):
                import_dir = trans.app.config.library_import_dir
                import_dir_desc = 'library_import_dir'
                full_dir = os.path.join( import_dir, server_dir )
            else:
                import_dir = trans.app.config.user_library_import_dir
                import_dir_desc = 'user_library_import_dir'
                if server_dir == trans.user.email:
                    full_dir = os.path.join( import_dir, server_dir )
                else:
                    full_dir = os.path.join( import_dir, trans.user.email, server_dir )
            if import_dir:
                message = 'Select a directory'
            else:
                response_code = 403
                message = '"%s" is not defined in the Galaxy configuration file' % import_dir_desc
        elif upload_option == 'upload_paths':
            if not trans.app.config.allow_library_path_paste:
                response_code = 403
                message = '"allow_library_path_paste" is not defined in the Galaxy configuration file'
        # Some error handling should be added to this method.
        try:
            # FIXME: instead of passing params here ( which have been processed by util.Params(), the original kwd
            # should be passed so that complex objects that may have been included in the initial request remain.
            library_bunch = upload_common.handle_library_params( trans, params, folder_id, replace_dataset )
        except:
            response_code = 500
            message = "Unable to parse upload parameters, please report this error."
        # Proceed with (mostly) regular upload processing if we're still errorless
        if response_code == 200:
            precreated_datasets = upload_common.get_precreated_datasets( trans, tool_params, trans.app.model.LibraryDatasetDatasetAssociation, controller=cntrller )
            if upload_option == 'upload_file':
                tool_params = upload_common.persist_uploads( tool_params )
                uploaded_datasets = upload_common.get_uploaded_datasets( trans, cntrller, tool_params, precreated_datasets, dataset_upload_inputs, library_bunch=library_bunch )
            elif upload_option == 'upload_directory':
                uploaded_datasets, response_code, message = self.get_server_dir_uploaded_datasets( trans, cntrller, params, full_dir, import_dir_desc, library_bunch, response_code, message )
            elif upload_option == 'upload_paths':
                uploaded_datasets, response_code, message = self.get_path_paste_uploaded_datasets( trans, cntrller, params, library_bunch, response_code, message )
            upload_common.cleanup_unused_precreated_datasets( precreated_datasets )
            if upload_option == 'upload_file' and not uploaded_datasets:
                response_code = 400
                message = 'Select a file, enter a URL or enter text'
        if response_code != 200:
            if cntrller == 'api':
                return ( response_code, message )
            trans.response.send_redirect( web.url_for( controller='library_common',
                                                       action='upload_library_dataset',
                                                       cntrller=cntrller,
                                                       library_id=library_id,
                                                       folder_id=folder_id,
                                                       replace_id=replace_id,
                                                       upload_option=upload_option,
                                                       show_deleted=show_deleted,
                                                       message=util.sanitize_text( message ),
                                                       status='error' ) )
        json_file_path = upload_common.create_paramfile( trans, uploaded_datasets )
        data_list = [ ud.data for ud in uploaded_datasets ]
        return upload_common.create_job( trans, tool_params, tool, json_file_path, data_list, folder=library_bunch.folder )
    def make_library_uploaded_dataset( self, trans, cntrller, params, name, path, type, library_bunch, in_folder=None ):
        library_bunch.replace_dataset = None # not valid for these types of upload
        uploaded_dataset = util.bunch.Bunch()
        # Remove compressed file extensions, if any
        new_name = name
        if new_name.endswith( '.gz' ):
            new_name = new_name.rstrip( '.gz' )
        elif new_name.endswith( '.zip' ):
            new_name = new_name.rstrip( '.zip' )
        uploaded_dataset.name = new_name
        uploaded_dataset.path = path
        uploaded_dataset.type = type
        uploaded_dataset.ext = None
        uploaded_dataset.file_type = params.file_type
        uploaded_dataset.dbkey = params.dbkey
        uploaded_dataset.space_to_tab = params.space_to_tab
        if in_folder:
            uploaded_dataset.in_folder = in_folder
        uploaded_dataset.data = upload_common.new_upload( trans, cntrller, uploaded_dataset, library_bunch )
        if params.get( 'link_data_only', False ):
            uploaded_dataset.link_data_only = True
            uploaded_dataset.data.file_name = os.path.abspath( path )
            # Since we are not copying the file into Galaxy's managed
            # default file location, the dataset should never be purgable.
            uploaded_dataset.data.dataset.purgable = False
            trans.sa_session.add_all( ( uploaded_dataset.data, uploaded_dataset.data.dataset ) )
            trans.sa_session.flush()
        return uploaded_dataset
    def get_server_dir_uploaded_datasets( self, trans, cntrller, params, full_dir, import_dir_desc, library_bunch, response_code, message ):
        files = []
        try:
            for entry in os.listdir( full_dir ):
                # Only import regular files
                path = os.path.join( full_dir, entry )
                if os.path.islink( full_dir ) and params.get( 'link_data_only', False ):
                    # If we're linking instead of copying and the
                    # sub-"directory" in the import dir is actually a symlink,
                    # dereference the symlink, but not any of its contents.
                    link_path = os.readlink( full_dir )
                    if os.path.isabs( link_path ):
                        path = os.path.join( link_path, entry )
                    else:
                        path = os.path.abspath( os.path.join( link_path, entry ) )
                elif os.path.islink( path ) and os.path.isfile( path ) and params.get( 'link_data_only', False ):
                    # If we're linking instead of copying and the "file" in the
                    # sub-directory of the import dir is actually a symlink,
                    # dereference the symlink (one dereference only, Vasili).
                    link_path = os.readlink( path )
                    if os.path.isabs( link_path ):
                        path = link_path
                    else:
                        path = os.path.abspath( os.path.join( os.path.dirname( path ), link_path ) )
                if os.path.isfile( path ):
                    files.append( path )
        except Exception, e:
            message = "Unable to get file list for configured %s, error: %s" % ( import_dir_desc, str( e ) )
            response_code = 500
            return None, response_code, message
        if not files:
            message = "The directory '%s' contains no valid files" % full_dir
            response_code = 400
            return None, response_code, message
        uploaded_datasets = []
        for file in files:
            name = os.path.basename( file )
            uploaded_datasets.append( self.make_library_uploaded_dataset( trans, cntrller, params, name, file, 'server_dir', library_bunch ) )
        return uploaded_datasets, 200, None
    def get_path_paste_uploaded_datasets( self, trans, cntrller, params, library_bunch, response_code, message ):
        if params.get( 'filesystem_paths', '' ) == '':
            message = "No paths entered in the upload form"
            response_code = 400
            return None, response_code, message
        preserve_dirs = True
        if params.get( 'dont_preserve_dirs', False ):
            preserve_dirs = False
        # locate files
        bad_paths = []
        uploaded_datasets = []
        for line in [ l.strip() for l in params.filesystem_paths.splitlines() if l.strip() ]:
            path = os.path.abspath( line )
            if not os.path.exists( path ):
                bad_paths.append( path )
                continue
            # don't bother processing if we're just going to return an error
            if not bad_paths:
                if os.path.isfile( path ):
                    name = os.path.basename( path )
                    uploaded_datasets.append( self.make_library_uploaded_dataset( trans, cntrller, params, name, path, 'path_paste', library_bunch ) )
                for basedir, dirs, files in os.walk( line ):
                    for file in files:
                        file_path = os.path.abspath( os.path.join( basedir, file ) )
                        if preserve_dirs:
                            in_folder = os.path.dirname( file_path.replace( path, '', 1 ).lstrip( '/' ) )
                        else:
                            in_folder = None
                        uploaded_datasets.append( self.make_library_uploaded_dataset( trans,
                                                                                      cntrller,
                                                                                      params,
                                                                                      file,
                                                                                      file_path,
                                                                                      'path_paste',
                                                                                      library_bunch,
                                                                                      in_folder ) )
        if bad_paths:
            message = "Invalid paths:<br><ul><li>%s</li></ul>" % "</li><li>".join( bad_paths )
            response_code = 400
            return None, response_code, message
        return uploaded_datasets, 200, None
    @web.expose
    def add_history_datasets_to_library( self, trans, cntrller, library_id, folder_id, hda_ids='', **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        ldda_message = util.restore_text( params.get( 'ldda_message', '' ) )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        replace_id = params.get( 'replace_id', None )
        replace_dataset = None
        upload_option = params.get( 'upload_option', 'import_from_history' )
        if params.get( 'files_0|space_to_tab', False ):
            space_to_tab = params.get( 'files_0|space_to_tab', '' )
        else:
            space_to_tab = params.get( 'space_to_tab', '' )
        link_data_only = params.get( 'link_data_only', '' )
        dbkey = params.get( 'dbkey', '?' )
        if isinstance( dbkey, list ):
            last_used_build = dbkey[0]
        else:
            last_used_build = dbkey
        roles = params.get( 'roles', '' )
        is_admin = trans.user_is_admin() and cntrller in ( 'library_admin', 'api' )
        current_user_roles = trans.get_current_user_roles()
        if replace_id not in [ None, 'None' ]:
            try:
                replace_dataset = trans.sa_session.query( trans.app.model.LibraryDataset ).get( trans.security.decode_id( replace_id ) )
            except:
                replace_dataset = None
            self._check_access( trans, cntrller, is_admin, replace_dataset, current_user_roles, use_panels, library_id, show_deleted )
            self._check_modify( trans, cntrller, is_admin, replace_dataset, current_user_roles, use_panels, library_id, show_deleted )
            library = replace_dataset.folder.parent_library
            folder = replace_dataset.folder
            last_used_build = replace_dataset.library_dataset_dataset_association.dbkey
        else:
            folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( trans.security.decode_id( folder_id ) )
            self._check_access( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            self._check_add( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            library = folder.parent_library
            last_used_build = folder.genome_build
        # See if the current history is empty
        history = trans.get_history()
        trans.sa_session.refresh( history )
        if not history.active_datasets:
            message = 'Your current history is empty'
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
        if params.get( 'add_history_datasets_to_library_button', False ):
            hda_ids = util.listify( hda_ids )
            if hda_ids:
                dataset_names = []
                created_ldda_ids = ''
                for hda_id in hda_ids:
                    try:
                        hda = trans.sa_session.query( trans.app.model.HistoryDatasetAssociation ).get( trans.security.decode_id( hda_id ) )
                    except:
                        hda = None
                    self._check_access( trans, cntrller, is_admin, hda, current_user_roles, use_panels, library_id, show_deleted )
                    if roles:
                        role_ids = roles.split( ',' )
                        role_obj_list = [ trans.sa_session.query( trans.model.Role ).get( role_id ) for role_id in role_ids ]
                    else:
                        role_obj_list = []
                    ldda = hda.to_library_dataset_dataset_association( trans,
                                                                       target_folder=folder,
                                                                       replace_dataset=replace_dataset,
                                                                       roles=role_obj_list,
                                                                       ldda_message=ldda_message )
                    created_ldda_ids = '%s,%s' % ( created_ldda_ids, str( ldda.id ) )
                    dataset_names.append( ldda.name )
                    if not replace_dataset:
                        # If replace_dataset is None, the Library level permissions will be taken from the folder and applied to the new 
                        # LDDA and LibraryDataset.
                        trans.app.security_agent.copy_library_permissions( folder, ldda )
                        trans.app.security_agent.copy_library_permissions( folder, ldda.library_dataset )
                    # Permissions must be the same on the LibraryDatasetDatasetAssociation and the associated LibraryDataset
                    trans.app.security_agent.copy_library_permissions( ldda.library_dataset, ldda )
                if created_ldda_ids:
                    created_ldda_ids = created_ldda_ids.lstrip( ',' )
                    ldda_id_list = created_ldda_ids.split( ',' )
                    total_added = len( ldda_id_list )
                    if replace_dataset:
                        message = "Added %d dataset versions to the library dataset '%s' in the folder '%s'." % ( total_added, replace_dataset.name, folder.name )
                    else:
                        if not folder.parent:
                            # Libraries have the same name as their root_folder
                            message = "Added %d datasets to the library '%s' (each is selected).  " % ( total_added, folder.name )
                        else:
                            message = "Added %d datasets to the folder '%s' (each is selected).  " % ( total_added, folder.name )
                        if cntrller == 'library_admin':
                            message += "Click the Go button at the bottom of this page to edit the permissions on these datasets if necessary."
                        else:
                            # Since permissions on all LibraryDatasetDatasetAssociations must be the same at this point, we only need
                            # to check one of them to see if the current user can manage permissions on them.
                            check_ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( ldda_id_list[0] )
                            if trans.app.security_agent.can_manage_library_item( current_user_roles, check_ldda ):
                                if replace_dataset:
                                    default_action = ''
                                else:
                                    message += "Click the Go button at the bottom of this page to edit the permissions on these datasets if necessary."
                                    default_action = 'manage_permissions'
                            else:
                                default_action = 'add'
                    return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                      action='browse_library',
                                                                      cntrller=cntrller,
                                                                      id=library_id,
                                                                      created_ldda_ids=created_ldda_ids,
                                                                      show_deleted=show_deleted,
                                                                      message=util.sanitize_text( message ),
                                                                      status='done' ) )
            else:
                message = 'Select at least one dataset from the list of active datasets in your current history'
                status = 'error'
                upload_option = params.get( 'upload_option', 'import_from_history' )
                widgets = self._get_populated_widgets( folder )
                # Send list of data formats to the upload form so the "extension" select list can be populated dynamically
                file_formats = trans.app.datatypes_registry.upload_file_formats
                # Send list of genome builds to the form so the "dbkey" select list can be populated dynamically
                def get_dbkey_options( last_used_build ):
                    for dbkey, build_name in util.dbnames:
                        yield build_name, dbkey, ( dbkey==last_used_build )
                dbkeys = get_dbkey_options( last_used_build )
                # Send the current history to the form to enable importing datasets from history to library
                history = trans.get_history()
                trans.sa_session.refresh( history )
                action = 'add_history_datasets_to_library'
                upload_option_select_list = self._build_upload_option_select_list( trans, upload_option, is_admin )
                roles_select_list = self._build_roles_select_list( trans, cntrller, library, util.listify( roles ) )
                return trans.fill_template( "/library/common/upload.mako",
                                            cntrller=cntrller,
                                            upload_option_select_list=upload_option_select_list,
                                            upload_option=upload_option,
                                            action=action,
                                            library_id=library_id,
                                            folder_id=folder_id,
                                            replace_dataset=replace_dataset,
                                            file_formats=file_formats,
                                            dbkeys=dbkeys,
                                            last_used_build=last_used_build,
                                            roles_select_list=roles_select_list,
                                            history=history,
                                            widgets=widgets,
                                            space_to_tab=space_to_tab,
                                            link_data_only=link_data_only,
                                            show_deleted=show_deleted,
                                            ldda_message=ldda_message,
                                            message=message,
                                            status=status )
    def _build_roles_select_list( self, trans, cntrller, library, selected_role_ids=[] ):
        # Get the list of legitimate roles to display on the upload form.  If the library is public,
        # all active roles are legitimate.  If the library is restricted by the LIBRARY_ACCESS permission, only
        # the set of all roles associated with users that have that permission are legitimate.
        legitimate_roles = trans.app.security_agent.get_legitimate_roles( trans, library, cntrller )
        if legitimate_roles:
            # Build the roles multi-select list using the list of legitimate roles, making sure to select any that
            # were selected before refresh_on_change, if one occurred.
            roles_select_list = SelectField( "roles", multiple="true", size="5" )
            for role in legitimate_roles:
                selected = str( role.id ) in selected_role_ids
                roles_select_list.add_option( text=role.name, value=str( role.id ), selected=selected )
            return roles_select_list
        else:
            return None
    def _build_upload_option_select_list( self, trans, upload_option, is_admin ):
        # Build the upload_option select list
        upload_refresh_on_change_values = [ option_value for option_value, option_label in trans.model.LibraryDataset.upload_options ]
        upload_option_select_list = SelectField( 'upload_option', 
                                                 refresh_on_change=True, 
                                                 refresh_on_change_values=upload_refresh_on_change_values )
        for option_value, option_label in trans.model.LibraryDataset.upload_options:
            if option_value == 'upload_directory':
                if is_admin and not trans.app.config.library_import_dir:
                    continue
                elif not is_admin and not trans.app.config.user_library_import_dir:
                    continue
            elif option_value == 'upload_paths':
                if not is_admin or not trans.app.config.allow_library_path_paste:
                    continue
            upload_option_select_list.add_option( option_label, option_value, selected=option_value==upload_option )
        return upload_option_select_list
    def _get_populated_widgets( self, folder ):
        # See if we have any inherited templates.
        info_association, inherited = folder.get_info_association( inherited=True )
        if info_association and info_association.inheritable:
            widgets = folder.get_template_widgets( trans, get_contents=True )
            # Retain contents of widget fields when form was submitted via refresh_on_change.
            return self.populate_widgets_from_kwd( trans, widgets, **kwd )
        else:
            return []
    @web.expose
    def download_dataset_from_folder( self, trans, cntrller, id, library_id=None, **kwd ):
        """Catches the dataset id and displays file contents as directed"""
        show_deleted = util.string_as_bool( kwd.get( 'show_deleted', False ) )
        params = util.Params( kwd )        
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( id ) )
        except:
            ldda = None
        self._check_access( trans, cntrller, is_admin, ldda, current_user_roles, use_panels, library_id, show_deleted )
        composite_extensions = trans.app.datatypes_registry.get_composite_extensions( )
        ext = ldda.extension
        if ext in composite_extensions:
            # is composite - must return a zip of contents and the html file itself - ugh - should be reversible at upload!
            # use act_on_multiple_datasets( self, trans, cntrller, library_id, ldda_ids='', **kwd ) since it does what we need
            kwd['do_action'] = 'zip'
            return self.act_on_multiple_datasets( trans, cntrller, library_id, ldda_ids=[id,], **kwd )
        else:
            mime = trans.app.datatypes_registry.get_mimetype_by_extension( ldda.extension.lower() )
            trans.response.set_content_type( mime )
            fStat = os.stat( ldda.file_name )
            trans.response.headers[ 'Content-Length' ] = int( fStat.st_size )
            valid_chars = '.,^_-()[]0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            fname = ldda.name
            fname = ''.join( c in valid_chars and c or '_' for c in fname )[ 0:150 ]
            trans.response.headers[ "Content-Disposition" ] = "attachment; filename=%s" % fname
            try:
                return open( ldda.file_name )
            except: 
                message = 'This dataset contains no content'
        return trans.response.send_redirect( web.url_for( controller='library_common',
                                                          action='browse_library',
                                                          cntrller=cntrller,
                                                          use_panels=use_panels,
                                                          id=library_id,
                                                          show_deleted=show_deleted,
                                                          message=util.sanitize_text( message ),
                                                          status='error' ) )
    @web.expose
    def library_dataset_info( self, trans, cntrller, id, library_id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            library_dataset = trans.sa_session.query( trans.app.model.LibraryDataset ).get( trans.security.decode_id( id ) )
        except:
            library_dataset = None
        self._check_access( trans, cntrller, is_admin, library_dataset, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'edit_attributes_button', False ):
            self._check_modify( trans, cntrller, is_admin, library_dataset, current_user_roles, use_panels, library_id, show_deleted )
            old_name = library_dataset.name
            new_name = util.restore_text( params.get( 'name', '' ) )
            new_info = util.restore_text( params.get( 'info', '' ) )
            if not new_name:
                message = 'Enter a valid name'
                status = 'error'
            else:
                library_dataset.name = new_name
                library_dataset.info = new_info
                trans.sa_session.add( library_dataset )
                trans.sa_session.flush()
                message = "Information updated for library dataset '%s'." % library_dataset.name
                status = 'done'
        # See if we have any associated templates
        widgets = []
        widget_fields_have_contents = False
        info_association, inherited = library_dataset.library_dataset_dataset_association.get_info_association()
        if info_association and ( not( inherited ) or info_association.inheritable ):
            widgets = library_dataset.library_dataset_dataset_association.get_template_widgets( trans )
            widget_fields_have_contents = self.widget_fields_have_contents( widgets )
        return trans.fill_template( '/library/common/library_dataset_info.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    library_dataset=library_dataset,
                                    library_id=library_id,
                                    current_user_roles=current_user_roles,
                                    info_association=info_association,
                                    inherited=inherited,
                                    widgets=widgets,
                                    widget_fields_have_contents=widget_fields_have_contents,
                                    show_deleted=show_deleted,
                                    message=message,
                                    status=status )
    @web.expose
    def library_dataset_permissions( self, trans, cntrller, id, library_id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        try:
            library_dataset = trans.sa_session.query( trans.app.model.LibraryDataset ).get( trans.security.decode_id( id ) )
        except:
            library_dataset = None
        self._check_access( trans, cntrller, is_admin, library_dataset, current_user_roles, use_panels, library_id, show_deleted )
        self._check_manage( trans, cntrller, is_admin, library_dataset, current_user_roles, use_panels, library_id, show_deleted )
        if params.get( 'update_roles_button', False ):
            # The user clicked the Save button on the 'Associate With Roles' form
            permissions = {}
            for k, v in trans.app.model.Library.permitted_actions.items():
                if k != 'LIBRARY_ACCESS':
                    # LIBRARY_ACCESS is a special permission set only at the library level
                    # and it is not inherited.
                    in_roles = [ trans.sa_session.query( trans.app.model.Role ).get( x ) for x in util.listify( kwd.get( k + '_in', [] ) ) ]
                    permissions[ trans.app.security_agent.get_action( v.action ) ] = in_roles
            # Set the LIBRARY permissions on the LibraryDataset
            # NOTE: the LibraryDataset and LibraryDatasetDatasetAssociation will be set with the same permissions
            trans.app.security_agent.set_all_library_permissions( library_dataset, permissions )
            trans.sa_session.refresh( library_dataset )
            # Set the LIBRARY permissions on the LibraryDatasetDatasetAssociation
            trans.app.security_agent.set_all_library_permissions( library_dataset.library_dataset_dataset_association, permissions )
            trans.sa_session.refresh( library_dataset.library_dataset_dataset_association )
            message = "Permisisons updated for library dataset '%s'." % library_dataset.name
            status = 'done'
        roles = trans.app.security_agent.get_legitimate_roles( trans, library_dataset, cntrller )
        return trans.fill_template( '/library/common/library_dataset_permissions.mako',
                                    cntrller=cntrller,
                                    use_panels=use_panels,
                                    library_dataset=library_dataset,
                                    library_id=library_id,
                                    roles=roles,
                                    current_user_roles=current_user_roles,
                                    show_deleted=show_deleted,
                                    message=message,
                                    status=status )
    @web.expose
    def make_library_item_public( self, trans, cntrller, library_id, item_type, id, **kwd ):
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        current_user_roles = trans.get_current_user_roles()
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        if item_type == 'library':
            library = trans.sa_session.query( trans.model.Library ).get( trans.security.decode_id( id ) )
            self._check_access( trans, cntrller, is_admin, library, current_user_roles, use_panels, library_id, show_deleted )
            self._check_manage( trans, cntrller, is_admin, library, current_user_roles, use_panels, library_id, show_deleted )
            contents = util.string_as_bool( params.get( 'contents', 'False' ) )
            trans.app.security_agent.make_library_public( library, contents=contents )
            if contents:
                message = "The data library (%s) and all it's contents have been made publicly accessible." % library.name
            else:
                message = "The data library (%s) has been made publicly accessible, but access to it's contents has been left unchanged." % library.name
        elif item_type == 'folder':
            folder = trans.sa_session.query( trans.model.LibraryFolder ).get( trans.security.decode_id( id ) )
            self._check_access( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            self._check_manage( trans, cntrller, is_admin, folder, current_user_roles, use_panels, library_id, show_deleted )
            trans.app.security_agent.make_folder_public( folder )
            message = "All of the contents of folder (%s) have been made publicly accessible." % folder.name
        elif item_type == 'ldda':
            ldda = trans.sa_session.query( trans.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( id ) )
            self._check_access( trans, cntrller, is_admin, ldda.library_dataset, current_user_roles, use_panels, library_id, show_deleted )
            self._check_manage( trans, cntrller, is_admin, ldda.library_dataset, current_user_roles, use_panels, library_id, show_deleted )
            trans.app.security_agent.make_dataset_public( ldda.dataset )
            message = "The libary dataset (%s) has been made publicly accessible." % ldda.name
        else:
            message = "Invalid item_type (%s) received." % str( item_type )
            status = 'error'
        return trans.response.send_redirect( web.url_for( controller='library_common',
                                                          action='browse_library',
                                                          cntrller=cntrller,
                                                          use_panels=use_panels,
                                                          id=library_id,
                                                          show_deleted=show_deleted,
                                                          message=util.sanitize_text( message ),
                                                          status=status ) )
    @web.expose
    def act_on_multiple_datasets( self, trans, cntrller, library_id, ldda_ids='', **kwd ):
        class NgxZip( object ):
            def __init__( self, url_base ):
                self.files = {}
                self.url_base = url_base
            def add( self, file, relpath ):
                self.files[file] = relpath
            def __str__( self ):
                rval = ''
                for fname, relpath in self.files.items():
                    crc = '-'
                    size = os.stat( fname ).st_size
                    quoted_fname = urllib.quote_plus( fname, '/' )
                    rval += '%s %i %s%s %s\r\n' % ( crc, size, self.url_base, quoted_fname, relpath )
                return rval
        # Perform an action on a list of library datasets.
        params = util.Params( kwd )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        action = params.get( 'do_action', None )
        lddas = []
        error = False
        is_admin = trans.user_is_admin() and cntrller == 'library_admin'
        current_user_roles = trans.get_current_user_roles()
        if not ldda_ids:
            error = True
            message = 'You must select at least one dataset.'
        elif not action:
            error = True
            message = 'You must select an action to perform on the selected datasets.'
        else:
            # Set up the list of lddas for later, and get permission checks out of the way so we don't have to do it in multiple places later.
            ldda_ids = util.listify( ldda_ids )
            for ldda_id in ldda_ids:
                try:
                    ldda = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ).get( trans.security.decode_id( ldda_id ) )
                except:
                    ldda = None
                if not ldda or ( not is_admin and not trans.app.security_agent.can_access_library_item( current_user_roles, ldda, trans.user ) ):
                    error = True
                    message = "Invalid library dataset id ( %s ) specified." % str( ldda_id )
                    break
                lddas.append( ldda )
            if action == 'import_to_history' or action == 'add':
                if trans.get_history() is None:
                    # Must be a bot sending a request without having a history.
                    error = True
                    message = "You do not have a current history"
            elif action == 'manage_permissions':
                if not is_admin:
                    for ldda in lddas:
                        if not ( trans.app.security_agent.can_manage_library_item( current_user_roles, ldda ) and \
                                 trans.app.security_agent.can_manage_dataset( current_user_roles, ldda.dataset ) ):
                            error = True
                            message = "You are not authorized to manage permissions on library dataset '%s'." % ldda.name
                            break
            elif action == 'delete':
                if not is_admin:
                    for ldda in lddas:
                        if not trans.app.security_agent.can_modify_library_item( current_user_roles, ldda ):
                            error = True
                            message = "You are not authorized to modify library dataset '%s'." % ldda.name
                            break
        if error:
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
        if action == 'import_to_history' or action == 'add':
            history = trans.get_history()
            total_imported_lddas = 0
            message = ''
            status = 'done'
            for ldda in lddas:
                if ldda.dataset.state in [ 'new', 'upload', 'queued', 'running', 'empty', 'discarded' ]:
                    message += "Cannot import dataset '%s' since its state is '%s'.  " % ( ldda.name, ldda.dataset.state )
                    status = 'error'
                elif ldda.dataset.state in [ 'ok', 'error' ]:
                    hda = ldda.to_history_dataset_association( target_history=history, add_to_history=True )
                    total_imported_lddas += 1
            if total_imported_lddas:
                trans.sa_session.add( history )
                trans.sa_session.flush()
                message += "%i dataset(s) have been imported into your history.  " % total_imported_lddas
        elif action == 'manage_permissions':
            trans.response.send_redirect( web.url_for( controller='library_common',
                                                       action='ldda_permissions',
                                                       cntrller=cntrller,
                                                       use_panels=use_panels,
                                                       library_id=library_id,
                                                       folder_id=trans.security.encode_id( lddas[0].library_dataset.folder.id ),
                                                       id=",".join( ldda_ids ),
                                                       show_deleted=show_deleted,
                                                       message=util.sanitize_text( message ),
                                                       status=status ) )
        elif action == 'delete':
            for ldda in lddas:
                # Do not delete the association, just delete the library_dataset.  The
                # cleanup_datasets.py script handles everything else.
                ld = ldda.library_dataset
                ld.deleted = True
                trans.sa_session.add( ld )
            trans.sa_session.flush()
            message = "The selected datasets have been removed from this data library"
        elif action in ['zip','tgz','tbz','ngxzip']:
            error = False
            killme = string.punctuation + string.whitespace
            trantab = string.maketrans(killme,'_'*len(killme))
            try:
                outext = 'zip'
                if action == 'zip':
                    # Can't use mkstemp - the file must not exist first
                    tmpd = tempfile.mkdtemp()
                    tmpf = os.path.join( tmpd, 'library_download.' + action )
                    if ziptype == '64' and trans.app.config.upstream_gzip:
                        archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_STORED, True )
                    elif ziptype == '64':
                        archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_DEFLATED, True )
                    elif trans.app.config.upstream_gzip:
                        archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_STORED )
                    else:
                        archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_DEFLATED )
                    archive.add = lambda x, y: archive.write( x, y.encode('CP437') )
                elif action == 'tgz':
                    if trans.app.config.upstream_gzip:
                        archive = util.streamball.StreamBall( 'w|' )
                        outext = 'tar'
                    else:
                        archive = util.streamball.StreamBall( 'w|gz' )
                        outext = 'tgz'
                elif action == 'tbz':
                    archive = util.streamball.StreamBall( 'w|bz2' )
                    outext = 'tbz2'
                elif action == 'ngxzip':
                    archive = NgxZip( trans.app.config.nginx_x_archive_files_base )
            except (OSError, zipfile.BadZipfile):
                error = True
                log.exception( "Unable to create archive for download" )
                message = "Unable to create archive for download, please report this error"
                status = 'error'
            except:
                 error = True
                 log.exception( "Unexpected error %s in create archive for download" % sys.exc_info()[0])
                 message = "Unable to create archive for download, please report - %s" % sys.exc_info()[0]
                 status = 'error'
            if not error:
                composite_extensions = trans.app.datatypes_registry.get_composite_extensions( )
                seen = []
                for ldda in lddas:
                    if ldda.dataset.state in [ 'new', 'upload', 'queued', 'running', 'empty', 'discarded' ]:
                        continue
                    ext = ldda.extension
                    is_composite = ext in composite_extensions
                    path = ""
                    parent_folder = ldda.library_dataset.folder
                    while parent_folder is not None:
                        # Exclude the now-hidden "root folder"
                        if parent_folder.parent is None:
                            path = os.path.join( parent_folder.library_root[0].name, path )
                            break
                        path = os.path.join( parent_folder.name, path )
                        parent_folder = parent_folder.parent
                    path += ldda.name
                    while path in seen:
                        path += '_'
                    seen.append( path )
                    zpath = os.path.split(path)[-1] # comes as base_name/fname
                    outfname,zpathext = os.path.splitext(zpath)
                    if is_composite:
                        # need to add all the components from the extra_files_path to the zip
                        if zpathext == '':
                            zpath = '%s.html' % zpath # fake the real nature of the html file 
                        try:
                            archive.add(ldda.dataset.file_name,zpath) # add the primary of a composite set
                        except IOError:
                            error = True
                            log.exception( "Unable to add composite parent %s to temporary library download archive" % ldda.dataset.file_name)
                            message = "Unable to create archive for download, please report this error"
                            status = 'error'
                            continue                                
                        flist = glob.glob(os.path.join(ldda.dataset.extra_files_path,'*.*')) # glob returns full paths
                        for fpath in flist:
                            efp,fname = os.path.split(fpath)
                            if fname > '':
                                fname = fname.translate(trantab)
                            try:
                                archive.add( fpath,fname )
                            except IOError:
                                error = True
                                log.exception( "Unable to add %s to temporary library download archive %s" % (fname,outfname))
                                message = "Unable to create archive for download, please report this error"
                                status = 'error'
                                continue
                    else: # simple case
                        try:
                            archive.add( ldda.dataset.file_name, path )
                        except IOError:
                            error = True
                            log.exception( "Unable to write %s to temporary library download archive" % ldda.dataset.file_name)
                            message = "Unable to create archive for download, please report this error"
                            status = 'error'                            
                if not error:
                    lname = trans.sa_session.query( trans.app.model.Library ).get( trans.security.decode_id( library_id ) ).name
                    fname = lname.replace( ' ', '_' ) + '_files'
                    if action == 'zip':
                        archive.close()
                        tmpfh = open( tmpf )
                        # clean up now
                        try:
                            os.unlink( tmpf )
                            os.rmdir( tmpd )
                        except OSError:
                            error = True
                            log.exception( "Unable to remove temporary library download archive and directory" )
                            message = "Unable to create archive for download, please report this error"
                            status = 'error'
                        if not error:
                            trans.response.set_content_type( "application/x-zip-compressed" )
                            trans.response.headers[ "Content-Disposition" ] = "attachment; filename=%s.%s" % (fname,outext)
                            return tmpfh
                    elif action == 'ngxzip':
                        trans.response.set_content_type( "application/zip" )
                        trans.response.headers[ "Content-Disposition" ] = "attachment; filename=%s.%s" % (fname,outext)
                        trans.response.headers[ "X-Archive-Files" ] = "zip"
                        return archive
                    else:
                        trans.response.set_content_type( "application/x-tar" )
                        trans.response.headers[ "Content-Disposition" ] = "attachment; filename=%s.%s" % (fname,outext)
                        archive.wsgi_status = trans.response.wsgi_status()
                        archive.wsgi_headeritems = trans.response.wsgi_headeritems()
                        return archive.stream
        else:
            status = 'error'
            message = 'Invalid action ( %s ) specified.' % action
        return trans.response.send_redirect( web.url_for( controller='library_common',
                                                          action='browse_library',
                                                          cntrller=cntrller,
                                                          use_panels=use_panels,
                                                          id=library_id,
                                                          show_deleted=show_deleted,
                                                          message=util.sanitize_text( message ),
                                                          status=status ) )
    @web.expose
    def manage_template_inheritance( self, trans, cntrller, item_type, library_id, folder_id=None, ldda_id=None, **kwd ):
        params = util.Params( kwd )
        show_deleted = util.string_as_bool( params.get( 'show_deleted', False ) )
        use_panels = util.string_as_bool( params.get( 'use_panels', False ) )
        message = util.restore_text( params.get( 'message', ''  ) )
        status = params.get( 'status', 'done' )
        is_admin = ( trans.user_is_admin() and cntrller == 'library_admin' )
        current_user_roles = trans.get_current_user_roles()
        try:
            item, item_desc, action, id = self.get_item_and_stuff( trans,
                                                                   item_type=item_type,
                                                                   library_id=library_id,
                                                                   folder_id=folder_id,
                                                                   ldda_id=ldda_id,
                                                                   is_admin=is_admin )
        except ValueError:
            return None
        if not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, item ) ):
            message = "You are not authorized to modify %s '%s'." % ( item_desc, item.name )
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
        info_association, inherited = item.get_info_association( restrict=True )
        if info_association:
            if info_association.inheritable:
                message = "The template for this %s will no longer be inherited to contained folders and datasets." % item_desc
            else:
                message = "The template for this %s will now be inherited to contained folders and datasets." % item_desc
            info_association.inheritable = not( info_association.inheritable )
            trans.sa_session.add( info_association )
            trans.sa_session.flush()
        return trans.response.send_redirect( web.url_for( controller='library_common',
                                                          action=action,
                                                          cntrller=cntrller,
                                                          use_panels=use_panels,
                                                          library_id=library_id,
                                                          folder_id=folder_id,
                                                          id=id,
                                                          show_deleted=show_deleted,
                                                          message=util.sanitize_text( message ),
                                                          status='done' ) )
    @web.expose
    def delete_library_item( self, trans, cntrller, library_id, item_id, item_type, **kwd ):
        # This action will handle deleting all types of library items.  State is saved for libraries and
        # folders ( i.e., if undeleted, the state of contents of the library or folder will remain, so previously
        # deleted / purged contents will have the same state ).  When a library or folder has been deleted for
        # the amount of time defined in the cleanup_datasets.py script, the library or folder and all of its
        # contents will be purged.  The association between this method and the cleanup_datasets.py script
        # enables clean maintenance of libraries and library dataset disk files.  This is also why the item_types
        # are not any of the associations ( the cleanup_datasets.py script handles everything ).
        show_deleted = util.string_as_bool( kwd.get( 'show_deleted', False ) )
        item_types = { 'library': trans.app.model.Library,
                       'folder': trans.app.model.LibraryFolder,
                       'library_dataset': trans.app.model.LibraryDataset }
        is_admin = ( trans.user_is_admin() and cntrller == 'library_admin' )
        current_user_roles = trans.get_current_user_roles()
        if item_type not in item_types:
            message = 'Bad item_type specified: %s' % str( item_type )
            status = 'error'
        else:
            if item_type == 'library_dataset':
                item_desc = 'Dataset'
            else:
                item_desc = item_type.capitalize()
            try:
                library_item = trans.sa_session.query( item_types[ item_type ] ).get( trans.security.decode_id( item_id ) )
            except:
                library_item = None
            if not library_item or not ( is_admin or trans.app.security_agent.can_access_library_item( current_user_roles, library_item, trans.user ) ):
                message = 'Invalid %s id ( %s ) specifield.' % ( item_desc, item_id )
                status = 'error'
            elif not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, library_item ) ):
                message = "You are not authorized to delete %s '%s'." % ( item_desc, library_item.name )
                status = 'error'
            else:
                library_item.deleted = True
                trans.sa_session.add( library_item )
                trans.sa_session.flush()
                message = util.sanitize_text( "%s '%s' has been marked deleted" % ( item_desc, library_item.name ) )
                status = 'done'
        if item_type == 'library':
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_libraries',
                                                              message=message,
                                                              status=status ) )
        else:
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=message,
                                                              status=status ) )
    @web.expose
    def undelete_library_item( self, trans, cntrller, library_id, item_id, item_type, **kwd ):
        # This action will handle undeleting all types of library items
        show_deleted = util.string_as_bool( kwd.get( 'show_deleted', False ) )
        item_types = { 'library': trans.app.model.Library,
                       'folder': trans.app.model.LibraryFolder,
                       'library_dataset': trans.app.model.LibraryDataset }
        is_admin = ( trans.user_is_admin() and cntrller == 'library_admin' )
        current_user_roles = trans.get_current_user_roles()
        if item_type not in item_types:
            message = 'Bad item_type specified: %s' % str( item_type )
            status = ERROR
        else:
            if item_type == 'library_dataset':
                item_desc = 'Dataset'
            else:
                item_desc = item_type.capitalize()
            try:
                library_item = trans.sa_session.query( item_types[ item_type ] ).get( trans.security.decode_id( item_id ) )
            except:
                library_item = None
            if not library_item or not ( is_admin or trans.app.security_agent.can_access_library_item( current_user_roles, library_item, trans.user ) ):
                message = 'Invalid %s id ( %s ) specifield.' % ( item_desc, item_id )
                status = 'error'
            elif library_item.purged:
                message = '%s %s has been purged, so it cannot be undeleted' % ( item_desc, library_item.name )
                status = ERROR
            elif not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, library_item ) ):
                message = "You are not authorized to delete %s '%s'." % ( item_desc, library_item.name )
                status = 'error'
            else:
                library_item.deleted = False
                trans.sa_session.add( library_item )
                trans.sa_session.flush()
                message = util.sanitize_text( "%s '%s' has been marked undeleted" % ( item_desc, library_item.name ) )
                status = SUCCESS
        if item_type == 'library':
            return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                              action='browse_libraries',
                                                              message=message,
                                                              status=status ) )
        else:
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=message,
                                                              status=status ) )
    def _check_access( self, trans, cntrller, is_admin, item, current_user_roles, use_panels, library_id, show_deleted ):
        can_access = True
        if isinstance( item, trans.model.HistoryDatasetAssociation ):
            # Make sure the user has the DATASET_ACCESS permission on the history_dataset_association.
            if not item:
                message = "Invalid history dataset (%s) specified." % str( item )
                can_access = False
            elif not trans.app.security_agent.can_access_dataset( current_user_roles, item.dataset ) and item.history.user==trans.user:
                message = "You do not have permission to access the history dataset with id (%s)." % str( item.id )
                can_access = False
        else:
            # Make sure the user has the LIBRARY_ACCESS permission on the library item.
            if not item:
                message = "Invalid library item (%s) specified." % str( item )
                can_access = False
            elif not ( is_admin or trans.app.security_agent.can_access_library_item( current_user_roles, item, trans.user ) ):
                if isinstance( item, trans.model.Library ):
                    item_type = 'data library'
                elif isinstance( item, trans.model.LibraryFolder ):
                    item_type = 'folder'
                else:
                    item_type = '(unknown item type)'
                message = "You do not have permission to access the %s with id (%s)." % ( item_type, str( item.id ) )
                can_access = False
        if not can_access:
            if cntrller == 'api':
                return 400, message
            if isinstance( item, trans.model.Library ):
                return trans.response.send_redirect( web.url_for( controller=cntrller,
                                                                  action='browse_libraries',
                                                                  cntrller=cntrller,
                                                                  use_panels=use_panels,
                                                                  message=util.sanitize_text( message ),
                                                                  status='error' ) )
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
    def _check_add( self, trans, cntrller, is_admin, item, current_user_roles, use_panels, library_id, show_deleted ):
        # Deny access if the user is not an admin and does not have the LIBRARY_ADD permission.
        if not ( is_admin or trans.app.security_agent.can_add_library_item( current_user_roles, item ) ):
            message = "You are not authorized to add an item to (%s)." % item.name
            # Redirect to the real parent library since we know we have access to it.
            if cntrller == 'api':
                return 403, message
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              id=library_id,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
    def _check_manage( self, trans, cntrller, is_admin, item, current_user_roles, use_panels, library_id, show_deleted ):
        if isinstance( item, trans.model.LibraryDataset ):
            # Deny access if the user is not an admin and does not have the LIBRARY_MANAGE and DATASET_MANAGE_PERMISSIONS permissions.
            if not ( is_admin or \
                     ( trans.app.security_agent.can_manage_library_item( current_user_roles, item ) and 
                       trans.app.security_agent.can_manage_dataset( current_user_roles, library_dataset.library_dataset_dataset_association.dataset ) ) ):
                message = "You are not authorized to manage permissions on library dataset (%s)." % library_dataset.name
                if cntrller == 'api':
                    return 403, message
                return trans.response.send_redirect( web.url_for( controller='library_common',
                                                                  action='browse_library',
                                                                  id=library_id,
                                                                  cntrller=cntrller,
                                                                  use_panels=use_panels,
                                                                  message=util.sanitize_text( message ),
                                                                  status='error' ) )
        # Deny access if the user is not an admin and does not have the LIBRARY_MANAGE permission.
        if not ( is_admin or trans.app.security_agent.can_manage_library_item( current_user_roles, item ) ):
            message = "You are not authorized to manage permissions on (%s)." % item.name
            if cntrller == 'api':
                return 403, message
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              id=library_id,
                                                              cntrller=cntrller,
                                                              use_panels=use_panels,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )
    def _check_modify( self, trans, cntrller, is_admin, item, current_user_roles, use_panels, library_id, show_deleted ):
        # Deny modification if the user is not an admin and does not have the LIBRARY_MODIFY permission.
        if not ( is_admin or trans.app.security_agent.can_modify_library_item( current_user_roles, item ) ):
            message = "You are not authorized to modify (%s)." % item.name
            if cntrller == 'api':
                return 403, message
            return trans.response.send_redirect( web.url_for( controller='library_common',
                                                              action='browse_library',
                                                              cntrller=cntrller,
                                                              id=library_id,
                                                              use_panels=use_panels,
                                                              show_deleted=show_deleted,
                                                              message=util.sanitize_text( message ),
                                                              status='error' ) )

# ---- Utility methods -------------------------------------------------------

def active_folders( trans, folder ):
    # Much faster way of retrieving all active sub-folders within a given folder than the
    # performance of the mapper.  This query also eagerloads the permissions on each folder.
    return trans.sa_session.query( trans.app.model.LibraryFolder ) \
                           .filter_by( parent=folder, deleted=False ) \
                           .options( eagerload_all( "actions" ) ) \
                           .order_by( trans.app.model.LibraryFolder.table.c.name ) \
                           .all()
def activatable_folders( trans, folder ):
    return trans.sa_session.query( trans.app.model.LibraryFolder ) \
                           .filter_by( parent=folder, purged=False ) \
                           .options( eagerload_all( "actions" ) ) \
                           .order_by( trans.app.model.LibraryFolder.table.c.name ) \
                           .all()
def active_folders_and_lddas( trans, folder ):
    folders = active_folders( trans, folder )
    # This query is much faster than the folder.active_library_datasets property
    lddas = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ) \
                            .filter_by( deleted=False ) \
                            .join( "library_dataset" ) \
                            .filter( trans.app.model.LibraryDataset.table.c.folder_id==folder.id ) \
                            .order_by( trans.app.model.LibraryDatasetDatasetAssociation.table.c.name ) \
                            .all()
    return folders, lddas
def activatable_folders_and_lddas( trans, folder ):
    folders = activatable_folders( trans, folder )
    # This query is much faster than the folder.activatable_library_datasets property
    lddas = trans.sa_session.query( trans.app.model.LibraryDatasetDatasetAssociation ) \
                            .join( "library_dataset" ) \
                            .filter( trans.app.model.LibraryDataset.table.c.folder_id==folder.id ) \
                            .join( "dataset" ) \
                            .filter( trans.app.model.Dataset.table.c.deleted==False ) \
                            .order_by( trans.app.model.LibraryDatasetDatasetAssociation.table.c.name ) \
                            .all()
    return folders, lddas
def branch_deleted( folder ):
    # Return True if a folder belongs to a branch that has been deleted
    if folder.deleted:
        return True
    if folder.parent:
        return branch_deleted( folder.parent )
    return False
def get_containing_library_from_library_dataset( trans, library_dataset ):
    """Given a library_dataset, get the containing library"""
    folder = library_dataset.folder
    while folder.parent:
        folder = folder.parent
    # We have folder set to the library's root folder, which has the same name as the library
    for library in trans.sa_session.query( trans.model.Library ) \
                                   .filter( and_( trans.model.Library.table.c.deleted == False,
                                                  trans.model.Library.table.c.name == folder.name ) ):
        # Just to double-check
        if library.root_folder == folder:
            return library
    return None
