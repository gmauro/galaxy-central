import re

import pkg_resources
pkg_resources.require( "SQLAlchemy >= 0.4" )
import sqlalchemy

from galaxy import model
from galaxy import exceptions
from galaxy.model import tool_shed_install
from galaxy.util import sanitize_html


import logging
log = logging.getLogger( __name__ )


# =============================================================================
def security_check( trans, item, check_ownership=False, check_accessible=False ):
    """ Security checks for an item: checks if (a) user owns item or (b) item
    is accessible to user. This is a generic method for dealing with objects
    uniformly from the older controller mixin code - however whenever possible
    the managers for a particular model should be used to perform security
    checks.
    """

    # all items are accessible to an admin
    if trans.user_is_admin():
        return item

    # Verify ownership: there is a current user and that user is the same as the item's
    if check_ownership:
        if not trans.user:
            raise exceptions.ItemOwnershipException( "Must be logged in to manage Galaxy items", type='error' )
        if item.user != trans.user:
            raise exceptions.ItemOwnershipException( "%s is not owned by the current user" % item.__class__.__name__, type='error' )

    # Verify accessible:
    #   if it's part of a lib - can they access via security
    #   if it's something else (sharable) have they been added to the item's users_shared_with_dot_users
    if check_accessible:
        if type( item ) in ( trans.app.model.LibraryFolder, trans.app.model.LibraryDatasetDatasetAssociation, trans.app.model.LibraryDataset ):
            if not trans.app.security_agent.can_access_library_item( trans.get_current_user_roles(), item, trans.user ):
                raise exceptions.ItemAccessibilityException( "%s is not accessible to the current user" % item.__class__.__name__, type='error' )
        else:
            if ( item.user != trans.user ) and ( not item.importable ) and ( trans.user not in item.users_shared_with_dot_users ):
                raise exceptions.ItemAccessibilityException( "%s is not accessible to the current user" % item.__class__.__name__, type='error' )
    return item


def get_class( class_name ):
    """ Returns the class object that a string denotes. Without this method, we'd have to do eval(<class_name>). """
    if class_name == 'History':
        item_class = model.History
    elif class_name == 'HistoryDatasetAssociation':
        item_class = model.HistoryDatasetAssociation
    elif class_name == 'Page':
        item_class = model.Page
    elif class_name == 'StoredWorkflow':
        item_class = model.StoredWorkflow
    elif class_name == 'Visualization':
        item_class = model.Visualization
    elif class_name == 'Tool':
        item_class = model.Tool
    elif class_name == 'Job':
        item_class = model.Job
    elif class_name == 'User':
        item_class = model.User
    elif class_name == 'Group':
        item_class = model.Group
    elif class_name == 'Role':
        item_class = model.Role
    elif class_name == 'Quota':
        item_class = model.Quota
    elif class_name == 'Library':
        item_class = model.Library
    elif class_name == 'LibraryFolder':
        item_class = model.LibraryFolder
    elif class_name == 'LibraryDatasetDatasetAssociation':
        item_class = model.LibraryDatasetDatasetAssociation
    elif class_name == 'LibraryDataset':
        item_class = model.LibraryDataset
    elif class_name == 'ToolShedRepository':
        item_class = tool_shed_install.ToolShedRepository
    else:
        item_class = None
    return item_class


def get_object( trans, id, class_name, check_ownership=False, check_accessible=False, deleted=None ):
    """
    Convenience method to get a model object with the specified checks. This is
    a generic method for dealing with objects uniformly from the older
    controller mixin code - however whenever possible the managers for a
    particular model should be used to load objects.
    """
    try:
        decoded_id = trans.security.decode_id( id )
    except:
        raise exceptions.MessageException( "Malformed %s id ( %s ) specified, unable to decode"
                                           % ( class_name, str( id ) ), type='error' )
    try:
        item_class = get_class( class_name )
        assert item_class is not None
        item = trans.sa_session.query( item_class ).get( decoded_id )
        assert item is not None
    except Exception:
        log.exception( "Invalid %s id ( %s ) specified." % ( class_name, id ) )
        raise exceptions.MessageException( "Invalid %s id ( %s ) specified" % ( class_name, id ), type="error" )

    if check_ownership or check_accessible:
        security_check( trans, item, check_ownership, check_accessible )
    if deleted is True and not item.deleted:
        raise exceptions.ItemDeletionException( '%s "%s" is not deleted'
                                                % ( class_name, getattr( item, 'name', id ) ), type="warning" )
    elif deleted is False and item.deleted:
        raise exceptions.ItemDeletionException( '%s "%s" is deleted'
                                                % ( class_name, getattr( item, 'name', id ) ), type="warning" )
    return item


