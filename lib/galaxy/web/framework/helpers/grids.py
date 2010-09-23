from galaxy.model.orm import *
from galaxy.web.base.controller import *
from galaxy.web.framework.helpers import iff
from galaxy.web import url_for
from galaxy.util.json import from_json_string, to_json_string
from galaxy.util.odict import odict
from galaxy.web.framework.helpers import to_unicode
from galaxy import model
from galaxy.model.item_attrs import *

import sys, logging, math

log = logging.getLogger( __name__ )

class Grid( object ):
    """
    Specifies the content and format of a grid (data table).
    """
    webapp = None
    title = ""
    exposed = True
    model_class = None
    template = "grid_base.mako"
    async_template = "grid_base_async.mako"
    use_async = False
    global_actions = []
    columns = []
    operations = []
    standard_filters = []
    # Any columns that are filterable (either standard or advanced) should have a default value set in the default filter.
    default_filter = {}
    default_sort_key = None
    preserve_state = False
    use_paging = False
    num_rows_per_page = 25
    # Set preference names.
    cur_filter_pref_name = ".filter"
    cur_sort_key_pref_name = ".sort_key"    
    pass_through_operations = {}
    def __init__( self ):
        # Determine if any multiple row operations are defined
        self.has_multiple_item_operations = False
        for operation in self.operations:
            if operation.allow_multiple:
                self.has_multiple_item_operations = True
                break
                
        # If a column does not have a model class, set the column's model class 
        # to be the grid's model class.
        for column in self.columns:
            if not column.model_class:
                column.model_class = self.model_class
        
    def __call__( self, trans, **kwargs ):
        # Get basics.
        webapp = kwargs.get( 'webapp', 'galaxy' )
        status = kwargs.get( 'status', None )
        message = kwargs.get( 'message', None )
        # Build a base filter and sort key that is the combination of the saved state and defaults.
        # Saved state takes preference over defaults.
        base_filter = {}
        if self.default_filter:
            # default_filter is a dictionary that provides a default set of filters based on the grid's columns.
            base_filter = self.default_filter.copy()
        base_sort_key = self.default_sort_key
        if self.preserve_state:
            pref_name = unicode( self.__class__.__name__ + self.cur_filter_pref_name )
            if pref_name in trans.get_user().preferences:
                saved_filter = from_json_string( trans.get_user().preferences[pref_name] )
                base_filter.update( saved_filter )
            pref_name = unicode( self.__class__.__name__ + self.cur_sort_key_pref_name )
            if pref_name in trans.get_user().preferences:
                base_sort_key = from_json_string( trans.get_user().preferences[pref_name] )
        # Build initial query
        query = self.build_initial_query( trans, **kwargs )
        query = self.apply_query_filter( trans, query, **kwargs )
        # Maintain sort state in generated urls
        extra_url_args = {}
        # Determine whether use_default_filter flag is set.
        use_default_filter_str = kwargs.get( 'use_default_filter' )
        use_default_filter = False
        if use_default_filter_str:
            use_default_filter = ( use_default_filter_str.lower() == 'true' )
        # Process filtering arguments to (a) build a query that represents the filter and (b) build a
        # dictionary that denotes the current filter.
        cur_filter_dict = {}
        for column in self.columns:
            if column.key:
                # Get the filter criterion for the column. Precedence is (a) if using default filter, only look there; otherwise, 
                # (b) look in kwargs; and (c) look in base filter.
                column_filter = None
                if use_default_filter:
                    if self.default_filter:
                        column_filter = self.default_filter.get( column.key )
                elif "f-" + column.key in kwargs:
                    column_filter = kwargs.get( "f-" + column.key )
                elif column.key in base_filter:
                    column_filter = base_filter.get( column.key )
                # Method (1) combines a mix of strings and lists of strings into a single string and (2) attempts to de-jsonify all strings.
                def from_json_string_recurse(item):
                   decoded_list = []
                   if isinstance( item, basestring):
                       try:
                           # Not clear what we're decoding, so recurse to ensure that we catch everything.
                            decoded_item = from_json_string( item ) 
                            if isinstance( decoded_item, list):
                                decoded_list = from_json_string_recurse( decoded_item )
                            else:
                                decoded_list = [ unicode( decoded_item ) ]
                       except ValueError:
                           decoded_list = [ unicode ( item ) ]
                   elif isinstance( item, list):
                       return_val = []
                       for element in item:
                           a_list = from_json_string_recurse( element )
                           decoded_list = decoded_list + a_list
                   return decoded_list
                # If column filter found, apply it.
                if column_filter is not None:
                    # TextColumns may have a mix of json and strings.
                    if isinstance( column, TextColumn ):
                        column_filter = from_json_string_recurse( column_filter )
                        if len( column_filter ) == 1:
                            column_filter = column_filter[0]
                    # Interpret ',' as a separator for multiple terms.
                    if isinstance( column_filter, basestring ) and column_filter.find(',') != -1:
                        column_filter = column_filter.split(',')
                    # If filter criterion is empty, do nothing.
                    if column_filter == '':
                        continue
                    # Update query.
                    query = column.filter( trans, trans.get_user(), query, column_filter )
                    # Upate current filter dict.
                    cur_filter_dict[ column.key ] = column_filter
                    # Carry filter along to newly generated urls; make sure filter is a string so
                    # that we can encode to UTF-8 and thus handle user input to filters.
                    if isinstance( column_filter, list ):
                        # Filter is a list; process each item.
                        for filter in column_filter:
                            if not isinstance( filter, basestring ):
                                filter = unicode( filter ).encode("utf-8")
                        extra_url_args[ "f-" + column.key ] = to_json_string( column_filter ) 
                    else:
                        # Process singleton filter.
                        if not isinstance( column_filter, basestring ):
                            column_filter = unicode(column_filter)
                        extra_url_args[ "f-" + column.key ] = column_filter.encode("utf-8")
        # Process sort arguments.
        sort_key = None
        if 'sort' in kwargs:
            sort_key = kwargs['sort']
        elif base_sort_key:
            sort_key = base_sort_key
        if sort_key:            
            if sort_key.startswith( "-" ):
                ascending = False
                column_key = sort_key[1:]
            else:
                ascending = True
                column_key = sort_key
            # Sort key is a column key.
            for column in self.columns:
                if column.key == column_key:
                    query = column.sort( query, ascending )
                    break
            extra_url_args['sort'] = sort_key
        # There might be a current row
        current_item = self.get_current_item( trans, **kwargs )
        # Process page number.
        if self.use_paging:
            if 'page' in kwargs:
                if kwargs['page'] == 'all':
                    page_num = 0 
                else:
                    page_num = int( kwargs['page'] )
            else:
                page_num = 1
                
            if page_num == 0:
                # Show all rows in page.
                total_num_rows = query.count()
                page_num = 1
                num_pages = 1
            else:
                # Show a limited number of rows. Before modifying query, get the total number of rows that query 
                # returns so that the total number of pages can be computed.
                total_num_rows = query.count()
                query = query.limit( self.num_rows_per_page ).offset( ( page_num-1 ) * self.num_rows_per_page )
                num_pages = int ( math.ceil( float( total_num_rows ) / self.num_rows_per_page ) )
        else:
            # Defaults.
            page_num = 1
            num_pages = 1
        # Preserve grid state: save current filter and sort key.
        if self.preserve_state:
            pref_name = unicode( self.__class__.__name__ + self.cur_filter_pref_name )
            trans.get_user().preferences[pref_name] = unicode( to_json_string( cur_filter_dict ) )
            
            if sort_key:
                pref_name = unicode( self.__class__.__name__ + self.cur_sort_key_pref_name )
                trans.get_user().preferences[pref_name] = unicode( to_json_string( sort_key ) )
            trans.sa_session.flush()
        # Log grid view.
        context = unicode( self.__class__.__name__ )
        params = cur_filter_dict.copy()
        params['sort'] = sort_key
        params['async'] = ( 'async' in kwargs )
        params['webapp'] = webapp
        trans.log_action( trans.get_user(), unicode( "grid.view" ), context, params )
        # Render grid.
        def url( *args, **kwargs ):
            # Only include sort/filter arguments if not linking to another
            # page. This is a bit of a hack.
            if 'action' in kwargs:
                new_kwargs = dict()
            else:
                new_kwargs = dict( extra_url_args )
            # Extend new_kwargs with first argument if found
            if len(args) > 0:
                new_kwargs.update( args[0] )
            new_kwargs.update( kwargs )
            # We need to encode item ids
            if 'id' in new_kwargs:
                id = new_kwargs[ 'id' ]
                if isinstance( id, list ):
                    new_args[ 'id' ] = [ trans.security.encode_id( i ) for i in id ]
                else:
                    new_kwargs[ 'id' ] = trans.security.encode_id( id )
            return url_for( **new_kwargs )
        use_panels = ( kwargs.get( 'use_panels', False ) in [ True, 'True', 'true' ] )
        async_request = ( ( self.use_async ) and ( kwargs.get( 'async', False ) in [ True, 'True', 'true'] ) )
        # Currently, filling the template returns a str object; this requires decoding the string into a 
        # unicode object within mako templates. What probably should be done is to return the template as 
        # utf-8 unicode; however, this would require encoding the object as utf-8 before returning the grid
        # results via a controller method, which is require substantial changes. Hence, for now, return grid 
        # as str.
        return trans.fill_template( iff( async_request, self.async_template, self.template ),
                                    grid=self,
                                    query=query,
                                    cur_page_num = page_num,
                                    num_pages = num_pages,
                                    default_filter_dict=self.default_filter,
                                    cur_filter_dict=cur_filter_dict,
                                    sort_key=sort_key,
                                    current_item=current_item,
                                    ids = kwargs.get( 'id', [] ),
                                    url = url,
                                    status = status,
                                    message = message,
                                    use_panels=use_panels,
                                    webapp=webapp,
                                    # Pass back kwargs so that grid template can set and use args without
                                    # grid explicitly having to pass them.
                                    kwargs=kwargs )
    def get_ids( self, **kwargs ):
        id = []
        if 'id' in kwargs:
            id = kwargs['id']
            # Coerce ids to list
            if not isinstance( id, list ):
                id = id.split( "," )
            # Ensure ids are integers
            try:
                id = map( int, id )
            except:
                error( "Invalid id" )
        return id
    # ---- Override these ----------------------------------------------------
    def handle_operation( self, trans, operation, ids, **kwargs ):
        pass
    def get_current_item( self, trans, **kwargs ):
        return None
    def build_initial_query( self, trans, **kwargs ):
        return trans.sa_session.query( self.model_class )
    def apply_query_filter( self, trans, query, **kwargs ):
        # Applies a database filter that holds for all items in the grid.
        # (gvk) Is this method necessary?  Why not simply build the entire query,
        # including applying filters in the build_initial_query() method?
        return query
    
