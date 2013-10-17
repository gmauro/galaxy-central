"""
API operations on the contents of a folder.
"""
import logging, os, string, shutil, urllib, re, socket
from cgi import escape, FieldStorage
from galaxy import util, datatypes, jobs, web, util
from galaxy.web.base.controller import *
from galaxy.util.sanitize_html import sanitize_html
from galaxy.model.orm import *

log = logging.getLogger( __name__ )

class FolderContentsController( BaseAPIController, UsesLibraryMixin, UsesLibraryMixinItems ):
    """
    Class controls retrieval, creation and updating of folder contents.
    """

    @web.expose_api
    def index( self, trans, folder_id, **kwd ):
        """
        GET /api/folders/{encoded_folder_id}/contents
        
        Displays a collection (list) of a folder's contents (files and folders).
        
        The /api/library_contents/{encoded_library_id}/contents
        lists everything in a library recursively, which is not what
        we want here. We could add a parameter to use the recursive
        style, but this is meant to act similar to an "ls" directory listing.
        """
        folder_contents = []
        current_user_roles = trans.get_current_user_roles()


        def load_folder_contents( folder ):
            """
            Load contents of the folder (folders and datasets).
            """
            admin = trans.user_is_admin()
            rval = []
            for subfolder in folder.active_folders:
                if not admin:
                    can_access, folder_ids = trans.app.security_agent.check_folder_contents( trans.user, current_user_roles, subfolder )
                if (admin or can_access) and not subfolder.deleted:
                    subfolder.api_type = 'folder'
                    rval.append( subfolder )
            for ld in folder.datasets:
                if not admin:
                    can_access = trans.app.security_agent.can_access_dataset( current_user_roles, ld.library_dataset_dataset_association.dataset )
                if (admin or can_access) and not ld.deleted:
                    ld.api_type = 'file'
                    rval.append( ld )
            return rval

        try:
            decoded_folder_id = trans.security.decode_id( folder_id[-16:] )
        except TypeError:
            trans.response.status = 400
            return "Malformed folder id ( %s ) specified, unable to decode." % str( folder_id )

        try:
            folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( decoded_folder_id )
#             log.debug("XXXXXXXXXXXXXXXXXXXXXXXXXXX folder.parent_library" + str(folder.parent_library.id))
#             log.debug("XXXXXXXXXXXXXXXXXXXXXXXXXXX folder.parent_id" + str(folder.parent_id))
            parent_library = folder.parent_library
        except:
            folder = None
            log.error( "FolderContentsController.index: Unable to retrieve folder %s"
                      % folder_id )

        # TODO: Find the API's path to this folder if necessary.
        # This was needed in recursive descent, but it's not needed
        # for "ls"-style content checking:
        if not folder or not ( trans.user_is_admin() or trans.app.security_agent.can_access_library_item( current_user_roles, folder, trans.user ) ):
            trans.response.status = 400
            return "Invalid folder id ( %s ) specified." % str( folder_id )
        # TODO MARTEN Can it be that predecessors of current folder have different access rights? aka user shouldn't see them?
        
        # Search the path upwards and load the whole route of names and ids for breadcrumb purposes.
        path_to_root = []
        
        def build_path ( folder ):
            path_to_root = []
            # We are almost in root
            log.debug( "XXXXXXXXXXXXXXXXXXXXXXX folder.parent_id: " + str( folder.parent_id ) )
            log.debug( "XXXXXXXXXXXXXXXXXXXXXXX folder.parent_library.id: " + str( folder.parent_library.id ) )
            if folder.parent_id is None:
                log.debug( "XXXXXXXXXXXXXXXXXXXXXXX ALMOST ROOT FOLDER! ADDING: " + str( folder.name ) )
                path_to_root.append( ( folder.id, folder.name ) )
#                 upper_folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( folder.parent_library.id )
#                 path_to_root.append( ( upper_folder.id, upper_folder.name ) )
            else:
            # We add the current folder and traverse up one folder.
                log.debug( "XXXXXXXXXXXXXXXXXXXXXXX ADDING THIS FOLDER AND TRAVERSING UP:  " + str( folder.name ) )
                path_to_root.append( ( folder.id, folder.name ) )
                upper_folder = trans.sa_session.query( trans.app.model.LibraryFolder ).get( folder.parent_id )
                path_to_root.extend( build_path( upper_folder ) )
#             path_to_root = path_to_root.reverse()
#             return path_to_root[::-1]
            return path_to_root
            
        # Return the reversed path so it starts with the library node.
        full_path = build_path( folder )[::-1]

        # Go through every item in the folder and include its meta-data.
        for content_item in load_folder_contents( folder ):
            return_item = {}
            encoded_id = trans.security.encode_id( content_item.id )
            
            # For folder return also hierarchy values
            if content_item.api_type == 'folder':
                encoded_parent_library_id = trans.security.encode_id( content_item.parent_library.id )
                encoded_id = 'F' + encoded_id
                if content_item.parent_id is not None: # Return folder's parent id for browsing back.
                    encoded_parent_id = 'F' + trans.security.encode_id( content_item.parent_id )
                    return_item.update ( dict ( parent_id = encoded_parent_id ) )
            
            # For every item return also the default meta-data
            return_item.update( dict( id = encoded_id,
                               type = content_item.api_type,
                               name = content_item.name,
                               library_id = encoded_parent_library_id,
                               full_path = full_path,
                               url = url_for( 'folder_contents', folder_id=encoded_id ) ) )
            folder_contents.append( return_item )
        if len( folder_contents ) == 0:
            folder_contents.append( dict( full_path = full_path ) )
        return folder_contents

    @web.expose_api
    def show( self, trans, id, library_id, **kwd ):
        """
        GET /api/folders/{encoded_folder_id}/
        """
        pass

    @web.expose_api
    def create( self, trans, library_id, payload, **kwd ):
        """
        POST /api/folders/{encoded_folder_id}/contents
        Creates a new folder. This should be superseded by the
        LibraryController.
        """
        pass

    @web.expose_api
    def update( self, trans, id,  library_id, payload, **kwd ):
        """
        PUT /api/folders/{encoded_folder_id}/contents
        """
        pass

    # TODO: Move to library_common.
    def __decode_library_content_id( self, trans, content_id ):
        if ( len( content_id ) % 16 == 0 ):
            return 'LibraryDataset', content_id
        elif ( content_id.startswith( 'F' ) ):
            return 'LibraryFolder', content_id[1:]
        else:
            raise HTTPBadRequest( 'Malformed library content id ( %s ) specified, unable to decode.' % str( content_id ) )
