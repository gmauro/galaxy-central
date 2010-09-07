import logging, os, string, shutil, re, socket, mimetypes, smtplib, urllib, tempfile, zipfile, glob, sys

from galaxy.web.base.controller import *
from galaxy.web.framework.helpers import time_ago, iff, grids
from galaxy import util, datatypes, jobs, web, model
from cgi import escape, FieldStorage
from galaxy.datatypes.display_applications.util import encode_dataset_user, decode_dataset_user
from galaxy.util.sanitize_html import sanitize_html
from galaxy.model.item_attrs import *

from email.MIMEText import MIMEText
import pkg_resources; 
pkg_resources.require( "Paste" )
import paste.httpexceptions

if sys.version_info[:2] < ( 2, 6 ):
    zipfile.BadZipFile = zipfile.error
if sys.version_info[:2] < ( 2, 5 ):
    zipfile.LargeZipFile = zipfile.error

tmpd = tempfile.mkdtemp()
comptypes=[]
ziptype = '32'
tmpf = os.path.join( tmpd, 'compression_test.zip' )
try:
    archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_DEFLATED, True )
    archive.close()
    comptypes.append( 'zip' )
    ziptype = '64'
except RuntimeError:
    log.exception( "Compression error when testing zip compression. This option will be disabled for library downloads." )
except (TypeError, zipfile.LargeZipFile):    # ZIP64 is only in Python2.5+.  Remove TypeError when 2.4 support is dropped
    log.warning( 'Max zip file size is 2GB, ZIP64 not supported' )    
    comptypes.append( 'zip' )
try:
    os.unlink( tmpf )
except OSError:
    pass
os.rmdir( tmpd )

log = logging.getLogger( __name__ )

error_report_template = """
GALAXY TOOL ERROR REPORT
------------------------

This error report was sent from the Galaxy instance hosted on the server
"${host}"
-----------------------------------------------------------------------------
This is in reference to dataset id ${dataset_id} from history id ${history_id}
-----------------------------------------------------------------------------
You should be able to view the history containing the related history item

${hid}: ${history_item_name} 

by logging in as a Galaxy admin user to the Galaxy instance referenced above
and pointing your browser to the following link.

${history_view_link}
-----------------------------------------------------------------------------
The user '${email}' provided the following information:

${message}
-----------------------------------------------------------------------------
job id: ${job_id}
tool id: ${job_tool_id}
-----------------------------------------------------------------------------
job command line:
${job_command_line}
-----------------------------------------------------------------------------
job stderr:
${job_stderr}
-----------------------------------------------------------------------------
job stdout:
${job_stdout}
-----------------------------------------------------------------------------
job info:
${job_info}
-----------------------------------------------------------------------------
job traceback:
${job_traceback}
-----------------------------------------------------------------------------
(This is an automated message).
"""

class HistoryDatasetAssociationListGrid( grids.Grid ):
    # Custom columns for grid.
    class HistoryColumn( grids.GridColumn ):
        def get_value( self, trans, grid, hda):
            return hda.history.name
            
    class StatusColumn( grids.GridColumn ):
        def get_value( self, trans, grid, hda ):
            if hda.deleted:
                return "deleted"
            return ""
        def get_accepted_filters( self ):
            """ Returns a list of accepted filters for this column. """
            accepted_filter_labels_and_vals = { "Active" : "False", "Deleted" : "True", "All": "All" }
            accepted_filters = []
            for label, val in accepted_filter_labels_and_vals.items():
               args = { self.key: val }
               accepted_filters.append( grids.GridColumnFilter( label, args) )
            return accepted_filters

    # Grid definition
    title = "Saved Datasets"
    model_class = model.HistoryDatasetAssociation
    template='/dataset/grid.mako'
    default_sort_key = "-update_time"
    columns = [
        grids.TextColumn( "Name", key="name", 
                            # Link name to dataset's history.
                            link=( lambda item: iff( item.history.deleted, None, dict( operation="switch", id=item.id ) ) ), filterable="advanced", attach_popup=True ),
        HistoryColumn( "History", key="history", 
                        link=( lambda item: iff( item.history.deleted, None, dict( operation="switch_history", id=item.id ) ) ) ),
        grids.IndividualTagsColumn( "Tags", key="tags", model_tag_association_class=model.HistoryDatasetAssociationTagAssociation, filterable="advanced", grid_name="HistoryDatasetAssocationListGrid" ),
        StatusColumn( "Status", key="deleted", attach_popup=False ),
        grids.GridColumn( "Last Updated", key="update_time", format=time_ago ),
    ]
    columns.append( 
        grids.MulticolFilterColumn(  
        "Search", 
        cols_to_filter=[ columns[0], columns[2] ], 
        key="free-text-search", visible=False, filterable="standard" )
                )
    operations = [
        grids.GridOperation( "Copy to current history", condition=( lambda item: not item.deleted ), async_compatible=False ),
    ]
    standard_filters = []
    default_filter = dict( name="All", deleted="False", tags="All" )
    preserve_state = False
    use_paging = True
    num_rows_per_page = 50
    def build_initial_query( self, trans, **kwargs ):
        # Show user's datasets that are not deleted, not in deleted histories, and not hidden.
        # To filter HDAs by user, need to join model class/HDA and History table so that it is 
        # possible to filter by user. However, for dictionary-based filtering to work, need a 
        # primary table for the query.
        return trans.sa_session.query( self.model_class ).select_from( self.model_class.table.join( model.History.table ) ) \
                .filter( model.History.user == trans.user ) \
                .filter( self.model_class.deleted==False ) \
                .filter( model.History.deleted==False ) \
                .filter( self.model_class.visible==True )
        