class GridColumn( object ):
    def __init__( self, label, key=None, model_class=None, method=None, format=None, \
                  link=None, attach_popup=False, visible=True, ncells=1, \
                  # Valid values for filterable are ['standard', 'advanced', None]
                  filterable=None, sortable=True ):
        """
        Create a grid column. 
        """
        self.label = label
        self.key = key
        self.model_class = model_class
        self.method = method
        self.format = format
        self.link = link
        self.attach_popup = attach_popup
        self.visible = visible
        self.ncells = ncells
        self.filterable = filterable
        # Column must have a key to be sortable.
        self.sortable = ( self.key is not None and sortable )
            
    def get_value( self, trans, grid, item ):
        if self.method:
            value = getattr( grid, self.method )( trans, item )
        elif self.key:
            value = getattr( item, self.key )
        else:
            value = None
        if self.format:
            value = self.format( value )
        return value
        
    def get_link( self, trans, grid, item ):
        if self.link and self.link( item ):
            return self.link( item )
        return None
        
    def filter( self, trans, user, query, column_filter ):
        """ Modify query to reflect the column filter. """
        if column_filter == "All":
            pass
        if column_filter == "True":
            query = query.filter_by( **{ self.key: True } )
        elif column_filter == "False":
            query = query.filter_by( **{ self.key: False } )
        return query
        
    def get_accepted_filters( self ):
        """ Returns a list of accepted filters for this column. """
        accepted_filters_vals = [ "False", "True", "All" ]
        accepted_filters = []
        for val in accepted_filters_vals:
            args = { self.key: val }
            accepted_filters.append( GridColumnFilter( val, args) )
        return accepted_filters
    
    def sort( self, query, ascending ):
        """ Sort query using this column. """
        if ascending:
            query = query.order_by( self.model_class.table.c.get( self.key ).asc() ) 
        else:
            query = query.order_by( self.model_class.table.c.get( self.key ).desc() )
        return query
        