# =============================================================================
class ModelManager( object ):
    model_class = object
    default_order_by = None
    foreign_key_name = None

    def __init__( self, app ):
        assert isinstance( self.model_class, object ), (
            "model class must be set for %s" %( self.__class__.__name__ ) )
        self.model_class_name = self.model_class.__class__.__name__
        assert isinstance( self.default_order_by, tuple ), (
            "default_order_by for %s must be a tuple" %( self.__class__.__name__ ) )

        self.app = app

    #NOTE: at this layer, all ids are expected to be decoded and in int form
    # ------------------------------------------------------------------------- get/read/query
    def query( self, trans, eagerloads=True, filters=None, order_by=None, limit=None, offset=None, **kwargs ):
        #print 'query:', eagerloads, filters, order_by, limit, offset, kwargs
        query = trans.sa_session.query( self.model_class )

        # joined table loading
        if eagerloads is False:
            query = query.enable_eagerloads( False )

#TODO: if non-orm filters are the only option, here is where they'd go
        query = self._apply_filters( query, filters )
        query = self._apply_order_by_limit_offset( query, order_by, limit, offset )
        return query

    def _apply_filters( self, query, filters ):
        if filters is None:
            return query

        if not isinstance( filters, list ):
            filters = [ filters ]
        #note: implicit AND
        for filter in filters:
            query = query.filter( filter )
        return query

    def _munge_filters( self, filtersA, filtersB ):
        # ... which sounds like a euphamism for something
        final_filters = [ self.model_class.id == id ]
        if filtersA is None:
            return filtersB
        if filtersB is None:
            return filtersA
        if not isinstance( filtersA, list ):
            filtersA = [ filtersA ]
        if not isinstance( filtersB, list ):
            filtersB = [ filtersB ]
        return filtersA + filtersB

    def _apply_order_by_limit_offset( self, query, order_by, limit, offset ):
        query = self._apply_order_by( query, order_by )
        return self._apply_limit_offset( query, limit, offset )

    def _apply_order_by( self, query, order_by ):
        if order_by is None:
            #TODO: allow non-tuple default_order_by
            return query.order_by( *self.default_order_by )

        if isinstance( order_by, ( list, tuple ) ):
            return query.order_by( *order_by )
        return query.order_by( order_by )

    def _apply_limit_offset( self, query, limit, offset ):
        if limit is not None:
            query = query.limit( limit )
        if offset is not None:
            query = query.offset( offset )
        return query

    # ......................................................................... common queries
