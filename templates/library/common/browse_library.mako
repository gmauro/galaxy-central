<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/library/common/library_item_info.mako" import="render_library_item_info" />
<%namespace file="/library/common/common.mako" import="render_actions_on_multiple_items" />

<%!
   def inherit(context):
       if context.get('use_panels'):
           return '/webapps/galaxy/base_panels.mako'
       else:
           return '/base.mako'
%>
<%inherit file="${inherit(context)}"/>

<%def name="init()">
<%
   self.has_left_panel=False
   self.has_right_panel=False
   self.message_box_visible=False
   self.active_view="user"
   self.overlay_visible=False
%>
</%def>

##
## Override methods from base.mako and base_panels.mako
##
<%def name="center_panel()">
   <div style="overflow: auto; height: 100%;">
       <div class="page-container" style="padding: 10px;">
           ${render_content()}
       </div>
   </div>
</%def>

## Render the grid's basic elements. Each of these elements can be subclassed.
<%def name="body()">
   ${render_content()}
</%def>

<%def name="title()">Browse data library</%def>
<%def name="stylesheets()">
   ${parent.stylesheets()}
   ${h.css( "library" )}
</%def>

<%def name="javascripts()">
  ${parent.javascripts()}
  ${self.grid_javascripts()}
</%def>

<%def name="grid_javascripts()">
   <script type="text/javascript">
       $( document ).ready( function () {
           $("#library-grid").each( function() {
              // Recursively fill in children and descendents of each row
              var process_row = function( q, parents ) {
                   // Find my index
                   var index = $(q).parent().children().index( $(q) );
                   // Find my immediate children
                   var children = $(q).siblings().filter( "[parent='" + index + "']" );
                   // Recursively handle them
                   var descendents = children;
                   children.each( function() {
                       child_descendents = process_row( $(this), parents.add( q ) );
                       descendents = descendents.add( child_descendents );
                   });
                   // Set up expand / hide link
                   // HACK: assume descendents are invisible. The caller actually
                   //       ensures this for the root node. However, if we start
                   //       remembering folder states, we'll need something
                   //       more sophisticated here.
                   var visible = false;
                   $(q).find( "span.expandLink").click( function() {
                       if ( visible ) {
                           descendents.hide();
                           descendents.removeClass( "expanded" );
                           q.removeClass( "expanded" );
                           visible = false;
                       } else {
                           children.show();
                           q.addClass( "expanded" );
                           visible = true;
                       }
                   });
                   // Check/uncheck boxes in subfolders.
                   q.children( "td" ).children( "input[type=checkbox]" ).click( function() {
                       if ( $(this).is(":checked") ) {
                           descendents.find( "input[type=checkbox]").attr( 'checked', true );
                       } else {
                           descendents.find( "input[type=checkbox]").attr( 'checked', false );
                           // If you uncheck a lower level checkbox, uncheck the boxes above it
                           // (since deselecting a child means the parent is not fully selected any
                           // more).
                           parents.children( "td" ).children( "input[type=checkbox]" ).attr( "checked", false );
                       }
                   });
                   // return descendents for use by parent
                   return descendents;
              }
              $(this).find( "tbody tr" ).not( "[parent]").each( function() {
                   descendents = process_row( $(this), $([]) );
                   descendents.hide();
              });
           });
       });
       function checkForm() {
           if ( $("select#action_on_datasets_select option:selected").text() == "delete" ) {
               if ( confirm( "Click OK to delete these datasets?" ) ) {
                   return true;
               } else {
                   return false;
               }
           }
       }
       // Looks for changes in dataset state using an async request. Keeps
       // calling itself (via setTimeout) until all datasets are in a terminal
       // state.
       var updater = function ( tracked_datasets ) {
           // Check if there are any items left to track
           var empty = true;
           for ( i in tracked_datasets ) {
               empty = false;
               break;
           }
           if ( ! empty ) {
               setTimeout( function() { updater_callback( tracked_datasets ) }, 3000 );
           }
       };
       var updater_callback = function ( tracked_datasets ) {
           // Build request data
           var ids = []
           var states = []
           $.each( tracked_datasets, function ( id, state ) {
               ids.push( id );
               states.push( state );
           });
           // Make ajax call
           $.ajax( {
               type: "POST",
               url: "${h.url_for( controller='library_common', action='library_item_updates' )}",
               dataType: "json",
               data: { ids: ids.join( "," ), states: states.join( "," ) },
               success : function ( data ) {
                   $.each( data, function( id, val ) {
                       // Replace HTML
                       var cell = $("#libraryItem-" + id).find("#libraryItemInfo");
                       cell.html( val.html );
                       // If new state was terminal, stop tracking
                       if (( val.state == "ok") || ( val.state == "error") || ( val.state == "empty") || ( val.state == "deleted" ) || ( val.state == "discarded" )) {
                           delete tracked_datasets[ parseInt(id) ];
                       } else {
                           tracked_datasets[ parseInt(id) ] = val.state;
                       }
                   });
                   updater( tracked_datasets ); 
               },
               error: function() {
                   // Just retry, like the old method, should try to be smarter
                   updater( tracked_datasets );
               }
           });
       };
   </script>