class ReverseSortColumn( GridColumn ):
    """ Column that reverses sorting; this is useful when the natural sort is descending. """
    def sort( self, query, ascending ):
        return GridColumn.sort( self, query, (not ascending) )
        
class TextColumn( GridColumn ):
    """ Generic column that employs freetext and, hence, supports freetext, case-independent filtering. """
    def filter( self, trans, user, query, column_filter ):
        """ Modify query to filter using free text, case independence. """
        if column_filter == "All":
            pass
        elif column_filter:
            query = query.filter( self.get_filter( trans, user, column_filter ) )
        return query
    def get_filter( self, trans, user, column_filter ):
        """ Returns a SQLAlchemy criterion derived from column_filter. """ 
        if isinstance( column_filter, basestring ):
            return self.get_single_filter( user, column_filter )
        elif isinstance( column_filter, list ):
            clause_list = []
            for filter in column_filter:
                clause_list.append( self.get_single_filter( user, filter ) )
            return and_( *clause_list )
    def get_single_filter( self, user, a_filter ):
        """ Returns a SQLAlchemy criterion derived for a single filter. Single filter is the most basic filter--usually a string--and cannot be a list. """
        model_class_key_field = getattr( self.model_class, self.key )
        return func.lower( model_class_key_field ).like( "%" + a_filter.lower() + "%" )
    def sort( self, query, ascending ):
        """Sort column using case-insensitive alphabetical sorting."""
        if ascending:
            query = query.order_by( func.lower( self.model_class.table.c.get( self.key ) ).asc() ) 
        else:
            query = query.order_by( func.lower( self.model_class.table.c.get( self.key ) ).desc() )
        return query