#TODO: needed?
    def one( self, trans, **kwargs ):
        try:
            return self.query( trans, **kwargs ).one()
        # re-raise as serializable errors
        except sqlalchemy.orm.exc.NoResultFound, not_found:
            raise exceptions.ObjectNotFound( self.model_class.__name__ + ' not found' )
        except sqlalchemy.orm.exc.MultipleResultsFound, multi_found:
            raise exceptions.Conflict( 'found more than one ' + self.model_class.__name__ )

    def list( self, trans, **kwargs ):
        return self.query( trans, **kwargs ).all()

    def by_id( self, trans, id, **kwargs ):
        id_filter = self.model_class.id == id
        return self.one( trans, filters=id_filter, **kwargs )

    def _query_by_ids( self, trans, ids, filters=None, **kwargs ):
        ids_filter = self.model_class.id.in_( ids )
        return self.query( trans, filters=self._munge_filters( ids_filter, filters ), **kwargs )

    def by_ids( self, trans, ids, **kwargs ):
        found = self._query_by_ids( trans, ids, **kwargs ).all()
        #TODO: this does not order by the original 'ids' array

        # ...could use get (supposedly since found are in the session, the db won't be hit twice)
        #return map( trans.sa_session.query( self.model_class ).get, ids )

        # ...could implement own version here - slow?
        return self._order_items_by_id( ids, found )
        #return found

    def _order_items_by_id( self, ids, items ):
        """
        Given a list of (unique) ids and a list of items having an 'id' attribute,
        return items that have the given ids in that order.

        If an id in ids is not found or if an item in items doesn't have a given
        id, they will not be in the returned list.
        """
        ID_ATTR_NAME = 'id'
        #TODO:?? aside from sqlalx.get mentioned above, I haven't seen an in-SQL way
        #   to make this happen. This may not be the most efficient way either.
        #NOTE: that this isn't sorting by id - this is matching the order in items to the order in ids
        # move items list into dict by id
        item_dict = {}
        for item in items:
            item_id = getattr( item, ID_ATTR_NAME, None )
            if item_id:
                item_dict[ item_id ] = item
        # pull from map in order of ids
        in_order = []
        for id in ids:
            if id in item_dict:
                in_order.append( item_dict[ id ] )
        return in_order

    # ------------------------------------------------------------------------- create
    def create( self, trans, flush=True, *args, **kwargs ):
        item = self.model_class( *args, **kwargs )
        trans.sa_session.add( item )
        if flush:
            trans.sa_session.flush()
        return item

    def copy( self, trans, item, **kwargs ):
        raise exceptions.NotImplemented( 'Abstract method' )

    # ------------------------------------------------------------------------- update
    def update( self, trans, item, new_values, flush=True, **kwargs ):
        trans.sa_session.add( item )
        for key, value in new_values.items():
            if hasattr( item, key ):
                setattr( item, key, value )
        if flush:
            trans.sa_session.flush()
        return item

    def associate( self, trans, associate_with, item, foreign_key_name=None ):
        foreign_key_name = foreign_key_name or self.foreign_key_name
        setattr( associate_with, foreign_key_name, item )
        return item

    def query_associated( self, trans, associated_model_class, item, foreign_key_name=None ):
        foreign_key_name = foreign_key_name or self.foreign_key_name
        foreign_key = getattr( associated_model_class, foreign_key_name )
        return trans.sa_session.query( associated_model_class ).filter( foreign_key == item )

    # ------------------------------------------------------------------------- delete
    # a rename of sql DELETE to differentiate from the Galaxy notion of mark_as_deleted
    #def remove_from_db( self, trans, item, **kwargs ):
    #    return item


# =============================================================================
class DeletableModelInterface( object ):

    def delete( self, trans, item, flush=True, **kwargs ):
        # often only a matter of 'marking as deleted'
        trans.sa_session.add( item )
        item.deleted = True
        if flush:
            trans.sa_session.flush()
        return item

    def undelete( self, trans, item, flush=True, **kwargs ):
        trans.sa_session.add( item )
        item.deleted = False
        if flush:
            trans.sa_session.flush()
        return item


# =============================================================================
class PurgableModelInterface( DeletableModelInterface ):

    def error_unless_dataset_purge_allowed( self, trans, item, msg=None ):
        if not trans.app.config.allow_user_dataset_purge:
            msg = msg or 'This instance does not allow user dataset purging'
            raise exceptions.ConfigDoesNotAllowException( msg )
            #raise exceptions.ConfigDoesNotAllowException( msg, item=item )
        return item

    def purge( self, trans, item, flush=True, **kwargs ):
        trans.sa_session.add( item )
        item.purged = True
        if flush:
            trans.sa_session.flush()
        return item