class DatasetInterface( BaseController, UsesAnnotations, UsesHistoryDatasetAssociation, UsesItemRatings ):
        
    stored_list_grid = HistoryDatasetAssociationListGrid()

    @web.expose
    def errors( self, trans, id ):
        hda = trans.sa_session.query( model.HistoryDatasetAssociation ).get( id )
        return trans.fill_template( "dataset/errors.mako", hda=hda )
    @web.expose
    def stderr( self, trans, id ):
        dataset = trans.sa_session.query( model.HistoryDatasetAssociation ).get( id )
        job = dataset.creating_job_associations[0].job
        trans.response.set_content_type( 'text/plain' )
        return job.stderr
    @web.expose
    def report_error( self, trans, id, email='', message="" ):
        smtp_server = trans.app.config.smtp_server
        if smtp_server is None:
            return trans.show_error_message( "Mail is not configured for this galaxy instance" )
        to_address = trans.app.config.error_email_to
        if to_address is None:
            return trans.show_error_message( "Error reporting has been disabled for this galaxy instance" )
        # Get the dataset and associated job
        hda = trans.sa_session.query( model.HistoryDatasetAssociation ).get( id )
        job = hda.creating_job_associations[0].job
        # Get the name of the server hosting the Galaxy instance from which this report originated
        host = trans.request.host
        history_view_link = "%s/history/view?id=%s" % ( str( host ), trans.security.encode_id( hda.history_id ) )
        # Build the email message
        msg = MIMEText( string.Template( error_report_template )
            .safe_substitute( host=host,
                              dataset_id=hda.dataset_id,
                              history_id=hda.history_id,
                              hid=hda.hid,
                              history_item_name=hda.get_display_name(),
                              history_view_link=history_view_link,
                              job_id=job.id,
                              job_tool_id=job.tool_id,
                              job_command_line=job.command_line,
                              job_stderr=job.stderr,
                              job_stdout=job.stdout,
                              job_info=job.info,
                              job_traceback=job.traceback,
                              email=email, 
                              message=message ) )
        frm = to_address
        # Check email a bit
        email = email.strip()
        parts = email.split()
        if len( parts ) == 1 and len( email ) > 0:
            to = to_address + ", " + email
        else:
            to = to_address
        msg[ 'To' ] = to
        msg[ 'From' ] = frm
        msg[ 'Subject' ] = "Galaxy tool error report from " + email
        # Send it
        try:
            s = smtplib.SMTP()
            s.connect( smtp_server )
            s.sendmail( frm, [ to ], msg.as_string() )
            s.close()
            return trans.show_ok_message( "Your error report has been sent" )
        except Exception, e:
            return trans.show_error_message( "An error occurred sending the report by email: %s" % str( e ) )
    
    @web.expose
    def default(self, trans, dataset_id=None, **kwd):
        return 'This link may not be followed from within Galaxy.'
    
    @web.expose
    def archive_composite_dataset( self, trans, data=None, **kwd ):
        # save a composite object into a compressed archive for downloading
        params = util.Params( kwd )
        valid_chars = '.,^_-()[]0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        outfname = data.name[0:150]
        outfname = ''.join(c in valid_chars and c or '_' for c in outfname)
        if (params.do_action == None):
     	    params.do_action = 'zip' # default
        msg = util.restore_text( params.get( 'msg', ''  ) )
        messagetype = params.get( 'messagetype', 'done' )
        if not data:
            msg = "You must select at least one dataset"
            messagetype = 'error'
        else:
            error = False
            try:
                if (params.do_action == 'zip'): 
                    # Can't use mkstemp - the file must not exist first
                    tmpd = tempfile.mkdtemp()
                    tmpf = os.path.join( tmpd, 'library_download.' + params.do_action )
                    if ziptype == '64':
                        archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_DEFLATED, True )
                    else:
                        archive = zipfile.ZipFile( tmpf, 'w', zipfile.ZIP_DEFLATED )
                    archive.add = lambda x, y: archive.write( x, y.encode('CP437') )
                elif params.do_action == 'tgz':
                    archive = util.streamball.StreamBall( 'w|gz' )
                elif params.do_action == 'tbz':
                    archive = util.streamball.StreamBall( 'w|bz2' )
            except (OSError, zipfile.BadZipFile):
                error = True
                log.exception( "Unable to create archive for download" )
                msg = "Unable to create archive for %s for download, please report this error" % outfname
                messagetype = 'error'
            if not error:
                current_user_roles = trans.get_current_user_roles()
                ext = data.extension
                path = data.file_name
                fname = os.path.split(path)[-1]
                efp = data.extra_files_path
                htmlname = os.path.splitext(outfname)[0]
                if not htmlname.endswith(ext):
                    htmlname = '%s_%s' % (htmlname,ext)
                archname = '%s.html' % htmlname # fake the real nature of the html file
                try:
                    archive.add(data.file_name,archname)
                except IOError:
                    error = True
                    log.exception( "Unable to add composite parent %s to temporary library download archive" % data.file_name)
                    msg = "Unable to create archive for download, please report this error"
                    messagetype = 'error'
                flist = glob.glob(os.path.join(efp,'*.*')) # glob returns full paths
                for fpath in flist:
                    efp,fname = os.path.split(fpath)
                    try:
                        archive.add( fpath,fname )
                    except IOError:
                        error = True
                        log.exception( "Unable to add %s to temporary library download archive" % fname)
                        msg = "Unable to create archive for download, please report this error"
                        messagetype = 'error'
                        continue
                if not error:    
                    if params.do_action == 'zip':
                        archive.close()
                        tmpfh = open( tmpf )
                        # clean up now
                        try:
                            os.unlink( tmpf )
                            os.rmdir( tmpd )
                        except OSError:
                            error = True
                            msg = "Unable to remove temporary library download archive and directory"
                            log.exception( msg )
                            messagetype = 'error'
                        if not error:
                            trans.response.set_content_type( "application/x-zip-compressed" )
                            trans.response.headers[ "Content-Disposition" ] = "attachment; filename=%s.zip" % outfname 
                            return tmpfh
                    else:
                        trans.response.set_content_type( "application/x-tar" )
                        outext = 'tgz'
                        if params.do_action == 'tbz':
                            outext = 'tbz'
                        trans.response.headers[ "Content-Disposition" ] = "attachment; filename=%s.%s" % (outfname,outext) 
                        archive.wsgi_status = trans.response.wsgi_status()
                        archive.wsgi_headeritems = trans.response.wsgi_headeritems()
                        return archive.stream
        return trans.show_error_message( msg )


    
    @web.expose
    def display(self, trans, dataset_id=None, preview=False, filename=None, to_ext=None, **kwd):
        """Catches the dataset id and displays file contents as directed"""
        composite_extensions = trans.app.datatypes_registry.get_composite_extensions( )
        composite_extensions.append('html') # for archiving composite datatypes
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
            raise paste.httpexceptions.HTTPRequestRangeNotSatisfiable( "Invalid reference dataset id: %s." % str( dataset_id ) )
        current_user_roles = trans.get_current_user_roles()
        if trans.app.security_agent.can_access_dataset( current_user_roles, data.dataset ):
            if data.state == trans.model.Dataset.states.UPLOAD:
                return trans.show_error_message( "Please wait until this dataset finishes uploading before attempting to view it." )
            
            if filename and filename != "index":
                # For files in extra_files_path
                file_path = os.path.join( data.extra_files_path, filename )
                if os.path.exists( file_path ):
                    mime, encoding = mimetypes.guess_type( file_path )
                    if not mime:
                        try:
                            mime = trans.app.datatypes_registry.get_mimetype_by_extension( ".".split( file_path )[-1] )
                        except:
                            mime = "text/plain"
                
                    trans.response.set_content_type( mime )
                    return open( file_path )
                else:
                    return "Could not find '%s' on the extra files path %s." % (filename,file_path)
            
            mime = trans.app.datatypes_registry.get_mimetype_by_extension( data.extension.lower() )
            trans.response.set_content_type(mime)
            trans.log_event( "Display dataset id: %s" % str( dataset_id ) )
            
            if to_ext: # Saving the file
                if data.ext in composite_extensions:
                    return self.archive_composite_dataset( trans, data, **kwd )
                else:                    
                    trans.response.headers['Content-Length'] = int( os.stat( data.file_name ).st_size )
                    if to_ext[0] != ".":
                        to_ext = "." + to_ext
                    valid_chars = '.,^_-()[]0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                    fname = data.name
                    fname = ''.join(c in valid_chars and c or '_' for c in fname)[0:150]
                    trans.response.headers["Content-Disposition"] = "attachment; filename=Galaxy%s-[%s]%s" % (data.hid, fname, to_ext)
                    return open( data.file_name )
            if os.path.exists( data.file_name ):
                max_peek_size = 1000000 # 1 MB
                if preview and (not isinstance(data.datatype, datatypes.binary.Binary)) and os.stat( data.file_name ).st_size > max_peek_size:
                    trans.response.set_content_type( "text/html" )
                    return trans.stream_template_mako( "/dataset/large_file.mako",
                                                    truncated_data = open( data.file_name ).read(max_peek_size),
                                                    data = data )
                else:
                    return open( data.file_name )
            else:
                raise paste.httpexceptions.HTTPNotFound( "File Not Found (%s)." % data.file_name )
        else:
            return trans.show_error_message( "You are not allowed to access this dataset" )
            
    @web.expose
    @web.require_login( "see all available datasets" )
    def list( self, trans, **kwargs ):
        """List all available datasets"""
        status = message = None

        if 'operation' in kwargs:
            operation = kwargs['operation'].lower()
            hda_ids = util.listify( kwargs.get( 'id', [] ) )
            
            # Display no message by default
            status, message = None, None

            # Load the hdas and ensure they all belong to the current user
            hdas = []
            for encoded_hda_id in hda_ids:
                hda_id = trans.security.decode_id( encoded_hda_id )
                hda = trans.sa_session.query( model.HistoryDatasetAssociation ).filter_by( id=hda_id ).first()
                if hda:
                    # Ensure history is owned by current user
                    if hda.history.user_id != None and trans.user:
                        assert trans.user.id == hda.history.user_id, "HistoryDatasetAssocation does not belong to current user"
                    hdas.append( hda )
                else:
                    log.warn( "Invalid history_dataset_association id '%r' passed to list", hda_id )

            if hdas:
                if operation == "switch" or operation == "switch_history":
                    # Switch to a history that the HDA resides in.
                    
                    # Convert hda to histories.
                    histories = []
                    for hda in hdas:
                        histories.append( hda.history )
                        
                    # Use history controller to switch the history. TODO: is this reasonable?
                    status, message = trans.webapp.controllers['history']._list_switch( trans, histories )
                    
                    # Current history changed, refresh history frame; if switching to a dataset, set hda seek.
                    trans.template_context['refresh_frames'] = ['history']
                    if operation == "switch":
                        hda_ids = [ trans.security.encode_id( hda.id ) for hda in hdas ]
                        trans.template_context[ 'seek_hda_ids' ] = hda_ids
                elif operation == "copy to current history":
                    # Copy a dataset to the current history.
                    target_histories = [ trans.get_history() ]
                    status, message = self._copy_datasets( trans, hda_ids, target_histories )
                    
                    # Current history changed, refresh history frame.
                    trans.template_context['refresh_frames'] = ['history']

        # Render the list view
        return self.stored_list_grid( trans, status=status, message=message, **kwargs )
        
    @web.expose
    def imp( self, trans, dataset_id=None, **kwd ):
        """ Import another user's dataset via a shared URL; dataset is added to user's current history. """
        msg = ""
        
        # Set referer message.
        referer = trans.request.referer
        if referer is not "":
            referer_message = "<a href='%s'>return to the previous page</a>" % referer
        else:
            referer_message = "<a href='%s'>go to Galaxy's start page</a>" % url_for( '/' )
        
        # Error checking.
        if not dataset_id:
            return trans.show_error_message( "You must specify a dataset to import. You can %s." % referer_message, use_panels=True )
            
        # Do import.
        cur_history = trans.get_history( create=True )
        status, message = self._copy_datasets( trans, [ dataset_id ], [ cur_history ], imported=True )
        message = "Dataset imported. <br>You can <a href='%s'>start using the dataset</a> or %s." % ( url_for('/'),  referer_message )
        return trans.show_message( message, type=status, use_panels=True )
        
    @web.expose
    @web.json
    @web.require_login( "use Galaxy datasets" )
    def get_name_and_link_async( self, trans, id=None ):
        """ Returns dataset's name and link. """
        dataset = self.get_dataset( trans, id, False, True )
        return_dict = { "name" : dataset.name, "link" : url_for( action="display_by_username_and_slug", username=dataset.history.user.username, slug=trans.security.encode_id( dataset.id ) ) }
        return return_dict
                
    @web.expose
    def get_embed_html_async( self, trans, id ):
        """ Returns HTML for embedding a dataset in a page. """
        dataset = self.get_dataset( trans, id, False, True )
        if dataset:
            return "Embedded Dataset '%s'" % dataset.name

    @web.expose
    @web.require_login( "use Galaxy datasets" )
    def set_accessible_async( self, trans, id=None, accessible=False ):
        """ Does nothing because datasets do not have an importable/accessible attribute. This method could potentially set another attribute. """
        return
        
    @web.expose
    @web.require_login( "rate items" )
    @web.json
    def rate_async( self, trans, id, rating ):
        """ Rate a dataset asynchronously and return updated community data. """

        dataset = self.get_dataset( trans, id, check_ownership=False, check_accessible=True )
        if not dataset:
            return trans.show_error_message( "The specified dataset does not exist." )

        # Rate dataset.
        dataset_rating = self.rate_item( rate_item, trans.get_user(), dataset, rating )

        return self.get_ave_item_rating_data( trans.sa_session, dataset )
        
    @web.expose
    def display_by_username_and_slug( self, trans, username, slug, preview=True ):
        """ Display dataset by username and slug; because datasets do not yet have slugs, the slug is the dataset's id. """
        dataset = self.get_dataset( trans, slug, False, True )
        if dataset:
            truncated, dataset_data = self.get_data( dataset, preview )
            dataset.annotation = self.get_item_annotation_str( trans.sa_session, dataset.history.user, dataset )
            
            # If data is binary or an image, stream without template; otherwise, use display template.
            # TODO: figure out a way to display images in display template.
            if isinstance(dataset.datatype, datatypes.binary.Binary) or isinstance(dataset.datatype, datatypes.images.Image):
                mime = trans.app.datatypes_registry.get_mimetype_by_extension( dataset.extension.lower() )
                trans.response.set_content_type( mime )
                return open( dataset.file_name )
            else:
                # Get rating data.
                user_item_rating = 0
                if trans.get_user():
                    user_item_rating = self.get_user_item_rating( trans.sa_session, trans.get_user(), dataset )
                    if user_item_rating:
                        user_item_rating = user_item_rating.rating
                    else:
                        user_item_rating = 0
                ave_item_rating, num_ratings = self.get_ave_item_rating_data( trans.sa_session, dataset )
                
                return trans.fill_template_mako( "/dataset/display.mako", item=dataset, item_data=dataset_data, truncated=truncated,
                                                user_item_rating = user_item_rating, ave_item_rating=ave_item_rating, num_ratings=num_ratings )
        else:
            raise web.httpexceptions.HTTPNotFound()
            
    @web.expose
    def get_item_content_async( self, trans, id ):
        """ Returns item content in HTML format. """

        dataset = self.get_dataset( trans, id, False, True )
        if dataset is None:
            raise web.httpexceptions.HTTPNotFound()
        truncated, dataset_data = self.get_data( dataset, preview=True )
        # Get annotation.
        dataset.annotation = self.get_item_annotation_str( trans.sa_session, trans.user, dataset )
        return trans.stream_template_mako( "/dataset/item_content.mako", item=dataset, item_data=dataset_data, truncated=truncated )
        
    @web.expose
    def annotate_async( self, trans, id, new_annotation=None, **kwargs ):
        dataset = self.get_dataset( trans, id, False, True )
        if not dataset:
            web.httpexceptions.HTTPNotFound()
        if dataset and new_annotation:
            # Sanitize annotation before adding it.
            new_annotation = sanitize_html( new_annotation, 'utf-8', 'text/html' )
            self.add_item_annotation( trans.sa_session, trans.get_user(), dataset, new_annotation )
            trans.sa_session.flush()
            return new_annotation
    
    @web.expose
    def get_annotation_async( self, trans, id ):
        dataset = self.get_dataset( trans, id, False, True )
        if not dataset:
            web.httpexceptions.HTTPNotFound()
        return self.get_item_annotation_str( trans.sa_session, trans.user, dataset )

    @web.expose
    def display_at( self, trans, dataset_id, filename=None, **kwd ):
        """Sets up a dataset permissions so it is viewable at an external site"""
        site = filename
        data = trans.sa_session.query( trans.app.model.HistoryDatasetAssociation ).get( dataset_id )
        if not data:
            raise paste.httpexceptions.HTTPRequestRangeNotSatisfiable( "Invalid reference dataset id: %s." % str( dataset_id ) )
        if 'display_url' not in kwd or 'redirect_url' not in kwd:
            return trans.show_error_message( 'Invalid parameters specified for "display at" link, please contact a Galaxy administrator' )
        try:
              redirect_url = kwd['redirect_url'] % urllib.quote_plus( kwd['display_url'] )
        except:
              redirect_url = kwd['redirect_url'] # not all will need custom text
        current_user_roles = trans.get_current_user_roles()
        if trans.app.security_agent.dataset_is_public( data.dataset ):
            return trans.response.send_redirect( redirect_url ) # anon access already permitted by rbac
        if trans.app.security_agent.can_access_dataset( current_user_roles, data.dataset ):
            trans.app.host_security_agent.set_dataset_permissions( data, trans.user, site )
            return trans.response.send_redirect( redirect_url )
        else:
            return trans.show_error_message( "You are not allowed to view this dataset at external sites.  Please contact your Galaxy administrator to acquire management permissions for this dataset." )

    @web.expose
    def display_application( self, trans, dataset_id=None, user_id=None, app_name = None, link_name = None, app_action = None, action_param = None, **kwds ):
        """Access to external display applications"""
        if kwds:
            log.debug( "Unexpected Keywords passed to display_application: %s" % kwds ) #route memory?
        #decode ids
        data, user = decode_dataset_user( trans, dataset_id, user_id )
        if not data:
            raise paste.httpexceptions.HTTPRequestRangeNotSatisfiable( "Invalid reference dataset id: %s." % str( dataset_id ) )
        if user is None:
            user = trans.user
        if user:
            user_roles = user.all_roles()
        else:
            user_roles = []
        if None in [ app_name, link_name ]:
            return trans.show_error_message( "A display application name and link name must be provided." )
        
        if trans.app.security_agent.can_access_dataset( user_roles, data.dataset ):
            msg = []
            refresh = False
            display_app = trans.app.datatypes_registry.display_applications.get( app_name )
            assert display_app, "Unknown display application has been requested: %s" % app_name
            dataset_hash, user_hash = encode_dataset_user( trans, data, user )
            display_link = display_app.get_link( link_name, data, dataset_hash, user_hash, trans )
            assert display_link, "Unknown display link has been requested: %s" % link_name
            if data.state == data.states.ERROR:
                msg.append( ( 'This dataset is in an error state, you cannot view it at an external display application.', 'error' ) )
            elif data.deleted:
                msg.append( ( 'This dataset has been deleted, you cannot view it at an external display application.', 'error' ) )
            elif data.state != data.states.OK:
                msg.append( ( 'You must wait for this dataset to be created before you can view it at an external display application.', 'info' ) )
                refresh = True
            else:
                #We have permissions, dataset is not deleted and is in OK state, allow access
                if display_link.display_ready():
                    if app_action in [ 'data', 'param' ]:
                        assert action_param, "An action param must be provided for a data or param action"
                        #data is used for things with filenames that could be passed off to a proxy
                        #in case some display app wants all files to be in the same 'directory', 
                        #data can be forced to param, but not the other way (no filename for other direction)
                        #get param name from url param name
                        action_param = display_link.get_param_name_by_url( action_param )
                        value = display_link.get_param_value( action_param )
                        assert value, "An invalid parameter name was provided: %s" % action_param
                        assert value.parameter.viewable, "This parameter is not viewable."
                        if value.parameter.type == 'data':
                            content_length = os.path.getsize( value.file_name )
                            rval = open( value.file_name )
                        else:
                            rval = str( value )
                            content_length = len( rval )
                        trans.response.set_content_type( value.mime_type() )
                        trans.response.headers[ 'Content-Length' ] = content_length
                        return rval
                    elif app_action == None:
                        #redirect user to url generated by display link
                        return trans.response.send_redirect( display_link.display_url() )
                    else:
                        msg.append( ( 'Invalid action provided: %s' % app_action, 'error' ) )
                else:
                    if app_action == None:
                        if trans.history != data.history:
                            msg.append( ( 'You must import this dataset into your current history before you can view it at the desired display application.', 'error' ) )
                        else:
                            refresh = True
                            msg.append( ( 'This display application is being prepared.', 'info' ) )
                            if not display_link.preparing_display():
                                display_link.prepare_display()
                    else:
                        raise Exception( 'Attempted a view action (%s) on a non-ready display application' % app_action )
            return trans.fill_template_mako( "dataset/display_application/display.mako", msg = msg, display_app = display_app, display_link = display_link, refresh = refresh )
        return trans.show_error_message( 'You do not have permission to view this dataset at an external display application.' )

    def _undelete( self, trans, id ):
        try:
            id = int( id )
        except ValueError, e:
            return False
        history = trans.get_history()
        data = trans.sa_session.query( self.app.model.HistoryDatasetAssociation ).get( id )
        if data and data.undeletable:
            # Walk up parent datasets to find the containing history
            topmost_parent = data
            while topmost_parent.parent:
                topmost_parent = topmost_parent.parent
            assert topmost_parent in history.datasets, "Data does not belong to current history"
            # Mark undeleted
            data.mark_undeleted()
            trans.sa_session.flush()
            trans.log_event( "Dataset id %s has been undeleted" % str(id) )
            return True
        return False

    def _unhide( self, trans, id ):
        try:
            id = int( id )
        except ValueError, e:
            return False
        history = trans.get_history()
        data = trans.sa_session.query( self.app.model.HistoryDatasetAssociation ).get( id )
        if data:
            # Walk up parent datasets to find the containing history
            topmost_parent = data
            while topmost_parent.parent:
                topmost_parent = topmost_parent.parent
            assert topmost_parent in history.datasets, "Data does not belong to current history"
            # Mark undeleted
            data.mark_unhidden()
            trans.sa_session.flush()
            trans.log_event( "Dataset id %s has been unhidden" % str(id) )
            return True
        return False
    
    @web.expose
    def undelete( self, trans, id ):
        if self._undelete( trans, id ):
            return trans.response.send_redirect( web.url_for( controller='root', action='history', show_deleted = True ) )
        raise "Error undeleting"

    @web.expose
    def unhide( self, trans, id ):
        if self._unhide( trans, id ):
            return trans.response.send_redirect( web.url_for( controller='root', action='history', show_hidden = True ) )
        raise "Error unhiding"


    @web.expose
    def undelete_async( self, trans, id ):
        if self._undelete( trans, id ):
            return "OK"
        raise "Error undeleting"
    
    @web.expose
    def copy_datasets( self, trans, source_dataset_ids="", target_history_ids="", new_history_name="", do_copy=False, **kwd ):
        params = util.Params( kwd )
        user = trans.get_user()
        history = trans.get_history()
        create_new_history = False
        refresh_frames = []
        if source_dataset_ids:
            if not isinstance( source_dataset_ids, list ):
                source_dataset_ids = source_dataset_ids.split( "," )
            source_dataset_ids = map( int, source_dataset_ids )
        else:
            source_dataset_ids = []
        if target_history_ids:
            if not isinstance( target_history_ids, list ):
                target_history_ids = target_history_ids.split( "," )
            if "create_new_history" in target_history_ids:
                create_new_history = True
                target_history_ids.remove( "create_new_history" )
            target_history_ids = map( int, target_history_ids )
        else:
            target_history_ids = []
        done_msg = error_msg = ""
        if do_copy:
            invalid_datasets = 0
            if not source_dataset_ids or not ( target_history_ids or create_new_history ):
                error_msg = "You must provide both source datasets and target histories."
                if create_new_history:
                    target_history_ids.append( "create_new_history" )
            else:
                if create_new_history:
                    new_history = trans.app.model.History()
                    if new_history_name:
                        new_history.name = new_history_name
                    new_history.user = user
                    trans.sa_session.add( new_history )
                    trans.sa_session.flush()
                    target_history_ids.append( new_history.id )
                if user:
                    target_histories = [ hist for hist in map( trans.sa_session.query( trans.app.model.History ).get, target_history_ids ) if ( hist is not None and hist.user == user )]
                else:
                    target_histories = [ history ]
                if len( target_histories ) != len( target_history_ids ):
                    error_msg = error_msg + "You do not have permission to add datasets to %i requested histories.  " % ( len( target_history_ids ) - len( target_histories ) )
                for data in map( trans.sa_session.query( trans.app.model.HistoryDatasetAssociation ).get, source_dataset_ids ):
                    if data is None:
                        error_msg = error_msg + "You tried to copy a dataset that does not exist.  "
                        invalid_datasets += 1
                    elif data.history != history:
                        error_msg = error_msg + "You tried to copy a dataset which is not in your current history.  "
                        invalid_datasets += 1
                    else:
                        for hist in target_histories:
                            hist.add_dataset( data.copy( copy_children = True ) )
                if history in target_histories:
                    refresh_frames = ['history']
                trans.sa_session.flush()
                done_msg = "%i datasets copied to %i histories." % ( len( source_dataset_ids ) - invalid_datasets, len( target_histories ) )
                trans.sa_session.refresh( history )
        elif create_new_history:
            target_history_ids.append( "create_new_history" )
        source_datasets = history.active_datasets
        target_histories = [history]
        if user:
           target_histories = user.active_histories 
        return trans.fill_template( "/dataset/copy_view.mako",
                                    source_dataset_ids = source_dataset_ids,
                                    target_history_ids = target_history_ids,
                                    source_datasets = source_datasets,
                                    target_histories = target_histories,
                                    new_history_name = new_history_name,
                                    done_msg = done_msg,
                                    error_msg = error_msg,
                                    refresh_frames = refresh_frames )

    def _copy_datasets( self, trans, dataset_ids, target_histories, imported=False ):
        """ Helper method for copying datasets. """
        user = trans.get_user()
        done_msg = error_msg = ""
        
        invalid_datasets = 0
        if not dataset_ids or not target_histories:
            error_msg = "You must provide both source datasets and target histories."
        else:
            # User must own target histories to copy datasets to them.
            for history in target_histories:
                if user != history.user:
                    error_msg = error_msg + "You do not have permission to add datasets to %i requested histories.  " % ( len( target_histories ) )
            for dataset_id in dataset_ids:
                data = self.get_dataset( trans, dataset_id, False, True )
                if data is None:
                    error_msg = error_msg + "You tried to copy a dataset that does not exist or that you do not have access to.  "
                    invalid_datasets += 1
                else:
                    for hist in target_histories:
                        dataset_copy = data.copy( copy_children = True )
                        if imported:
                            dataset_copy.name = "imported: " + dataset_copy.name
                        hist.add_dataset( dataset_copy )
            trans.sa_session.flush()
            num_datasets_copied = len( dataset_ids ) - invalid_datasets
            done_msg = "%i dataset%s copied to %i histor%s." % \
                ( num_datasets_copied, iff( num_datasets_copied == 1, "", "s"), len( target_histories ), iff( len ( target_histories ) == 1, "y", "ies") )
            trans.sa_session.refresh( history )
        
        if error_msg != "":
            status = ERROR
            message = error_msg
        else:
            status = SUCCESS
            message = done_msg
        return status, message