class DateTimeColumn( TextColumn ):
    def sort( self, query, ascending ):
        """Sort query using this column."""
        return GridColumn.sort( self, query, ascending )

class IntegerColumn( TextColumn ):
    """
    Integer column that employs freetext, but checks that the text is an integer, 
    so support filtering on integer values.
    
    IMPORTANT NOTE: grids that use this column type should not include the column
    in the cols_to_filter list of MulticolFilterColumn ( i.e., searching on this
    column type should not be performed in the grid's standard search - it won't
    throw exceptions, but it also will not find what you're looking for ).  Grids
    that search on this column should use 'filterable="advanced"' so that searching
    is only performed in the advanced search component, restricting the search to
    the specific column.
    
    This is useful for searching on object ids or other integer columns.  See the 
    JobIdColumn column in the SpecifiedDateListGrid class in the jobs controller of
    the reports webapp for an example.
    """
    def get_single_filter( self, user, a_filter ):
        model_class_key_field = getattr( self.model_class, self.key )
        assert int( a_filter ), "The search entry must be an integer"
        return model_class_key_field == int( a_filter )
    def sort( self, query, ascending ):
        """Sort query using this column."""
        return GridColumn.sort( self, query, ascending )
        
class CommunityRatingColumn( GridColumn, UsesItemRatings ):
    """ Column that displays community ratings for an item. """
    
    def get_value( self, trans, grid, item ):
        ave_item_rating, num_ratings = self.get_ave_item_rating_data( trans.sa_session, item )
        return trans.fill_template( "community_rating.mako", 
                                    ave_item_rating=ave_item_rating, 
                                    num_ratings=num_ratings, 
                                    item_id=trans.security.encode_id( item.id ) )
    def sort( self, query, ascending ):
        def get_foreign_key( source_class, target_class ):
            """ Returns foreign key in source class that references target class. """
            target_fk = None
            for fk in source_class.table.foreign_keys:
                if fk.references( target_class.table ):
                    target_fk = fk
                    break
            if not target_fk:
                raise RuntimeException( "No foreign key found between objects: %s, %s" % source_class.table, target_class.table )
            return target_fk
        # Get the columns that connect item's table and item's rating association table.
        item_rating_assoc_class = getattr( model, '%sRatingAssociation' % self.model_class.__name__ )
        foreign_key = get_foreign_key( item_rating_assoc_class, self.model_class )
        fk_col = foreign_key.parent
        referent_col = foreign_key.get_referent( self.model_class.table )
        # Do sorting using a subquery.
        db_session = query.session
        # Subquery to get average rating for each item.
        ave_rating_subquery = db_session.query( fk_col, \
                                                func.avg( item_rating_assoc_class.table.c.rating \
                                                ).label('avg_rating') ).group_by( fk_col ).subquery()
        # Integrate subquery into main query.
        query = query.outerjoin( (ave_rating_subquery, referent_col==ave_rating_subquery.columns[fk_col.name]) )
        # Sort using subquery results; use coalesce to avoid null values.
        if not ascending: # TODO: for now, reverse sorting b/c first sort is ascending, and that should be the natural sort.
            query = query.order_by( func.coalesce( ave_rating_subquery.c.avg_rating, 0 ).asc() )
        else:
            query = query.order_by( func.coalesce( ave_rating_subquery.c.avg_rating, 0 ).desc() )
        return query