</%def>

<%def name="render_dataset( cntrller, ldda, library_dataset, selected, library, folder, pad, parent, row_counter, tracked_datasets, show_deleted=False )">
    <%
        ## The received ldda must always be a LibraryDatasetDatasetAssociation object.  The object id passed to methods
        ## from the drop down menu should be the ldda id to prevent id collision ( which could happen when displaying
        ## children, which are always lddas ).  We also need to make sure we're displaying the latest version of this
        ## library_dataset, so we display the attributes from the ldda.

        from galaxy.web.controllers.library_common import active_folders, active_folders_and_lddas, activatable_folders_and_lddas, branch_deleted

        if ldda.user:
            uploaded_by = ldda.user.email
        else:
            uploaded_by = 'anonymous'
        if ldda == library_dataset.library_dataset_dataset_association:
            current_version = True
            if trans.user_is_admin() and cntrller == 'library_admin':
                can_modify = can_manage = True
            elif cntrller in [ 'library', 'requests' ]:
                can_modify = trans.app.security_agent.can_modify_library_item( current_user_roles, library_dataset )
                can_manage = trans.app.security_agent.can_manage_library_item( current_user_roles, library_dataset )
            else:
                can_modify = can_manage = False
        else:
            current_version = False
        if current_version and ldda.state not in ( 'ok', 'error', 'empty', 'deleted', 'discarded' ):
            tracked_datasets[ldda.id] = ldda.state
        info_association, inherited = ldda.get_info_association( restrict=True )
    %>
    %if current_version and ( not ldda.library_dataset.deleted or show_deleted ):
        <tr class="datasetRow"
            %if parent is not None:
                parent="${parent}"
            %endif
            id="libraryItem-${ldda.id}">
            <td style="padding-left: ${pad+20}px;">
                %if selected:
                    <input type="checkbox" name="ldda_ids" value="${trans.security.encode_id( ldda.id )}" checked/>
                %else:
                    <input type="checkbox" name="ldda_ids" value="${trans.security.encode_id( ldda.id )}"/>
                %endif
                %if ldda.library_dataset.deleted:
                   <span class="libraryItem-error">
               %endif
               <a href="${h.url_for( controller='library_common', action='ldda_info', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}"><b>${ldda.name[:50]}</b></a>
               %if ldda.library_dataset.deleted:
                   </span>
               %endif
               %if not library.deleted:
                   <a id="dataset-${ldda.id}-popup" class="popup-arrow" style="display: none;">&#9660;</a>
                   <div popupmenu="dataset-${ldda.id}-popup">
                       %if not branch_deleted( folder ) and not ldda.library_dataset.deleted and ( cntrller == 'library_admin' or can_modify ):
                           <a class="action-button" href="${h.url_for( controller='library_common', action='ldda_edit_info', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit information</a>
                       %else:
                           <a class="action-button" href="${h.url_for( controller='library_common', action='ldda_info', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}">View information</a>
                       %endif
                       %if not branch_deleted( folder ) and not ldda.library_dataset.deleted and ( ( cntrller == 'library_admin' or can_modify ) and not info_association ):
                           <a class="action-button" href="${h.url_for( controller='library_common', action='add_template', cntrller=cntrller, item_type='ldda', library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), ldda_id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}">Add template</a>
                       %endif
                       %if not branch_deleted( folder ) and not ldda.library_dataset.deleted and ( ( cntrller == 'library_admin' or can_modify ) and info_association ):
                           <a class="action-button" href="${h.url_for( controller='library_common', action='edit_template', cntrller=cntrller, item_type='ldda', library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), ldda_id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit template</a>
                           <a class="action-button" href="${h.url_for( controller='library_common', action='delete_template', cntrller=cntrller, item_type='ldda', library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), ldda_id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}">Delete template</a>
                       %endif
                       %if not branch_deleted( folder ) and not ldda.library_dataset.deleted and ( cntrller == 'library_admin' or can_manage ):
                           <a class="action-button" href="${h.url_for( controller='library_common', action='ldda_permissions', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), id=trans.security.encode_id( ldda.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit permissions</a>
                       %endif
                       %if not branch_deleted( folder ) and not ldda.library_dataset.deleted and ( cntrller == 'library_admin' or can_modify ):
                           <a class="action-button" href="${h.url_for( controller='library_common', action='upload_library_dataset', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), replace_id=trans.security.encode_id( library_dataset.id ), show_deleted=show_deleted )}">Upload a new version of this dataset</a>
                       %endif
                       %if not branch_deleted( folder ) and not ldda.library_dataset.deleted and ldda.has_data:
                           <a class="action-button" href="${h.url_for( controller='library_common', action='act_on_multiple_datasets', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), ldda_ids=trans.security.encode_id( ldda.id ), do_action='import_to_history', use_panels=use_panels, show_deleted=show_deleted )}">Import this dataset into your current history</a>
                           <a class="action-button" href="${h.url_for( controller='library_common', action='download_dataset_from_folder', cntrller=cntrller, id=trans.security.encode_id( ldda.id ), library_id=trans.security.encode_id( library.id ), use_panels=use_panels )}">Download this dataset</a>
                       %endif
                       %if can_modify:
                           %if not library.deleted and not branch_deleted( folder ) and not ldda.library_dataset.deleted:
                               <a class="action-button" confirm="Click OK to delete dataset '${ldda.name}'." href="${h.url_for( controller='library_common', action='delete_library_item', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), item_id=trans.security.encode_id( library_dataset.id ), item_type='library_dataset', show_deleted=show_deleted )}">Delete this dataset</a>
                           %elif not library.deleted and not branch_deleted( folder ) and not ldda.library_dataset.purged and ldda.library_dataset.deleted:
                               <a class="action-button" href="${h.url_for( controller='library_common', action='undelete_library_item', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), item_id=trans.security.encode_id( library_dataset.id ), item_type='library_dataset', show_deleted=show_deleted )}">Undelete this dataset</a>
                           %endif
                       %endif
                   </div>
               %endif
            </td>
            <td id="libraryItemInfo">${render_library_item_info( ldda )}</td>
            <td>${uploaded_by}</td>
            <td>${ldda.create_time.strftime( "%Y-%m-%d" )}</td>
            <td>${ldda.get_size( nice_size=True )}</td>
        </tr>
        <%
            my_row = row_counter.count
            row_counter.increment()
        %>
    %endif
