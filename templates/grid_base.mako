<%!
    from galaxy.web.framework.helpers.grids import TextColumn

    def inherit(context):
        kwargs = context.get( 'kwargs', {} )
        if kwargs.get( 'embedded', False ):
            # No inheritance - using only embeddable content (self.body)
            return None

        if context.get('use_panels'):
            if context.get('webapp'):
                webapp = context.get('webapp')
            else:
                webapp = 'galaxy'
            return '/webapps/%s/base_panels.mako' % webapp
        else:
            return '/base.mako'
%>
<%inherit file="${inherit(context)}"/>
<%namespace file="/display_common.mako" import="get_class_plural" />

##
## Override methods from base.mako and base_panels.mako
##

<%def name="init( embedded=False, insert=None )">
<%
    self.has_left_panel         = False
    self.has_right_panel        = False
    self.message_box_visible    = False
    self.overlay_visible        = False
    self.active_view            = 'user'
%>
</%def>

## render title
<%def name="title()">${grid.title}</%def>

## render in center panel
<%def name="center_panel()">
    ${self.load()}
</%def>

## render in body
<%def name="body()">
    ${self.load()}
</%def>

## creates grid
<%def name="load( embedded=False, insert=None )">
    <!-- grid_base.mako -->
    ## imports
    ${h.css( "autocomplete_tagging", "jquery.rating" )}
    ${h.js("libs/jquery/jquery.autocomplete", "galaxy.autocom_tagging", "libs/jquery/jquery.rating" )}

    ## grid container
    <div id="grid-container"></div>

    ## load javascript
    <script type="text/javascript">
        var gridView = null;
        function add_tag_to_grid_filter( tag_name, tag_value ){
            // Put tag name and value together.
            var tag = tag_name + ( tag_value !== undefined && tag_value !== "" ? ":" + tag_value : "" );
            var advanced_search = $( '#advanced-search').is(":visible" );
            if( !advanced_search ){
                $('#standard-search').slideToggle('fast');
                $('#advanced-search').slideToggle('fast');
            }
            gridView.add_filter_condition( "tags", tag );
        };

        // load grid viewer
        require(['mvc/grid/grid-view'], function(GridView) {
            $(function() {
                gridView = new GridView( ${ h.dumps( self.get_grid_config( embedded=embedded, insert=insert ) ) } );
            });
        });
    </script>
</%def>

<%def name="get_grid_config( embedded=False, insert=None )">
## generates dictionary
<%
    self.grid_config = {
        'title'                         : grid.title,
        'url_base'                      : trans.request.path_url,
        'async'                         : grid.use_async,
        'async_ops'                     : [],
        'categorical_filters'           : {},
        'filters'                       : cur_filter_dict,
        'sort_key'                      : sort_key,
        'show_item_checkboxes'          : context.get('show_item_checkboxes', False),
        'cur_page_num'                  : cur_page_num,
        'num_pages'                     : num_pages,
        'num_page_links'                : num_page_links,
        'history_tag_autocomplete_url'  : url( controller='tag', action='tag_autocomplete_data', item_class='History' ),
        'history_name_autocomplete_url' : url( controller='history', action='name_autocomplete_data' ),
        'status'                        : status,
        'message'                       : util.restore_text(message),
        'global_actions'                : [],
        'operations'                    : [],
        'items'                         : [],
        'columns'                       : [],
        'get_class_plural'              : get_class_plural( grid.model_class ).lower(),
        'use_paging'                    : grid.use_paging,
        'legend'                        : grid.legend,
        'current_item_id'               : False,
        'use_panels'                    : context.get('use_panels'),
        'use_hide_message'              : grid.use_hide_message,
        'insert'                        : insert,
        'default_filter_dict'           : default_filter_dict,
        'advanced_search'               : advanced_search,
        'refresh_frames'                : [],
        'embedded'                      : embedded,
        'info_text'                     : grid.info_text,
        'url'                           : url(dict())
    }

    ## add refresh frames
    if refresh_frames:
        self.grid_config['refresh_frames'] = refresh_frames

    ## add current item if exists
    if current_item:
        self.grid_config['current_item_id'] = current_item.id
    endif

    ## column
    for column in grid.columns:

        ## add column sort links
        href = None
        extra = ''
        if column.sortable:
            if sort_key.endswith(column.key):
                if not sort_key.startswith("-"):
                    href = url( sort=( "-" + column.key ) )
                    extra = "&darr;"
                else:
                    href = url( sort=( column.key ) )
                    extra = "&uarr;"
            else:
                href = url( sort=column.key )

        ## add to configuration
        self.grid_config['columns'].append({
            'key'               : column.key,
            'visible'           : column.visible,
            'nowrap'            : column.nowrap,
            'attach_popup'      : column.attach_popup,
            'label_id_prefix'   : column.label_id_prefix,
            'sortable'          : column.sortable,
            'label'             : column.label,
            'filterable'        : column.filterable,
            'is_text'           : isinstance(column, TextColumn),
            'href'              : href,
            'extra'             : extra
        })
    endfor

    ## operations
    for operation in grid.operations:
        self.grid_config['operations'].append({
            'allow_multiple'        : operation.allow_multiple,
            'allow_popup'           : operation.allow_popup,
            'target'                : operation.target,
            'label'                 : operation.label,
            'confirm'               : operation.confirm,
            'inbound'               : operation.inbound,
            'global_operation'      : False
        })
        if operation.allow_multiple:
            self.grid_config['show_item_checkboxes'] = True

        if operation.global_operation:
            self.grid_config['global_operation'] = url( ** (operation.global_operation()) )
    endfor

    ## global actions
    for action in grid.global_actions:
        self.grid_config['global_actions'].append({
            'url_args'  : url(**action.url_args),
            'label'     : action.label,
            'inbound'   : action.inbound
        })
    endfor

    ## Operations that are async (AJAX) compatible.
    for operation in [op for op in grid.operations if op.async_compatible]:
        self.grid_config['async_ops'].append(operation.label.lower());
    endfor

    ## Filter values for categorical filters.
    for column in grid.columns:
        if column.filterable is not None and not isinstance( column, TextColumn ):
            self.grid_config['categorical_filters'][column.key] = dict([ (filter.label, filter.args) for filter in column.get_accepted_filters() ])
        endif
    endfor

    # items
    for i, item in enumerate( query ):
        item_dict = {
            'id'                    : item.id,
            'encode_id'             : trans.security.encode_id(item.id),
            'link'                  : [],
            'operation_config'      : {},
            'column_config'         : {}
        }

        ## data columns
        for column in grid.columns:
            if column.visible:
                ## get link
                link = column.get_link(trans, grid, item)
                if link:
                    link = url(**link)
                else:
                    link = None
                endif

                ## inbound
                inbound = column.inbound

                ## get value
                value = column.get_value( trans, grid, item )

                # Handle non-ascii chars.
                if isinstance(value, str):
                    value = unicode(value, 'utf-8')
                    value = value.replace('/', '//')
                endif

                ## Item dictionary
                item_dict['column_config'][column.label] = {
                    'link'      : link,
                    'value'     : value,
                    'inbound'   : inbound
                }
            endif
        endfor
        ## add operation details to item
        for operation in grid.operations:
            item_dict['operation_config'][operation.label] = {
                'allowed'   : operation.allowed(item),
                'url_args'  : url( **operation.get_url_args( item ) )
            }
        endfor

        ## add item to list
        self.grid_config['items'].append(item_dict)
    endfor

    return self.grid_config
%>
</%def>