class OwnerAnnotationColumn( TextColumn, UsesAnnotations ):
    """ Column that displays and filters item owner's annotations. """
    def __init__( self, col_name, key, model_class=None, model_annotation_association_class=None, filterable=None ):
        GridColumn.__init__( self, col_name, key=key, model_class=model_class, filterable=filterable )
        self.sortable = False
        self.model_annotation_association_class = model_annotation_association_class
    def get_value( self, trans, grid, item ):
        """ Returns first 150 characters of annotation. """
        annotation = self.get_item_annotation_str( trans.sa_session, item.user, item )
        if annotation:
            ann_snippet = annotation[:155]
            if len( annotation ) > 155:
                ann_snippet = ann_snippet[ :ann_snippet.rfind(' ') ]
                ann_snippet += "..."
        else:
            ann_snippet = ""
        return ann_snippet
    def get_single_filter( self, user, a_filter ):
        """ Filter by annotation and annotation owner. """
        return self.model_class.annotations.any( 
            and_( func.lower( self.model_annotation_association_class.annotation ).like( "%" + a_filter.lower() + "%" ), 
                # TODO: not sure why, to filter by owner's annotations, we have to do this rather than 
                # 'self.model_class.user==self.model_annotation_association_class.user'
                self.model_annotation_association_class.table.c.user_id==self.model_class.table.c.user_id ) )            
                        
class CommunityTagsColumn( TextColumn ):
    """ Column that supports community tags. """
    def __init__( self, col_name, key, model_class=None, model_tag_association_class=None, filterable=None, grid_name=None ):
        GridColumn.__init__( self, col_name, key=key, model_class=model_class, filterable=filterable, sortable=False )
        self.model_tag_association_class = model_tag_association_class
        # Column-specific attributes.
        self.grid_name = grid_name
    def get_value( self, trans, grid, item ):
        return trans.fill_template( "/tagging_common.mako", tag_type="community", trans=trans, user=trans.get_user(), tagged_item=item, elt_context=self.grid_name,
                                    in_form=True, input_size="20", tag_click_fn="add_tag_to_grid_filter", use_toggle_link=True )
    def filter( self, trans, user, query, column_filter ):
        """ Modify query to filter model_class by tag. Multiple filters are ANDed. """
        if column_filter == "All":
            pass
        elif column_filter:
            query = query.filter( self.get_filter( trans, user, column_filter ) )
        return query
    def get_filter( self, trans, user, column_filter ):
            # Parse filter to extract multiple tags.
            if isinstance( column_filter, list ):
                # Collapse list of tags into a single string; this is redundant but effective. TODO: fix this by iterating over tags.
                column_filter = ",".join( column_filter )
            raw_tags = trans.app.tag_handler.parse_tags( column_filter.encode( "utf-8" ) )
            clause_list = []
            for name, value in raw_tags.items():
                if name:
                    # Filter by all tags.
                    clause_list.append( self.model_class.tags.any( func.lower( self.model_tag_association_class.user_tname ).like( "%" + name.lower() + "%" ) ) )
                    if value:
                        # Filter by all values.
                        clause_list.append( self.model_class.tags.any( func.lower( self.model_tag_association_class.user_value ).like( "%" + value.lower() + "%" ) ) )
            return and_( *clause_list )
            