# =============================================================================
class AccessibleModelInterface( object ):

    # don't want to override by_id since consumers will also want to fetch w/o any security checks

    def accessible_by_id( self, trans, id, user, **kwargs ):
        item = ModelManager.by_id( self, trans, id )
        return self.error_unless_accessible( trans, item, user )

    def error_unless_accessible( self, trans, item, user ):
        if self.is_accessible( trans, item, user ):
            return item
        raise exceptions.ItemAccessibilityException( "%s is not accessible by user" % self.model_class_name )

    def is_accessible( self, trans, item, user ):
        raise exceptions.NotImplemented( "Abstract Interface Method" )
        #OR? return False

    def list_accessible( self, trans, user, **kwargs ):
        items = ModelManager.list( self, trans, **kwargs )
        return [ self.error_unless_accessible( trans, item, user ) for item in items ]

    def filter_accessible( self, trans, user, **kwargs ):
        items = ModelManager.list( self, trans, **kwargs )
        return filter( lambda item: self.is_accessible( trans, item, user ), items )


# =============================================================================
class ModelSerializingError( exceptions.ObjectAttributeInvalidException ):
    """Thrown when request model values can't be serialized"""
    #TODO: better as 500?
    pass


class ModelDeserializingError( exceptions.ObjectAttributeInvalidException ):
    """Thrown when an incoming value isn't usable by the model
    (bad type, out of range, etc.)
    """
    pass


# -----------------------------------------------------------------------------
class ModelSerializer( object ):
    #model_mgr_class = None

    # primarily designed for turning models into/from JSONable dicts
    #   model   --> ModelSerializer --> JSON
    #   JSON    --> ModelSerializer --> model
    def __init__( self, app ):
        self.app = app
        #TODO:
        #self.mgr = model_mgr_class( app )
        
        # a map of dictionary keys to the functions (often lambdas) that create the values for those keys
        self.serializers = {}
        # add subclass serializers defined there
        self.add_serializers()
        # a list of valid serializable keys that can use the default (string) serializer
        #   this allows us to: 'mention' the key without adding the default serializer
        #NOTE: if a key is requested that is in neither serializable_keys or serializers, it is not returned
        #TODO: rename to 'keys_using_default_serializer'
        #TODO: or (alt) allow key in serializers with None as value (indicating use default_serializer)
        self.serializable_keys = []

        # views are collections of serializable attributes (a named array of keys)
        #   inspired by model.dict_{view}_visible_keys
        self.views = {}
        self.default_view = None

    # ......................................................................... serializing
    def add_serializers( self ):
        # register a map of attribute keys -> functions that will serialize the attribute
        # to be overridden in subclasses
        pass

    def serialize( self, trans, item, keys ):
        # main interface fn for converting a model to a dict
#TODO: try/catch here? add option 'fail_fast'/'raise' to allow optionally *catching* the error without raising it
#   (and then returning the error message in the serialized data)
        returned = {}
        for key in keys:
            # check both serializers and serializable keys
            if key in self.serializers:
                returned[ key ] = self.serializers[ key ]( trans, item, key )
            elif key in self.serializable_keys:
                returned[ key ] = self.default_serializer( trans, item, key )
            # ignore bad/unreg keys
        return returned

    # ... common deserializers for primitives
    def default_serializer( self, trans, item, key ):
        return getattr( item, key )

    def serialize_date( self, trans, item, key ):
        date = getattr( item, key )
        return date.isoformat() if date is not None else None

    # .... common serializers for Galaxy
    def serialize_id( self, trans, item, key ):
        id = getattr( item, key )
        return trans.security.encode_id( id ) if id is not None else None

    #TODO: AnnotatableMixin
    def serialize_annotation( self, trans, item, key ):
#TODO: which is correct here?
        #user = item.user
        user = trans.user
        return item.get_item_annotation_str( trans.sa_session, user, item )

    #TODO: TaggableMixin
    def serialize_tags( self, trans, item, key ):
#TODO: whose tags are these?
        return [ tag.user_tname + ( ':' + tag.user_value if tag.user_value else '' ) for tag in item.tags ]

    # ......................................................................... serializing to a view
    # where a view is a predefied list of keys to serialize
    def serialize_to_view( self, trans, item, view=None, keys=None ):