</%def>

<%def name="render_folder( cntrller, folder, folder_pad, created_ldda_ids, library, hidden_folder_ids, tracked_datasets, show_deleted=False, parent=None, row_counter=None, root_folder=False )">
   <%
       from galaxy.web.controllers.library_common import active_folders, active_folders_and_lddas, activatable_folders_and_lddas, branch_deleted

       if root_folder:
           pad = folder_pad
           expander = "/static/images/silk/resultset_bottom.png"
           folder_img = "/static/images/silk/folder_page.png"
       else:
           pad = folder_pad + 20
           expander = "/static/images/silk/resultset_next.png"
           folder_img = "/static/images/silk/folder.png"
       if created_ldda_ids:
           created_ldda_ids = util.listify( created_ldda_ids )
       if str( folder.id ) in hidden_folder_ids:
           return ""
       my_row = None
       if trans.user_is_admin() and cntrller == 'library_admin':
           can_add = can_modify = can_manage = True
       elif cntrller in [ 'library', 'requests' ]:
           can_access, folder_ids = trans.app.security_agent.check_folder_contents( trans.user, current_user_roles, folder )
           if not can_access:
               can_show, folder_ids = \
                   trans.app.security_agent.show_library_item( trans.user,
                                                               current_user_roles,
                                                               folder,
                                                               [ trans.app.security_agent.permitted_actions.LIBRARY_ADD,
                                                                 trans.app.security_agent.permitted_actions.LIBRARY_MODIFY,
                                                                 trans.app.security_agent.permitted_actions.LIBRARY_MANAGE ] )
               if not can_show:
                   return ""
           can_add = trans.app.security_agent.can_add_library_item( current_user_roles, folder )
           can_modify = trans.app.security_agent.can_modify_library_item( current_user_roles, folder )
           can_manage = trans.app.security_agent.can_manage_library_item( current_user_roles, folder )
       else:
           can_add = can_modify = can_manage = False
       info_association, inherited = folder.get_info_association( restrict=True )
   %>
   %if not root_folder and ( not folder.deleted or show_deleted ):
       <tr class="folderRow libraryOrFolderRow"
           %if parent is not None:
               parent="${parent}"
               style="display: none;"
           %endif

           <td style="padding-left: ${folder_pad}px;">
               <span class="expandLink"></span>
               <input type="checkbox" class="folderCheckbox"/>
               <span class="rowIcon"></span>
               %if folder.deleted:
                   <span class="libraryItem-error">
               %endif
               <div class="menubutton split" id="folder_img-${folder.id}-popup">
                   <a href="${h.url_for( controller='library_common', action='folder_info', cntrller=cntrller, use_panels=use_panels, id=trans.security.encode_id( folder.id ), library_id=trans.security.encode_id( library.id ), show_deleted=show_deleted )}">${folder.name}</a>
               </div>
               %if folder.description:
                   <i>- ${folder.description}</i>
               %endif
               %if folder.deleted:
                   </span>
               %endif
               %if not branch_deleted( folder ) and ( can_add or can_modify or can_manage ):
                   %if not library.deleted:
                       <div popupmenu="folder_img-${folder.id}-popup">
                           %if not branch_deleted( folder ) and can_add:
                               <a class="action-button" href="${h.url_for( controller='library_common', action='upload_library_dataset', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), use_panels=use_panels, show_deleted=show_deleted )}">Add datasets</a>
                               <a class="action-button" href="${h.url_for( controller='library_common', action='create_folder', cntrller=cntrller, parent_id=trans.security.encode_id( folder.id ), library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Add sub-folder</a>
                           %endif
                           %if not branch_deleted( folder ) and can_modify:
                               <a class="action-button" href="${h.url_for( controller='library_common', action='folder_info', cntrller=cntrller, id=trans.security.encode_id( folder.id ), library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit information</a>
                           %endif
                           %if not branch_deleted( folder ) and ( can_modify and not info_association ):
                               <a class="action-button" href="${h.url_for( controller='library_common', action='add_template', cntrller=cntrller, item_type='folder', library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), use_panels=use_panels, show_deleted=show_deleted )}">Add template</a>
                           %endif
                           %if not branch_deleted( folder ) and ( can_modify and info_association ):
                               <a class="action-button" href="${h.url_for( controller='library_common', action='edit_template', cntrller=cntrller, item_type='folder', library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit template</a>
                               <a class="action-button" href="${h.url_for( controller='library_common', action='delete_template', cntrller=cntrller, item_type='folder', library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( folder.id ), use_panels=use_panels, show_deleted=show_deleted )}">Delete template</a>
                           %endif
                           %if not branch_deleted( folder ) and can_manage:
                               <a class="action-button" href="${h.url_for( controller='library_common', action='folder_permissions', cntrller=cntrller, id=trans.security.encode_id( folder.id ), library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit permissions</a>
                           %endif
                           %if can_modify:
                               %if not library.deleted and not folder.deleted:
                                   <a class="action-button" confirm="Click OK to delete the folder '${folder.name}.'" href="${h.url_for( controller='library_common', action='delete_library_item', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), item_id=trans.security.encode_id( folder.id ), item_type='folder', show_deleted=show_deleted )}">Delete this folder</a>
                               %elif not library.deleted and folder.deleted and not folder.purged:
                                   <a class="action-button" href="${h.url_for( controller='library_common', action='undelete_library_item', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), item_id=trans.security.encode_id( folder.id ), item_type='folder', show_deleted=show_deleted )}">Undelete this folder</a>
                               %endif
                           %endif
                       </div>
                   %endif
               %endif
           </div>
           <td colspan="5"></td>
       </tr>
       <%
           my_row = row_counter.count
           row_counter.increment()
       %>
   %endif
   %if cntrller == 'library':
       <% sub_folders = active_folders( trans, folder ) %>
       %for sub_folder in sub_folders:
           ${render_folder( cntrller, sub_folder, pad, created_ldda_ids, library, hidden_folder_ids, tracked_datasets, show_deleted=show_deleted, parent=my_row, row_counter=row_counter, root_folder=False )}
       %endfor
       %for library_dataset in folder.active_library_datasets:
           <%
               ldda = library_dataset.library_dataset_dataset_association
               can_access = trans.app.security_agent.can_access_dataset( current_user_roles, ldda.dataset )
               selected = created_ldda_ids and str( ldda.id ) in created_ldda_ids
           %>
           %if can_access:
               ${render_dataset( cntrller, ldda, library_dataset, selected, library, folder, pad, my_row, row_counter, tracked_datasets, show_deleted=show_deleted )}
           %endif
       %endfor
   %elif trans.user_is_admin() and cntrller == 'library_admin':
       <%
           if show_deleted:
               sub_folders, lddas = activatable_folders_and_lddas( trans, folder )
           else:
               sub_folders, lddas = active_folders_and_lddas( trans, folder )
       %>
       %for sub_folder in sub_folders:
           ${render_folder( cntrller, sub_folder, pad, created_ldda_ids, library, [], tracked_datasets, show_deleted=show_deleted, parent=my_row, row_counter=row_counter, root_folder=False )}
       %endfor 
       %for ldda in lddas:
           <%
               library_dataset = ldda.library_dataset
               selected = created_ldda_ids and str( ldda.id ) in created_ldda_ids
           %>
           ${render_dataset( cntrller, ldda, library_dataset, selected, library, folder, pad, my_row, row_counter, tracked_datasets, show_deleted=show_deleted )}
       %endfor
   %endif