class IndividualTagsColumn( CommunityTagsColumn ):
    """ Column that supports individual tags. """
    def get_value( self, trans, grid, item ):
        return trans.fill_template( "/tagging_common.mako",
                                    tag_type="individual",
                                    user=trans.user,
                                    tagged_item=item,
                                    elt_context=self.grid_name,
                                    in_form=True,
                                    input_size="20",
                                    tag_click_fn="add_tag_to_grid_filter",
                                    use_toggle_link=True )
    def get_filter( self, trans, user, column_filter ):
            # Parse filter to extract multiple tags.
            if isinstance( column_filter, list ):
                # Collapse list of tags into a single string; this is redundant but effective. TODO: fix this by iterating over tags.
                column_filter = ",".join( column_filter )
            raw_tags = trans.app.tag_handler.parse_tags( column_filter.encode( "utf-8" ) )
            clause_list = []
            for name, value in raw_tags.items():
                if name:
                    # Filter by individual's tag names.
                    clause_list.append( self.model_class.tags.any( and_( func.lower( self.model_tag_association_class.user_tname ).like( "%" + name.lower() + "%" ), self.model_tag_association_class.user == user ) ) )
                    if value:
                        # Filter by individual's tag values.
                        clause_list.append( self.model_class.tags.any( and_( func.lower( self.model_tag_association_class.user_value ).like( "%" + value.lower() + "%" ), self.model_tag_association_class.user == user ) ) )
            return and_( *clause_list )
            
class MulticolFilterColumn( TextColumn ):
    """ Column that performs multicolumn filtering. """
    def __init__( self, col_name, cols_to_filter, key, visible, filterable="default" ):
        GridColumn.__init__( self, col_name, key=key, visible=visible, filterable=filterable)
        self.cols_to_filter = cols_to_filter
    def filter( self, trans, user, query, column_filter ):
        """ Modify query to filter model_class by tag. Multiple filters are ANDed. """
        if column_filter == "All":
            return query
        if isinstance( column_filter, list):
            clause_list = []
            for filter in column_filter:
                part_clause_list = []
                for column in self.cols_to_filter:
                    part_clause_list.append( column.get_filter( trans, user, filter ) )
                clause_list.append( or_( *part_clause_list ) )
            complete_filter = and_( *clause_list )
        else:
            clause_list = []
            for column in self.cols_to_filter:
                clause_list.append( column.get_filter( trans, user, column_filter ) )
            complete_filter = or_( *clause_list )
        return query.filter( complete_filter )
                
class OwnerColumn( TextColumn ):
    """ Column that lists item's owner. """
    def get_value( self, trans, grid, item ):
        return item.user.username
    def sort( self, query, ascending ):
        """ Sort column using case-insensitive alphabetical sorting on item's username. """
        if ascending:
            query = query.order_by( func.lower ( self.model_class.username ).asc() ) 
        else:
            query = query.order_by( func.lower( self.model_class.username ).desc() )
        return query

class PublicURLColumn( TextColumn ):
    """ Column displays item's public URL based on username and slug. """
    def get_link( self, trans, grid, item ):
        if item.user.username and item.slug:
            return dict( action='display_by_username_and_slug', username=item.user.username, slug=item.slug )
        elif not item.user.username:
            # TODO: provide link to set username.
            return None
        elif not item.user.slug:
            # TODO: provide link to set slug.
            return None

class DeletedColumn( GridColumn ):
    """ Column that tracks and filters for items with deleted attribute. """
    def get_accepted_filters( self ):
        """ Returns a list of accepted filters for this column. """
        accepted_filter_labels_and_vals = { "active" : "False", "deleted" : "True", "all": "All" }
        accepted_filters = []
        for label, val in accepted_filter_labels_and_vals.items():
           args = { self.key: val }
           accepted_filters.append( GridColumnFilter( label, args) )
        return accepted_filters