#TODO: if keys and view - munge view and keys
#    : if keys but no view - use keys
#    : if no keys but view - use view
#    : if no keys and no view - use default view
        keys = keys or []
        all_keys = self.view_to_list( view ) + keys
        return self.serialize( trans, item, all_keys )

    def view_to_list( self, view=None ):
        if view is None:
            view = self.default_view
        if view not in self.views:
            raise ModelSerializingError( 'unknown view', view=view, available_views=self.views )
        return self.views[ view ]

    #TODO: this is more util/gen. use
    def pluck_from_list( self, l, elems ):
        """
        Removes found elems from list l and returns list of found elems if found.
        """
        found = []
        for elem in elems:
            try:
                index = l.index( elem )
                found.append( l.pop( index ) )
            except ValueError, val_err:
                pass
        return found

    # ......................................................................... aliases
    #def to_dict( self, trans, item, view=None, view_keys=None ):
    #    view_keys = view_keys or self.view_to_list( view )
    #    return self.serialize( trans, item, view_keys )


# -----------------------------------------------------------------------------
class ModelValidator( object ):

    def __init__( self, app, *args, **kwargs ):
        self.app = app

    def type( self, key, val, types ):
        if not isinstance( val, types ):
            msg = 'must be a type: %s' % ( str( types ) )
            raise exceptions.RequestParameterInvalidException( msg, key=key, val=val )
        return val

    # validators for primitives
    def basestring( self, key, val ):
        return self.type( key, val, basestring )

    def nullable_basestring( self, key, val ):
        return self.type( key, val, ( basestring, type( None ) ) )

    def bool( self, key, val ):
        return self.type( key, val, bool )

    def int( self, key, val ):
        return self.type( key, val, int )

    def int_range( self, key, val, min=None, max=None ):
        val = self.type( key, val, int )
        if val < min:
            raise exceptions.RequestParameterInvalidException( "less than minimum", key=key, val=val, min=min )
        if val > max:
            raise exceptions.RequestParameterInvalidException( "greater than maximum", key=key, val=val, max=max )
        return val

    def basestring_list( self, key, val ):
        val = self.type( key, val, list )
        return [ self.basestring( key, elem ) for elem in val ]

    # validators for Galaxy
    def genome_build( self, trans, key, val ):
        #TODO: is this correct?
        if val is None:
            return '?'
        # wot...why tuples?
        if val not in dict( trans.db_builds ):
            raise exceptions.RequestParameterInvalidException( "invalid reference", key=key, val=val )
        return val

    #def slug( self, trans, item, key, val ):
    #    """validate slug"""
    #    pass