</%def>

<%def name="render_content()">
   <%
       from galaxy import util
       from galaxy.web.controllers.library_common import branch_deleted
       from time import strftime

       if trans.user_is_admin() and cntrller == 'library_admin':
           can_add = can_modify = can_manage = True
       elif cntrller in [ 'library', 'requests' ]:
           can_add = trans.app.security_agent.can_add_library_item( current_user_roles, library )
           can_modify = trans.app.security_agent.can_modify_library_item( current_user_roles, library )
           can_manage = trans.app.security_agent.can_manage_library_item( current_user_roles, library )
       else:
           can_add = can_modify = can_manage = False
       info_association, inherited = library.get_info_association()

       tracked_datasets = {}

       class RowCounter( object ):
           def __init__( self ):
               self.count = 0
           def increment( self ):
               self.count += 1
           def __str__( self ):
               return str( self.count )
   %>

   <h2>Data Library &ldquo;${library.name}&rdquo;</h2>

    <ul class="manage-table-actions">
        %if not library.deleted and ( ( trans.user_is_admin() and cntrller == 'requests_admin' ) or can_add ):
            <li><a class="action-button" href="${h.url_for( controller='library_common', action='upload_library_dataset', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), folder_id=trans.security.encode_id( library.root_folder.id ), use_panels=use_panels, show_deleted=show_deleted )}"><span>Add datasets</span></a></li>
            <li><a class="action-button" href="${h.url_for( controller='library_common', action='create_folder', cntrller=cntrller, parent_id=trans.security.encode_id( library.root_folder.id ), library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Add folder</a></li>
        %endif
        <li><a class="action-button" id="library-${library.id}-popup" class="menubutton">Library Actions</a></li>
        <div popupmenu="library-${library.id}-popup">
            %if not library.deleted:
                %if can_modify:
                    <a class="action-button" href="${h.url_for( controller='library_common', action='library_info', cntrller=cntrller, id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit information</a>
                    <a class="action-button" confirm="Click OK to delete the library named '${library.name}'." href="${h.url_for( controller='library_common', action='delete_library_item', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), item_id=trans.security.encode_id( library.id ), item_type='library' )}">Delete this data library</a>
                    %if show_deleted:
                        <a class="action-button" href="${h.url_for( controller='library_common', action='browse_library', cntrller=cntrller, id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=False )}">Hide deleted items</a>
                    %else:
                        <a class="action-button" href="${h.url_for( controller='library_common', action='browse_library', cntrller=cntrller, id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=True )}">Show deleted items</a>
                    %endif
                %endif
                %if can_modify and not library.info_association:
                    <a class="action-button" href="${h.url_for( controller='library_common', action='add_template', cntrller=cntrller, item_type='library', library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Add template</a>
                %endif
                %if can_modify and info_association:
                    <a class="action-button" href="${h.url_for( controller='library_common', action='edit_template', cntrller=cntrller, item_type='library', library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit template</a>
                    <a class="action-button" href="${h.url_for( controller='library_common', action='delete_template', cntrller=cntrller, item_type='library', library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Delete template</a>
                %endif
                %if can_manage:
                    <a class="action-button" href="${h.url_for( controller='library_common', action='library_permissions', cntrller=cntrller, id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">Edit permissions</a>
                %endif
            %elif can_modify and not library.purged:
                <a class="action-button" href="${h.url_for( controller='library_common', action='undelete_library_item', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), item_id=trans.security.encode_id( library.id ), item_type='library', use_panels=use_panels )}">Undelete this data library</a>
            %elif library.purged:
                <a class="action-button" href="${h.url_for( controller='library_common', action='browse_library', cntrller=cntrller, id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}">This data library has been purged</a>
            %endif
        </div>
   </ul>

   %if message:
       ${render_msg( message, status )}
   %endif

   %if library.synopsis not in [ 'None', None ]:
       <div class="libraryItemBody">
           ${library.synopsis}
       </div>
       <br/>
   %endif

   <form name="act_on_multiple_datasets" action="${h.url_for( controller='library_common', action='act_on_multiple_datasets', cntrller=cntrller, library_id=trans.security.encode_id( library.id ), use_panels=use_panels, show_deleted=show_deleted )}" onSubmit="javascript:return checkForm();" method="post">
       <table cellspacing="0" cellpadding="0" border="0" width="100%" class="grid" id="library-grid">
           <thead>
               <tr class="libraryTitle">
                   <th>Name</th>        
                   <th>Information</th>
                   <th>Uploaded By</th>
                   <th>Date</th>
                   <th>File Size</th>
               </thead>
           </tr>
           <% row_counter = RowCounter() %>
           %if cntrller in [ 'library', 'requests' ]:
               ${self.render_folder( 'library', library.root_folder, 0, created_ldda_ids, library, hidden_folder_ids, tracked_datasets, show_deleted=show_deleted, parent=None, row_counter=row_counter, root_folder=True )}
               %if not library.deleted:
                   ${render_actions_on_multiple_items()}
               %endif
           %elif ( trans.user_is_admin() and cntrller in [ 'library_admin', 'requests_admin' ] ):
               ${self.render_folder( 'library_admin', library.root_folder, 0, created_ldda_ids, library, [], tracked_datasets, show_deleted=show_deleted, parent=None, row_counter=row_counter, root_folder=True )}
               %if not library.deleted and not show_deleted:
                   ${render_actions_on_multiple_items()}
               %endif
           %endif
       </table>
   </form>

   %if tracked_datasets:
       <script type="text/javascript">
           // Updater
           updater({${ ",".join( [ '"%s" : "%s"' % ( k, v ) for k, v in tracked_datasets.iteritems() ] ) }});
       </script>
       <!-- running: do not change this comment, used by TwillTestCase.library_wait -->
   %endif

   ## Help about compression types

   <div class="libraryItemBody">
       <p class="infomark">
           TIP: You can download individual library files by selecting "Download this dataset" from the context menu (triangle) next to the dataset's name.
       </p>
   </div>
   %if len( comptypes ) > 1:
       <div class="libraryItemBody">
           <p class="infomark">
               TIP: Multiple compression options are available for downloading library datasets:
           </p>
           <ul style="padding-left: 1em; list-style-type: disc;">
               %if 'gz' in comptypes:
                   <li>gzip: Compression is fastest and yields a larger file, making it more suitable for fast network connections.
                       %if trans.app.config.upstream_gzip:
                           NOTE: The file you receive will be an uncompressed .tar file - this is because the Galaxy server compresses it and your browser decompresses it on the fly.
                       %endif
                   </li>
               %endif
               %if 'bz2' in comptypes:
                   <li>bzip2: Compression takes the most time but is better for slower network connections (that transfer slower than the rate of compression) since the resulting file size is smallest.</li>
               %endif
               %if 'zip' in comptypes:
                   <li>ZIP: Not recommended but is provided as an option for those on Windows without WinZip (since WinZip can read .bz2 and .gz files).</li>
               %endif
           </ul>
       </div>
   %endif
</%def>
