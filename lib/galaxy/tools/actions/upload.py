import os, shutil, urllib, StringIO, re, gzip, tempfile, shutil, zipfile
from galaxy import datatypes, jobs
from galaxy.datatypes import sniff
from galaxy import model, util

import sys, traceback

import logging
log = logging.getLogger( __name__ )

class UploadToolAction( object ):
    # Action for uploading files
    def __init__( self ):
        self.empty = False
        self.line_count = None
    def remove_tempfile( self, filename ):
        try:
            os.unlink( filename )
        except:
            log.exception( 'failure removing temporary file: %s' % filename )
    def execute( self, tool, trans, incoming={}, set_output_hid = True ):
        data_file = incoming['file_data']
        file_type = incoming['file_type']
        dbkey = incoming['other_dbkey'] or incoming['dbkey']
        url_paste = incoming['url_paste']
        is_multi_byte = False
        space_to_tab = False 
        if 'space_to_tab' in incoming:
            if incoming['space_to_tab'] not in ["None", None]:
                space_to_tab = True
        # Get any precreated datasets (when using asynchronous uploads)
        async_datasets = []
        self.precreated_datasets = []
        if incoming['async_datasets'] not in ["None", "", None]:
            async_datasets = incoming['async_datasets'].split(',')
        for id in async_datasets:
            try:
                data = trans.app.model.HistoryDatasetAssociation.get( int( id ) )
            except:
                log.exception( 'Unable to load precreated dataset (%s) sent in upload form' % id )
                continue
            if trans.user is None and trans.galaxy_session.current_history != data.history:
               log.error( 'Got a precreated dataset (%s) but it does not belong to anonymous user\'s current session (%s)' % ( data.id, trans.galaxy_session.id ) )
            elif data.history.user != trans.user:
               log.error( 'Got a precreated dataset (%s) but it does not belong to current user (%s)' % ( data.id, trans.user.id ) )
            else:
                self.precreated_datasets.append( data )
        temp_name = ""
        data_list = []
        # Create the job object
        job = trans.app.model.Job()
        job.session_id = trans.get_galaxy_session().id
        job.history_id = trans.history.id
        job.tool_id = tool.id
        try:
            # For backward compatibility, some tools may not have versions yet.
            job.tool_version = tool.version
        except:
            job.tool_version = "1.0.0"
        job.state = trans.app.model.Job.states.UPLOAD
        job.flush()
        log.info( 'tool %s created job id %d' % ( tool.id, job.id ) )
        trans.log_event( 'created job id %d' % job.id, tool_id=tool.id )
        if 'local_filename' in dir( data_file ):
            # Use the existing file
            file_name = data_file.filename
            file_name = file_name.split( '\\' )[-1]
            file_name = file_name.split( '/' )[-1]
            precreated_dataset = self.get_precreated_dataset( file_name )
            try:
                data_list.append( self.add_file( trans, data_file.local_filename, file_name, file_type, is_multi_byte,  dbkey, space_to_tab=space_to_tab, precreated_dataset=precreated_dataset ) )
            except Exception, e:
                log.exception( 'exception in add_file using datafile.local_filename %s: %s' % ( data_file.local_filename, str( e ) ) )
                self.remove_tempfile( data_file.local_filename )
                return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
        elif 'filename' in dir( data_file ):
            file_name = data_file.filename
            file_name = file_name.split( '\\' )[-1]
            file_name = file_name.split( '/' )[-1]
            precreated_dataset = self.get_precreated_dataset( file_name )
            try:
                temp_name, is_multi_byte = sniff.stream_to_file( data_file.file, prefix='upload' )
            except Exception, e:
                log.exception( 'exception in sniff.stream_to_file using file %s: %s' % ( data_file.filename, str( e ) ) )
                self.remove_tempfile( temp_name )
                return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
            try:
                data_list.append( self.add_file( trans, temp_name, file_name, file_type, is_multi_byte,  dbkey, space_to_tab=space_to_tab, precreated_dataset=precreated_dataset ) )
            except Exception, e:
                log.exception( 'exception in add_file using file temp_name %s: %s' % ( str( temp_name ), str( e ) ) )
                self.remove_tempfile( temp_name )
                return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
        if url_paste not in [ None, "" ]:
            if url_paste.lstrip().lower().startswith( 'http://' ) or url_paste.lstrip().lower().startswith( 'ftp://' ):
                # If we were sent a DATA_URL from an external application in a post, NAME and INFO
                # values should be in the request
                if 'NAME' in incoming and incoming[ 'NAME' ] not in [ "None", None ]:
                    NAME = incoming[ 'NAME' ]
                else:
                    NAME = ''
                if 'INFO' in incoming and incoming[ 'INFO' ] not in [ "None", None ]:
                    INFO = incoming[ 'INFO' ]
                else:
                    INFO = "uploaded url"
                url_paste = url_paste.replace( '\r', '' ).split( '\n' )
                name_set_from_line = False #if we are setting the name from the line, it needs to be the line that creates that dataset
                for line in url_paste:
                    line = line.strip()
                    if line:
                        if not line.lower().startswith( 'http://' ) and not line.lower().startswith( 'ftp://' ):
                            continue # non-url line, ignore
                        if not NAME or name_set_from_line:
                            NAME = line
                            name_set_from_line = True
                        precreated_dataset = self.get_precreated_dataset( NAME )
                        try:
                            temp_name, is_multi_byte = sniff.stream_to_file( urllib.urlopen( line ), prefix='url_paste' )
                        except Exception, e:
                            log.exception( 'exception in sniff.stream_to_file using url_paste %s: %s' % ( url_paste, str( e ) ) )
                            self.remove_tempfile( temp_name )
                            return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
                        try:
                            data_list.append( self.add_file( trans, temp_name, NAME, file_type, is_multi_byte,  dbkey, info="uploaded url", space_to_tab=space_to_tab, precreated_dataset=precreated_dataset ) )
                        except Exception, e:
                            log.exception( 'exception in add_file using url_paste temp_name %s: %s' % ( str( temp_name ), str( e ) ) )
                            self.remove_tempfile( temp_name )
                            return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
            else:
                precreated_dataset = self.get_precreated_dataset( 'Pasted Entry' )
                is_valid = False
                for line in url_paste:
                    line = line.rstrip( '\r\n' )
                    if line:
                        is_valid = True
                        break
                if is_valid:
                    try:
                        temp_name, is_multi_byte = sniff.stream_to_file( StringIO.StringIO( url_paste ), prefix='strio_url_paste' )
                    except Exception, e:
                        log.exception( 'exception in sniff.stream_to_file using StringIO.StringIO( url_paste ) %s: %s' % ( url_paste, str( e ) ) )
                        self.remove_tempfile( temp_name )
                        return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
                    try:
                        data_list.append( self.add_file( trans, temp_name, 'Pasted Entry', file_type, is_multi_byte,  dbkey, info="pasted entry", space_to_tab=space_to_tab, precreated_dataset=precreated_dataset ) )
                    except Exception, e:
                        log.exception( 'exception in add_file using StringIO.StringIO( url_paste ) temp_name %s: %s' % ( str( temp_name ), str( e ) ) )
                        self.remove_tempfile( temp_name )
                        return self.upload_empty( trans, job, "Error:", str( e ), precreated_dataset=precreated_dataset )
                else:
                    return self.upload_empty( trans, job, "No data error:", "you pasted no data.", precreated_dataset=precreated_dataset )
        if self.empty:
            return self.upload_empty( trans, job, "Empty file error:", "you attempted to upload an empty file." )
        elif len( data_list ) < 1:
            return self.upload_empty( trans, job, "No data error:", "either you pasted no data, the url you specified is invalid, or you have not specified a file." )
        #if we could make a 'real' job here, then metadata could be set before job.finish() is called
        hda = data_list[0] #only our first hda is being added as input for the job, why?
        job.state = trans.app.model.Job.states.OK
        file_size_str = datatypes.data.nice_size( hda.dataset.file_size )
        job.info = "%s, size: %s" % ( hda.info, file_size_str )
        job.add_output_dataset( hda.name, hda )
        job.flush()
        log.info( 'job id %d ended ok, file size: %s' % ( job.id, file_size_str ) )
        trans.log_event( 'job id %d ended ok, file size: %s' % ( job.id, file_size_str ), tool_id=tool.id )
        return dict( output=hda )

    def upload_empty(self, trans, job, err_code, err_msg, precreated_dataset = None):
        if precreated_dataset is not None:
            data = precreated_dataset
        else:
            data = trans.app.model.HistoryDatasetAssociation( create_dataset=True )
        trans.app.security_agent.set_all_dataset_permissions( data.dataset, trans.app.security_agent.history_get_default_permissions( trans.history ) )
        data.name = err_code
        data.extension = "txt"
        data.dbkey = "?"
        data.info = err_msg
        data.file_size = 0
        data.state = data.states.EMPTY
        data.flush()
        if precreated_dataset is None:
            trans.history.add_dataset( data )
        trans.app.model.flush()
        # Indicate job failure by setting state and info
        job.state = trans.app.model.Job.states.ERROR
        job.info = err_msg
        job.add_output_dataset( data.name, data )
        job.flush()
        log.info( 'job id %d ended with errors, err_msg: %s' % ( job.id, err_msg ) )
        trans.log_event( 'job id %d ended with errors, err_msg: %s' % ( job.id, err_msg ), tool_id=job.tool_id )
        return dict( output=data )

    def add_file( self, trans, temp_name, file_name, file_type, is_multi_byte,  dbkey, info=None, space_to_tab=False, precreated_dataset=None ):
        data_type = None
        # See if we have an empty file
        if not os.path.getsize( temp_name ) > 0:
            raise BadFileException( "you attempted to upload an empty file." )
        if is_multi_byte:
            ext = sniff.guess_ext( temp_name, is_multi_byte=True )
        else:
            if not data_type:
                # See if we have a gzipped file, which, if it passes our restrictions,
                # we'll decompress on the fly.
                is_gzipped, is_valid = self.check_gzip( temp_name )
                if is_gzipped and not is_valid:
                    raise BadFileException( "you attempted to upload an inappropriate file." )
                elif is_gzipped and is_valid:
                    # We need to uncompress the temp_name file
                    CHUNK_SIZE = 2**20 # 1Mb   
                    fd, uncompressed = tempfile.mkstemp()   
                    gzipped_file = gzip.GzipFile( temp_name )
                    while 1:
                        try:
                            chunk = gzipped_file.read( CHUNK_SIZE )
                        except IOError:
                            os.close( fd )
                            os.remove( uncompressed )
                            raise BadFileException( 'problem decompressing gzipped data.' )
                        if not chunk:
                            break
                        os.write( fd, chunk )
                    os.close( fd )
                    gzipped_file.close()
                    # Replace the gzipped file with the decompressed file
                    shutil.move( uncompressed, temp_name )
                    file_name = file_name.rstrip( '.gz' )
                    data_type = 'gzip'
                ext = ''
                if not data_type:
                    # See if we have a zip archive
                    is_zipped, is_valid, test_ext = self.check_zip( temp_name )
                    if is_zipped and not is_valid:
                        raise BadFileException( "you attempted to upload an inappropriate file." )
                    elif is_zipped and is_valid:
                        # Currently, we force specific tools to handle this case.  We also require the user
                        # to manually set the incoming file_type
                        if ( test_ext == 'ab1' or test_ext == 'scf' ) and file_type != 'binseq.zip':
                            raise BadFileException( "Invalid 'File Format' for archive consisting of binary files - use 'Binseq.zip'." )
                        elif test_ext == 'txt' and file_type != 'txtseq.zip':
                            raise BadFileException( "Invalid 'File Format' for archive consisting of text files - use 'Txtseq.zip'." )
                        if not ( file_type == 'binseq.zip' or file_type == 'txtseq.zip' ):
                            raise BadFileException( "you must manually set the 'File Format' to either 'Binseq.zip' or 'Txtseq.zip' when uploading zip files." )
                        data_type = 'zip'
                        ext = file_type
                if not data_type:
                    if self.check_binary( temp_name ):
                        parts = file_name.split( "." )
                        if len( parts ) > 1:
                            ext = parts[1].strip().lower()
                            if not( ext == 'ab1' or ext == 'scf' ):
                                raise BadFileException( "you attempted to upload an inappropriate file." )
                            if ext == 'ab1' and file_type != 'ab1':
                                raise BadFileException( "you must manually set the 'File Format' to 'Ab1' when uploading ab1 files." )
                            elif ext == 'scf' and file_type != 'scf':
                                raise BadFileException( "you must manually set the 'File Format' to 'Scf' when uploading scf files." )
                        data_type = 'binary'
                if not data_type:
                    # We must have a text file
                    if self.check_html( temp_name ):
                        raise BadFileException( "you attempted to upload an inappropriate file." )
                if data_type != 'binary' and data_type != 'zip':
                    if space_to_tab:
                        self.line_count = sniff.convert_newlines_sep2tabs( temp_name )
                    else:
                        self.line_count = sniff.convert_newlines( temp_name )
                    if file_type == 'auto':
                        ext = sniff.guess_ext( temp_name, sniff_order=trans.app.datatypes_registry.sniff_order )    
                    else:
                        ext = file_type
                    data_type = ext
        if info is None:
            info = 'uploaded %s file' %data_type
        if precreated_dataset is not None:
            data = precreated_dataset
            data.extension = ext
        else:
            data = trans.app.model.HistoryDatasetAssociation( history = trans.history, extension = ext, create_dataset = True )
        trans.app.security_agent.set_all_dataset_permissions( data.dataset, trans.app.security_agent.history_get_default_permissions( trans.history ) )
        data.name = file_name
        data.dbkey = dbkey
        data.info = info
        data.flush()
        shutil.move( temp_name, data.file_name )
        data.state = data.states.OK
        data.set_size()
        data.init_meta()
        if self.line_count is not None:
            try:
                if is_multi_byte:
                    data.set_multi_byte_peek( line_count=self.line_count )
                else:
                    data.set_peek( line_count=self.line_count )
            except:
                if is_multi_byte:
                    data.set_multi_byte_peek()
                else:
                    data.set_peek()
        else:
            if is_multi_byte:
                data.set_multi_byte_peek()
            else:
                data.set_peek()

        # validate incomming data
        # Commented by greg on 3/14/07
        # for error in data.datatype.validate( data ):
        #     data.add_validation_error( 
        #         model.ValidationError( message=str( error ), err_type=error.__class__.__name__, attributes=util.object_to_string( error.__dict__ ) ) )
        if data.missing_meta():
            data.datatype.set_meta( data )
        dbkey_to_store = dbkey
        if type( dbkey_to_store ) == type( [] ):
            dbkey_to_store = dbkey[0]
        if precreated_dataset is not None:
            trans.history.genome_build = dbkey_to_store
        else:
            trans.history.add_dataset( data, genome_build=dbkey_to_store )
        trans.app.model.flush()
        trans.log_event( "Added dataset %d to history %d" %( data.id, trans.history.id ), tool_id="upload" )
        return data

    def check_gzip( self, temp_name ):
        temp = open( temp_name, "U" )
        magic_check = temp.read( 2 )
        temp.close()
        if magic_check != util.gzip_magic:
            return ( False, False )
        CHUNK_SIZE = 2**15 # 32Kb
        gzipped_file = gzip.GzipFile( temp_name )
        chunk = gzipped_file.read( CHUNK_SIZE )
        gzipped_file.close()
        if self.check_html( temp_name, chunk=chunk ) or self.check_binary( temp_name, chunk=chunk ):
            return( True, False )
        return ( True, True )

    def check_zip( self, temp_name ):
        if not zipfile.is_zipfile( temp_name ):
            return ( False, False, None )
        zip_file = zipfile.ZipFile( temp_name, "r" )
        # Make sure the archive consists of valid files.  The current rules are:
        # 1. Archives can only include .ab1, .scf or .txt files
        # 2. All file extensions within an archive must be the same
        name = zip_file.namelist()[0]
        test_ext = name.split( "." )[1].strip().lower()
        if not ( test_ext == 'scf' or test_ext == 'ab1' or test_ext == 'txt' ):
            return ( True, False, test_ext )
        for name in zip_file.namelist():
            ext = name.split( "." )[1].strip().lower()
            if ext != test_ext:
                return ( True, False, test_ext )
        return ( True, True, test_ext )

    def check_html( self, temp_name, chunk=None ):
        if chunk is None:
            temp = open(temp_name, "U")
        else:
            temp = chunk
        regexp1 = re.compile( "<A\s+[^>]*HREF[^>]+>", re.I )
        regexp2 = re.compile( "<IFRAME[^>]*>", re.I )
        regexp3 = re.compile( "<FRAMESET[^>]*>", re.I )
        regexp4 = re.compile( "<META[^>]*>", re.I )
        lineno = 0
        for line in temp:
            lineno += 1
            matches = regexp1.search( line ) or regexp2.search( line ) or regexp3.search( line ) or regexp4.search( line )
            if matches:
                if chunk is None:
                    temp.close()
                return True
            if lineno > 100:
                break
        if chunk is None:
            temp.close()
        return False
    def check_binary( self, temp_name, chunk=None ):
        if chunk is None:
            temp = open( temp_name, "U" )
        else:
            temp = chunk
        lineno = 0
        for line in temp:
            lineno += 1
            line = line.strip()
            if line:
                if util.is_multi_byte( line ):
                    return False
                for char in line:
                    if ord( char ) > 128:
                        if chunk is None:
                            temp.close()
                        return True
            if lineno > 10:
                break
        if chunk is None:
            temp.close()
        return False

    def get_precreated_dataset( self, name ):
        """
        Return a dataset matching a name from the list of precreated (via async
        upload) datasets. If there's more than one upload with the exact same
        name, we need to pop one (the first) so it isn't chosen next time.
        """
        names = [ d.name for d in self.precreated_datasets ]
        if names.count( name ) > 0:
            return self.precreated_datasets.pop( names.index( name ) )
        else:
            return None
        
class BadFileException( Exception ):
    pass