# -----------------------------------------------------------------------------
class ModelDeserializer( object ):
    #model_mgr_class = None

    # primarily designed for creating models from dicts
    #   Dict    --> ModelDeserializer --> model
    def __init__( self, app ):
        self.app = app
        #TODO:
        #self.mgr = model_mgr_class( app )

        self.deserializers = {}
        self.add_deserializers()
        self.deserializable_keys = []
        self.validate = ModelValidator( self.app )

    # ......................................................................... deserializing
    def add_deserializers( self ):
        # register a map of attribute keys -> functions that will deserialize data into the attribute
        # to be overridden in subclasses
        pass

    def deserialize( self, trans, item, data, flush=True ):
        new_dict = {}
        for key, val in data.items():
            #print key, val
            if key in self.deserializers:
                #print '\t deserializer:', self.deserializers[ key ]
                new_dict[ key ] = self.deserializers[ key ]( trans, item, key, val )
            #!important: don't error on unreg. keys -- many clients will add weird ass keys onto the model
        #TODO:?? here or in manager?
        if flush and len( new_dict ):
            trans.sa_session.add( item )
            trans.sa_session.flush()
        return new_dict

    # ... common deserializers for primitives
    def default_deserializer( self, trans, item, key, val ):
        #TODO: sets the item attribute to value (this may not work in all instances)

        # only do the following if val == getattr( item, key )
        if hasattr( item, key ) and getattr( item, key ) != val:
            setattr( item, key, val )
        return val

    def deserialize_basestring( self, trans, item, key, val ):
        val = self.validate.basestring( key, val )
        return self.default_deserializer( trans, item, key, val )

    def deserialize_bool( self, trans, item, key, val ):
        val = self.validate.bool( key, val )
        return self.default_deserializer( trans, item, key, val )

    def deserialize_int( self, trans, item, key, val, min=None, max=None ):
        val = self.validate.int_range( key, val, min, max )
        return self.default_deserializer( trans, item, key, val )

    # ... common deserializers for Galaxy
    def deserialize_genome_build( self, trans, item, key, val ):
        val = self.validate.genome_build( trans, key, val )
        return self.default_deserializer( trans, item, key, val )

    def deserialize_annotation( self, trans, item, key, val ):
        val = self.validate.nullable_basestring( key, val )
        #TODO: have to assume trans.user here...
        return item.add_item_annotation( trans.sa_session, trans.user, item, val )

    def deserialize_tags( self, trans, item, key, val ):
        new_tags_list = self.validate.basestring_list( key, val )
        #TODO: have to assume trans.user here...
        user = trans.user
        #TODO: duped from tags manager - de-dupe when moved to taggable mixin
        tag_handler = trans.app.tag_handler
        tag_handler.delete_item_tags( trans, user, item )
        new_tags_str = ','.join( new_tags_list )
        tag_handler.apply_item_tags( trans, user, item, unicode( new_tags_str.encode( 'utf-8' ), 'utf-8' ) )
        #trans.sa_session.flush()
        return item.tags

    #def deserialize_rating( self, trans, item, key, val ):
    #    val = self.validate.int_range( key, val, 0, 5 )
    #    return self.set_rating...( trans, item, val, user=trans.user )

    # ......................................................................... aliases
    #def from_dict( self, trans, item, data ):
    #    self.deserialize( trans, item, data )


# -----------------------------------------------------------------------------
#TODO: these are of questionable value if we don't want to enable users to delete/purge via update
class DeletableModelDeserializer( object ):

    def add_deserializers( self ):
        self.deserializers[ 'deleted' ] = self.deserialize_deleted

    def deserialize_deleted( self, trans, item, key, val ):
        new_deleted = self.validate.bool( key, val )
        if new_deleted == item.deleted:
            return item.deleted
        #TODO:?? flush=False?
        if new_deleted:
            self.mgr.delete( trans, item )
        else:
            self.mgr.undelete( trans, item )
        return item.deleted


# -----------------------------------------------------------------------------
class PurgableModelDeserializer( DeletableModelDeserializer ):

    def add_deserializers( self ):
        self.deserializers[ 'purged' ] = self.deserialize_purged

    def deserialize_purged( self, trans, item, key, val ):
        new_purged = self.validate.bool( key, val )
        if new_purged == item.purged:
            return item.purged
        if new_purged:
            self.mgr.purge( trans, item )
        return self.purged


# -----------------------------------------------------------------------------
class TaggableSerializer( object ):

    def add_serializers( self ):
        self.serializers[ 'tags' ] = self.serialize_tags

    def serialize_tags( self, trans, item, key ):
        if not hasattr( item, 'tags' ):
            return None

        tags_str_list = []
        for tag in item.tags:
            tag_str = tag.user_tname
            if tag.value is not None:
                tag_str += ":" + tag.user_value
            tags_str_list.append( tag_str )
        print '\t tags_str_list', tags_str_list
        return tags_str_list


class AnnotatableSerializable( object ):

    def add_serializers( self ):
        self.serializers[ 'annotation' ] = lambda t, i, k: unicode( self.get_annotation( t, i ) )


class RatableSerializable( object ):

    def add_serializers( self ):
        self.serializers[ 'user_rating' ] = self.serialize_user_rating
        self.serializers[ 'community_rating' ] = self.serialize_community_rating

    def serialize_user_rating( self, trans, item, key ):
        pass

    def serialize_community_rating( self, trans, item, key ):
        pass