class StateColumn( GridColumn ):
    """
    Column that tracks and filters for items with state attribute.

    IMPORTANT NOTE: self.model_class must have a states Bunch or dict if
    this column type is used in the grid.
    """
    def get_value( self, trans, grid, item ):
        return item.state
    def filter( self, trans, user, query, column_filter ):
        """Modify query to filter self.model_class by state."""
        if column_filter == "All":
            pass
        elif column_filter in [ v for k, v in self.model_class.states.items() ]:
            query = query.filter( self.model_class.state == column_filter )
        return query
    def get_accepted_filters( self ):
        """Returns a list of accepted filters for this column."""
        all = GridColumnFilter( 'all', { self.key : 'All' } )
        accepted_filters = [ all ]
        for k, v in self.model_class.states.items():
           args = { self.key: v }
           accepted_filters.append( GridColumnFilter( v, args) )
        return accepted_filters

class SharingStatusColumn( GridColumn ):
    """ Grid column to indicate sharing status. """
    def get_value( self, trans, grid, item ):
        # Delete items cannot be shared.
        if item.deleted:
            return ""
        # Build a list of sharing for this item.
        sharing_statuses = []
        if item.users_shared_with:
            sharing_statuses.append( "Shared" )
        if item.importable:
            sharing_statuses.append( "Accessible" )
        if item.published:
            sharing_statuses.append( "Published" )
        return ", ".join( sharing_statuses )
    def get_link( self, trans, grid, item ):
        if not item.deleted and ( item.users_shared_with or item.importable or item.published ):
            return dict( operation="share or publish", id=item.id )
        return None
    def filter( self, trans, user, query, column_filter ):
        """ Modify query to filter histories by sharing status. """
        if column_filter == "All":
            pass
        elif column_filter:
            if column_filter == "private":
                query = query.filter( self.model_class.users_shared_with == None )
                query = query.filter( self.model_class.importable == False )
            elif column_filter == "shared":
                query = query.filter( self.model_class.users_shared_with != None )
            elif column_filter == "accessible":
                query = query.filter( self.model_class.importable == True )
            elif column_filter == "published":
                query = query.filter( self.model_class.published == True )
        return query
    def get_accepted_filters( self ):
        """ Returns a list of accepted filters for this column. """
        accepted_filter_labels_and_vals = odict()
        accepted_filter_labels_and_vals["private"] = "private"
        accepted_filter_labels_and_vals["shared"] = "shared"
        accepted_filter_labels_and_vals["accessible"] = "accessible"
        accepted_filter_labels_and_vals["published"] = "published"
        accepted_filter_labels_and_vals["all"] = "All"
        accepted_filters = []
        for label, val in accepted_filter_labels_and_vals.items():
            args = { self.key: val }
            accepted_filters.append( GridColumnFilter( label, args) )
        return accepted_filters

class GridOperation( object ):
    def __init__( self, label, key=None, condition=None, allow_multiple=True, allow_popup=True,
                  target=None, url_args=None, async_compatible=False, confirm=None ):
        self.label = label
        self.key = key
        self.allow_multiple = allow_multiple
        self.allow_popup = allow_popup
        self.condition = condition
        self.target = target
        self.url_args = url_args
        self.async_compatible = async_compatible
        # if 'confirm' is set, then ask before completing the operation
        self.confirm = confirm
    def get_url_args( self, item ):
        if self.url_args:
            temp = dict( self.url_args )
            temp['id'] = item.id
            return temp
        else:
            return dict( operation=self.label, id=item.id )
    def allowed( self, item ):
        if self.condition:
            return self.condition( item )
        else:
            return True
            
class DisplayByUsernameAndSlugGridOperation( GridOperation ):
    """ Operation to display an item by username and slug. """
    def get_url_args( self, item ):
        return { 'action' : 'display_by_username_and_slug', 'username' : item.user.username, 'slug' : item.slug }
        
class GridAction( object ):
    def __init__( self, label=None, url_args=None ):
        self.label = label
        self.url_args = url_args
        
class GridColumnFilter( object ):
    def __init__( self, label, args=None ):
        self.label = label
        self.args = args
    def get_url_args( self ):
        rval = {}
        for k, v in self.args.items():
            rval[ "f-" + k ] = v
        return rval
