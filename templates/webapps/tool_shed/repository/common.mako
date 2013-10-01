<%def name="common_javascripts(repository)">
    <script type="text/javascript">
        $(function(){
            $("#tree").ajaxComplete(function(event, XMLHttpRequest, ajaxOptions) {
                _log("debug", "ajaxComplete: %o", this); // dom element listening
            });
            // --- Initialize sample trees
            $("#tree").dynatree({
                title: "${repository.name}",
                rootVisible: true,
                minExpandLevel: 0, // 1: root node is not collapsible
                persist: false,
                checkbox: true,
                selectMode: 3,
                onPostInit: function(isReloading, isError) {
                    //alert("reloading: "+isReloading+", error:"+isError);
                    logMsg("onPostInit(%o, %o) - %o", isReloading, isError, this);
                    // Re-fire onActivate, so the text is updated
                    this.reactivate();
                }, 
                fx: { height: "toggle", duration: 200 },
                // initAjax is hard to fake, so we pass the children as object array:
                initAjax: {url: "${h.url_for( controller='repository', action='open_folder' )}",
                           dataType: "json", 
                           data: { folder_path: "${repository.repo_path( trans.app )}" },
                },
                onLazyRead: function(dtnode){
                    dtnode.appendAjax({
                        url: "${h.url_for( controller='repository', action='open_folder' )}", 
                        dataType: "json",
                        data: { folder_path: dtnode.data.key },
                    });
                },
                onSelect: function(select, dtnode) {
                    // Display list of selected nodes
                    var selNodes = dtnode.tree.getSelectedNodes();
                    // convert to title/key array
                    var selKeys = $.map(selNodes, function(node) {
                        return node.data.key;
                    });
                    if (document.forms["select_files_to_delete"]) {
                        // The following is used only ~/templates/webapps/tool_shed/repository/browse_repository.mako.
                        document.select_files_to_delete.selected_files_to_delete.value = selKeys.join(",");
                    }
                    // The following is used only in ~/templates/webapps/tool_shed/repository/upload.mako.
                    if (document.forms["upload_form"]) {
                        document.upload_form.upload_point.value = selKeys.slice(-1);
                    }
                },
                onActivate: function(dtnode) {
                    var cell = $("#file_contents");
                    var selected_value;
                     if (dtnode.data.key == 'root') {
                        selected_value = "${repository.repo_path( trans.app )}/";
                    } else {
                        selected_value = dtnode.data.key;
                    };
                    if (selected_value.charAt(selected_value.length-1) != '/') {
                        // Make ajax call
                        $.ajax( {
                            type: "POST",
                            url: "${h.url_for( controller='repository', action='get_file_contents' )}",
                            dataType: "json",
                            data: { file_path: selected_value },
                            success : function ( data ) {
                                cell.html( '<label>'+data+'</label>' )
                            }
                        });
                    } else {
                        cell.html( '' );
                    };
                },
            });
        });
    </script>
</%def>

<%def name="container_javascripts()">
    <script type="text/javascript">
        var init_dependencies = function() {
            var storage_id = "library-expand-state-${trans.security.encode_id(10000)}";
            var restore_folder_state = function() {
                var state = $.jStorage.get(storage_id);
                if (state) {
                    for (var id in state) {
                        if (state[id] === true) {
                            var row = $("#" + id),
                                index = row.parent().children().index(row);
                            row.addClass("expanded").show();
                            row.siblings().filter("tr[parent='" + index + "']").show();
                        }
                    }
                }
            };
            var save_folder_state = function() {
                var state = {};
                $("tr.folderRow").each( function() {
                    var folder = $(this);
                    state[folder.attr("id")] = folder.hasClass("expanded");
                });
                $.jStorage.set(storage_id, state);
            };
            $(".container-table").each(function() {
                //var container_id = this.id.split( "-" )[0];
                //alert( container_id );
                var child_of_parent_cache = {};
                // Recursively fill in children and descendants of each row
                var process_row = function(q, parents) {
                    // Find my index
                    var parent = q.parent(),
                        this_level = child_of_parent_cache[parent] || (child_of_parent_cache[parent] = parent.children());
                    var index = this_level.index(q);
                    // Find my immediate children
                    var children = $(par_child_dict[index]);
                    // Recursively handle them
                    var descendants = children;
                    children.each( function() {
                        child_descendants = process_row( $(this), parents.add(q) );
                        descendants = descendants.add(child_descendants);
                    });
                    // Set up expand / hide link
                    var expand_fn = function() {
                        if ( q.hasClass("expanded") ) {
                            descendants.hide();
                            descendants.removeClass("expanded");
                            q.removeClass("expanded");
                        } else {
                            children.show();
                            q.addClass("expanded");
                        }
                        save_folder_state();
                    };
                    $("." + q.attr("id") + "-click").click(expand_fn);
                    // return descendants for use by parent
                    return descendants;
                }
                // Initialize dict[parent_id] = rows_which_have_that_parent_id_as_parent_attr
                var par_child_dict = {},
                    no_parent = [];
                $(this).find("tbody tr").each( function() {
                    if ( $(this).attr("parent")) {
                        var parent = $(this).attr("parent");
                        if (par_child_dict[parent] !== undefined) {
                            par_child_dict[parent].push(this);
                        } else {
                            par_child_dict[parent] = [this];
                        }
                    } else {
                        no_parent.push(this);
                    }                        
                });
                $(no_parent).each( function() {
                    descendants = process_row( $(this), $([]) );
                    descendants.hide();
               });
            });
            restore_folder_state();
        };
        $(function() {
            init_dependencies();
        });
    </script>
</%def>

<%def name="render_repository_type_select_field( repository_type_select_field, render_help=True )">
    <div class="form-row">
        <label>Repository type:</label>
        <%
            from tool_shed.repository_types import util
            options = repository_type_select_field.options
            repository_types = []
            for option_tup in options:
                repository_types.append( option_tup[ 1 ] )
            render_as_text = len( options ) == 1
            if render_as_text:
                repository_type = options[ 0 ][ 0 ]
        %>
        %if render_as_text:
            ${repository_type | h}
            %if render_help:
                <div class="toolParamHelp" style="clear: both;">
                    This repository's type cannot be changed because its contents are valid only for its current type or it has been cloned.
                </div>
            %endif
        %else:
            ${repository_type_select_field.get_html()}
            %if render_help:
                <div class="toolParamHelp" style="clear: both;">
                    Select the repository type based on the following criteria.
                    <ul>
                        %if util.UNRESTRICTED in repository_types:
                            <li><b>Unrestricted</b> - contents can be any set of valid Galaxy utilities or files
                        %endif
                        %if util.TOOL_DEPENDENCY_DEFINITION in repository_types:
                            <li><b>Tool dependency definition</b> - contents will always be restricted to one file named tool_dependencies.xml
                        %endif
                    </ul>
                </div>
            %endif
        %endif
        <div style="clear: both"></div>
    </div>
</%def>         
            
<%def name="render_sharable_str( repository, changeset_revision=None )">
    <%
        from tool_shed.util.shed_util_common import generate_sharable_link_for_repository_in_tool_shed
        sharable_link = generate_sharable_link_for_repository_in_tool_shed( trans, repository, changeset_revision=changeset_revision )
    %>
    ${sharable_link}
</%def>

<%def name="render_clone_str( repository )">
    <%
        from tool_shed.util.shed_util_common import generate_clone_url_for_repository_in_tool_shed
        clone_str = generate_clone_url_for_repository_in_tool_shed( trans, repository )
    %>
    hg clone <a href="${clone_str}">${clone_str}</a>
</%def>

<%def name="render_folder( folder, folder_pad, parent=None, row_counter=None, is_root_folder=False, render_repository_actions_for='tool_shed' )">
    <%
        encoded_id = trans.security.encode_id( folder.id )
        
        if is_root_folder:
            pad = folder_pad
            expander = h.url_for("/static/images/silk/resultset_bottom.png")
            folder_img = h.url_for("/static/images/silk/folder_page.png")
        else:
            pad = folder_pad + 20
            expander = h.url_for("/static/images/silk/resultset_next.png")
            folder_img = h.url_for("/static/images/silk/folder.png")
        my_row = None
    %>
    %if not is_root_folder:
        <%
            if parent is None:
                bg_str = 'bgcolor="#D8D8D8"'
            else:
                bg_str = ''
        %>
        <tr id="folder-${encoded_id}" ${bg_str} class="folderRow libraryOrFolderRow"
            %if parent is not None:
                parent="${parent}"
                style="display: none;"
            %endif
            >
            <%
                col_span_str = ''
                folder_label = str( folder.label )
                if folder.datatypes:
                    col_span_str = 'colspan="4"'
                elif folder.label == 'Missing tool dependencies':
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    else:
                        folder_label = "%s<i> - repository tools require handling of these missing dependencies</i>" % folder_label
                    col_span_str = 'colspan="5"'
                elif folder.label in [ 'Installed repository dependencies', 'Repository dependencies', 'Missing repository dependencies' ]:
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    elif folder.label not in [ 'Installed repository dependencies' ] and folder.parent.label not in [ 'Installation errors' ]:
                        folder_label = "%s<i> - installation of these additional repositories is required</i>" % folder_label
                    if trans.webapp.name == 'galaxy':
                        col_span_str = 'colspan="4"'
                elif folder.label == 'Installation errors':
                    folder_label = "%s<i> - no functional tests were run for any tools in this changeset revision</i>" % folder_label
                elif folder.label == 'Invalid repository dependencies':
                    folder_label = "%s<i> - click the repository dependency to see why it is invalid</i>" % folder_label
                elif folder.label == 'Invalid tool dependencies':
                    folder_label = "%s<i> - click the tool dependency to see why it is invalid</i>" % folder_label
                elif folder.label == 'Valid tools':
                    col_span_str = 'colspan="3"'
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    else:
                        folder_label = "%s<i> - click the name to preview the tool and use the pop-up menu to inspect all metadata</i>" % folder_label
                elif folder.invalid_tools:
                    if trans.webapp.name == 'tool_shed':
                        folder_label = "%s<i> - click the tool config file name to see why the tool is invalid</i>" % folder_label
                elif folder.tool_dependencies:
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    else:
                        folder_label = "%s<i> - repository tools require handling of these dependencies</i>" % folder_label
                    col_span_str = 'colspan="4"'
                elif folder.workflows:
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    else:
                        folder_label = "%s<i> - click the name to view an SVG image of the workflow</i>" % folder_label
                    col_span_str = 'colspan="4"'
                elif folder.valid_data_managers:
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    col_span_str = 'colspan="3"'
                elif folder.invalid_data_managers:
                    if folder.description:
                        folder_label = "%s<i> - %s</i>" % ( folder_label, folder.description )
                    col_span_str = 'colspan="2"'
            %>
            <td ${col_span_str} style="padding-left: ${folder_pad}px;">
                <span class="expandLink folder-${encoded_id}-click">
                    <div style="float: left; margin-left: 2px;" class="expandLink folder-${encoded_id}-click">
                        <a class="folder-${encoded_id}-click" href="javascript:void(0);">
                            ${folder_label}
                        </a>
                    </div>
                </span>
            </td>
        </tr>
        <%
            my_row = row_counter.count
            row_counter.increment()  
        %>
    %endif
    %for sub_folder in folder.folders:
        ${render_folder( sub_folder, pad, parent=my_row, row_counter=row_counter, is_root_folder=False, render_repository_actions_for=render_repository_actions_for )}
    %endfor
    %for readme in folder.readme_files:
        ${render_readme( readme, pad, my_row, row_counter )}
    %endfor
    %for invalid_repository_dependency in folder.invalid_repository_dependencies:
        ${render_invalid_repository_dependency( invalid_repository_dependency, pad, my_row, row_counter )}
    %endfor
    %for index, repository_dependency in enumerate( folder.repository_dependencies ):
        <% row_is_header = index == 0 %>
        ${render_repository_dependency( repository_dependency, pad, my_row, row_counter, row_is_header )}
    %endfor
    %for invalid_tool_dependency in folder.invalid_tool_dependencies:
        ${render_invalid_tool_dependency( invalid_tool_dependency, pad, my_row, row_counter )}
    %endfor
    %for index, tool_dependency in enumerate( folder.tool_dependencies ):
        <% row_is_header = index == 0 %>
        ${render_tool_dependency( tool_dependency, pad, my_row, row_counter, row_is_header )}
    %endfor
    %if folder.valid_tools:
        %for index, tool in enumerate( folder.valid_tools ):
            <% row_is_header = index == 0 %>
            ${render_tool( tool, pad, my_row, row_counter, row_is_header, render_repository_actions_for=render_repository_actions_for )}
        %endfor
    %endif
    %for invalid_tool in folder.invalid_tools:
        ${render_invalid_tool( invalid_tool, pad, my_row, row_counter, render_repository_actions_for=render_repository_actions_for )}
    %endfor
    %if folder.workflows:
        %for index, workflow in enumerate( folder.workflows ):
            <% row_is_header = index == 0 %>
            ${render_workflow( workflow, pad, my_row, row_counter, row_is_header, render_repository_actions_for=render_repository_actions_for )}
        %endfor
    %endif
    %if folder.datatypes:
        %for index, datatype in enumerate( folder.datatypes ):
            <% row_is_header = index == 0 %>
            ${render_datatype( datatype, pad, my_row, row_counter, row_is_header )}
        %endfor
    %endif
    %if folder.valid_data_managers:
        %for index, data_manager in enumerate( folder.valid_data_managers ):
            <% row_is_header = index == 0 %>
            ${render_valid_data_manager( data_manager, pad, my_row, row_counter, row_is_header )}
        %endfor
    %endif
    %if folder.invalid_data_managers:
        %for index, data_manager in enumerate( folder.invalid_data_managers ):
            <% row_is_header = index == 0 %>
            ${render_invalid_data_manager( data_manager, pad, my_row, row_counter, row_is_header )}
        %endfor
    %endif
    %if folder.test_environments:
        %for test_environment in folder.test_environments:
            ${render_test_environment( test_environment, pad, my_row, row_counter )}
        %endfor
    %endif
    %if folder.failed_tests:
        %for failed_test in folder.failed_tests:
            ${render_failed_test( failed_test, pad, my_row, row_counter )}
        %endfor
    %endif
    %if folder.not_tested:
        %for not_tested in folder.not_tested:
            ${render_not_tested( not_tested, pad, my_row, row_counter )}
        %endfor
    %endif
    %if folder.passed_tests:
        %for passed_test in folder.passed_tests:
            ${render_passed_test( passed_test, pad, my_row, row_counter )}
        %endfor
    %endif
    %if folder.missing_test_components:
        %for missing_test_component in folder.missing_test_components:
            ${render_missing_test_component( missing_test_component, pad, my_row, row_counter )}
        %endfor
    %endif
    %if folder.installation_errors:
        %for installation_error in folder.installation_errors:
            ${render_folder( installation_error, pad, my_row, row_counter )}
        %endfor
    %endif
    %if folder.tool_dependency_installation_errors:
        %for tool_dependency_installation_error in folder.tool_dependency_installation_errors:
            ${render_tool_dependency_installation_error( tool_dependency_installation_error, pad, my_row, row_counter )}
        %endfor
    %endif 
    %if folder.repository_installation_errors:
        %for repository_installation_error in folder.repository_installation_errors:
            ${render_repository_installation_error( repository_installation_error, pad, my_row, row_counter, is_current_repository=False )}
        %endfor
    %endif 
    %if folder.current_repository_installation_errors:
        %for repository_installation_error in folder.current_repository_installation_errors:
            ${render_repository_installation_error( repository_installation_error, pad, my_row, row_counter, is_current_repository=True )}
        %endfor
    %endif 
</%def>

<%def name="render_datatype( datatype, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( datatype.id )
        if row_is_header:
            cell_type = 'th'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rd-${encoded_id}">
        <${cell_type} style="padding-left: ${pad+20}px;">${datatype.extension | h}</${cell_type}>
        <${cell_type}>${datatype.type | h}</${cell_type}>
        <${cell_type}>${datatype.mimetype | h}</${cell_type}>
        <${cell_type}>${datatype.subclass | h}</${cell_type}>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_failed_test( failed_test, pad, parent, row_counter, row_is_header=False )">
    <% 
        from tool_shed.util.shed_util_common import to_html_string
        encoded_id = trans.security.encode_id( failed_test.id )
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rft-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="test_environment">
                <tr><td bgcolor="#FFFFCC"><b>Tool id:</b> ${failed_test.tool_id | h}</td></tr>
                <tr><td><b>Tool version:</b> ${failed_test.tool_id | h}</td></tr>
                <tr><td><b>Test:</b> ${failed_test.test_id | h}</td></tr>
                <tr><td><b>Stderr:</b> <br/>${ to_html_string( failed_test.stderr ) }</td></tr>
                <tr><td><b>Traceback:</b> <br/>${ to_html_string( failed_test.traceback ) }</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_invalid_data_manager( data_manager, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( data_manager.id )
        if row_is_header:
            cell_type = 'th'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-ridm-${encoded_id}">
        <${cell_type} style="padding-left: ${pad+20}px;">${data_manager.index | h}</${cell_type}>
        <${cell_type}>${data_manager.error | h}</${cell_type}>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_invalid_repository_dependency( invalid_repository_dependency, pad, parent, row_counter )">
    <%
        encoded_id = trans.security.encode_id( invalid_repository_dependency.id )
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rird-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            ${ invalid_repository_dependency.error | h }
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_invalid_tool( invalid_tool, pad, parent, row_counter, valid=True, render_repository_actions_for='tool_shed' )">
    <% encoded_id = trans.security.encode_id( invalid_tool.id ) %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rit-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            %if trans.webapp.name == 'tool_shed' and invalid_tool.repository_id and invalid_tool.tool_config and invalid_tool.changeset_revision:
                <a class="view-info" href="${h.url_for( controller='repository', action='load_invalid_tool', repository_id=trans.security.encode_id( invalid_tool.repository_id ), tool_config=invalid_tool.tool_config, changeset_revision=invalid_tool.changeset_revision, render_repository_actions_for=render_repository_actions_for )}">
                    ${invalid_tool.tool_config | h}
                </a>
            %else:
                ${invalid_tool.tool_config | h}
            %endif
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_invalid_tool_dependency( invalid_tool_dependency, pad, parent, row_counter )">
    <%
        encoded_id = trans.security.encode_id( invalid_tool_dependency.id )
    %>
    <style type="text/css">
        #invalid_td_table{ table-layout:fixed;
                           width:100%;
                           overflow-wrap:normal;
                           overflow:hidden;
                           border:0px; 
                           word-break:keep-all;
                           word-wrap:break-word;
                           line-break:strict; }
    </style>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-ritd-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="invalid_td_table">
                <tr><td>${ invalid_tool_dependency.error | h }</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_missing_test_component( missing_test_component, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( missing_test_component.id )
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rmtc-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="test_environment">
                <tr><td bgcolor="#FFFFCC"><b>Tool id:</b> ${missing_test_component.tool_id | h}</td></tr>
                <tr><td><b>Tool version:</b> ${missing_test_component.tool_version | h}</td></tr>
                <tr><td><b>Tool guid:</b> ${missing_test_component.tool_guid | h}</td></tr>
                <tr><td><b>Missing components:</b> <br/>${missing_test_component.missing_components | h}</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_readme( readme, pad, parent, row_counter )">
    <%
        from tool_shed.util.shed_util_common import to_html_string
        from galaxy.util import rst_to_html
        encoded_id = trans.security.encode_id( readme.id )
        render_rst = readme.name.endswith( '.rst' )
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}" 
        %endif
        id="libraryItem-rr-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="readme_files">
                %if render_rst:
                    <tr><td>${ rst_to_html( readme.text ) }</td></tr>
                %else:
                    <tr><td>${ to_html_string( readme.text ) }</td></tr>
                %endif
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_repository_dependency( repository_dependency, pad, parent, row_counter, row_is_header=False )">
                
    <%
        from galaxy.util import asbool
        encoded_id = trans.security.encode_id( repository_dependency.id )
        if trans.webapp.name == 'galaxy':
            if repository_dependency.tool_shed_repository_id:
                encoded_required_repository_id = trans.security.encode_id( repository_dependency.tool_shed_repository_id )
            else:
                encoded_required_repository_id = None
            if repository_dependency.installation_status:
                installation_status = str( repository_dependency.installation_status )
            else:
                installation_status = None
        repository_name = str( repository_dependency.repository_name )
        repository_owner = str( repository_dependency.repository_owner )
        changeset_revision = str( repository_dependency.changeset_revision )
        if asbool( str( repository_dependency.prior_installation_required ) ):
            prior_installation_required_str = " <i>(prior install required)</i>"
        else:
            prior_installation_required_str = ""

        if trans.webapp.name == 'galaxy':
            if row_is_header:
                cell_type = 'th'
            else:
                cell_type = 'td'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rrd-${encoded_id}">
        %if trans.webapp.name == 'galaxy':
            <${cell_type} style="padding-left: ${pad+20}px;">
                %if row_is_header:
                    ${repository_name | h}
                %elif encoded_required_repository_id:
                    <a class="action-button" href="${h.url_for( controller='admin_toolshed', action='manage_repository', id=encoded_required_repository_id )}">${repository_name | h}</a>
                %else:
                   ${repository_name | h} 
                %endif
            </${cell_type}>
            <${cell_type}>
                ${changeset_revision | h}
            </${cell_type}>
            <${cell_type}>
                ${repository_owner | h}
            </${cell_type}>
            <${cell_type}>
                ${installation_status}
            </${cell_type}>
        %else:
            <td style="padding-left: ${pad+20}px;">
                Repository <b>${repository_name | h}</b> revision <b>${changeset_revision | h}</b> owned by <b>${repository_owner | h}</b>${prior_installation_required_str}
            </td>
        %endif
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_table_wrap_style( table_id )">
    <style type="text/css">
        table.${table_id}{ table-layout:fixed;
                           width:100%;
                           overflow-wrap:normal;
                           overflow:hidden;
                           border:0px; 
                           word-break:keep-all;
                           word-wrap:break-word;
                           line-break:strict; }
    </style>
</%def>

<%def name="render_tool_dependency_installation_error( installation_error, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( installation_error.id )
    %>
    ${render_table_wrap_style( "td_install_error_table" )}
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rtdie-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="td_install_error_table">
                <tr bgcolor="#FFFFCC">
                    <th>Type</th><th>Name</th><th>Version</th>
                </tr>
                <tr>
                    <td>${installation_error.name | h}</td>
                    <td>${installation_error.type | h}</td>
                    <td>${installation_error.version | h}</td>
                </tr>
                <tr><th>Error</th></tr>
                <tr><td colspan="3">${installation_error.error_message | h}</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_repository_installation_error( installation_error, pad, parent, row_counter, row_is_header=False, is_current_repository=False )">
    <%
        encoded_id = trans.security.encode_id( installation_error.id )
    %>
    ${render_table_wrap_style( "rd_install_error_table" )}
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rrie-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="rd_install_error_table">
                %if not is_current_repository:
                    <tr bgcolor="#FFFFCC">
                        <th>Tool shed</th><th>Name</th><th>Owner</th><th>Changeset revision</th>
                    </tr>
                    <tr>
                        <td>${installation_error.tool_shed | h}</td>
                        <td>${installation_error.name | h}</td>
                        <td>${installation_error.owner | h}</td>
                        <td>${installation_error.changeset_revision | h}</td>
                    </tr>
                %endif
                <tr><th>Error</th></tr>
                <tr><td colspan="4">${installation_error.error_message | h}</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_not_tested( not_tested, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( not_tested.id )
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rnt-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="test_environment">
                <tr><td>${not_tested.reason | h}</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_passed_test( passed_test, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( passed_test.id )
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rpt-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table id="test_environment">
                <tr><td bgcolor="#FFFFCC"><b>Tool id:</b> ${passed_test.tool_id | h}</td></tr>
                <tr><td><b>Tool version:</b> ${passed_test.tool_id | h}</td></tr>
                <tr><td><b>Test:</b> ${passed_test.test_id | h}</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_tool( tool, pad, parent, row_counter, row_is_header, render_repository_actions_for='tool_shed' )">
    <%
        encoded_id = trans.security.encode_id( tool.id )
        if row_is_header:
            cell_type = 'th'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rt-${encoded_id}">
        %if row_is_header:
            <th style="padding-left: ${pad+20}px;">${tool.name | h}</th>
        %else:
            <td style="padding-left: ${pad+20}px;">
                %if tool.repository_id:
                    %if trans.webapp.name == 'tool_shed':
                        <div style="float:left;" class="menubutton split popup" id="tool-${encoded_id}-popup">
                            <a class="view-info" href="${h.url_for( controller='repository', action='display_tool', repository_id=trans.security.encode_id( tool.repository_id ), tool_config=tool.tool_config, changeset_revision=tool.changeset_revision, render_repository_actions_for=render_repository_actions_for )}">${tool.name | h}</a>
                        </div>
                        <div popupmenu="tool-${encoded_id}-popup">
                            <a class="action-button" href="${h.url_for( controller='repository', action='view_tool_metadata', repository_id=trans.security.encode_id( tool.repository_id ), changeset_revision=tool.changeset_revision, tool_id=tool.tool_id, render_repository_actions_for=render_repository_actions_for )}">View tool metadata</a>
                        </div>
                    %else:
                        %if tool.repository_installation_status == trans.model.ToolShedRepository.installation_status.INSTALLED:
                            <a class="action-button" href="${h.url_for( controller='admin_toolshed', action='view_tool_metadata', repository_id=trans.security.encode_id( tool.repository_id ), changeset_revision=tool.changeset_revision, tool_id=tool.tool_id )}">${tool.name | h}</a>
                        %else:
                            ${tool.name | h}
                        %endif
                    %endif
                %else:
                    ${tool.name | h}
                %endif
            </td>
        %endif
        <${cell_type}>${tool.description | h}</${cell_type}>
        <${cell_type}>${tool.version | h}</${cell_type}>
        ##<${cell_type}>${tool.requirements | h}</${cell_type}>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_tool_dependency( tool_dependency, pad, parent, row_counter, row_is_header )">
    <%
        from galaxy.util import string_as_bool
        encoded_id = trans.security.encode_id( tool_dependency.id )
        is_missing = tool_dependency.installation_status not in [ 'Installed' ]
        if row_is_header:
            cell_type = 'th'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rtd-${encoded_id}">
        <${cell_type} style="padding-left: ${pad+20}px;">
            %if row_is_header:
                ${tool_dependency.name | h}
            %elif trans.webapp.name == 'galaxy' and tool_dependency.tool_dependency_id:
                %if tool_dependency.repository_id and tool_dependency.installation_status in [ trans.model.ToolDependency.installation_status.INSTALLED ]:
                    <a class="action-button" href="${h.url_for( controller='admin_toolshed', action='browse_tool_dependency', id=trans.security.encode_id( tool_dependency.tool_dependency_id ) )}">
                        ${tool_dependency.name | h}
                    </a>
                %elif tool_dependency.installation_status not in [ trans.model.ToolDependency.installation_status.UNINSTALLED ]:
                    <a class="action-button" href="${h.url_for( controller='admin_toolshed', action='manage_repository_tool_dependencies', tool_dependency_ids=trans.security.encode_id( tool_dependency.tool_dependency_id ) )}">
                        ${tool_dependency.name}
                    </a>
                %else:
                    ${tool_dependency.name | h}
                %endif
            %else:
                ${tool_dependency.name | h}
            %endif
        </${cell_type}>
        <${cell_type}>
            <%
                if tool_dependency.version:
                    version_str = tool_dependency.version
                else:
                    version_str = ''
            %>
            ${version_str | h}
        </${cell_type}>
        <${cell_type}>${tool_dependency.type | h}</${cell_type}>
        <${cell_type}>
            %if trans.webapp.name == 'galaxy':
                ${tool_dependency.installation_status | h}
            %else:
                %if row_is_header:
                    ${tool_dependency.is_orphan | h}
                %else:
                    <%
                        if string_as_bool( str( tool_dependency.is_orphan ) ):
                            is_orphan = 'yes'
                        else:
                            is_orphan = 'no'
                    %>
                    ${is_orphan | h}
                %endif
            %endif
        </${cell_type}>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_test_environment( test_environment, pad, parent, row_counter, row_is_header=False )">
    <% encoded_id = trans.security.encode_id( test_environment.id ) %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rte-${encoded_id}">
        <td style="padding-left: ${pad+20}px;">
            <table class="grid" id="test_environment">
                <tr><td><b>Time tested:</b> ${test_environment.time_last_tested | h}</td></tr>
                <tr><td><b>System:</b> ${test_environment.system | h}</td></tr>
                <tr><td><b>Architecture:</b> ${test_environment.architecture | h}</td></tr>
                <tr><td><b>Python version:</b> ${test_environment.python_version | h}</td></tr>
                <tr><td><b>Galaxy revision:</b> ${test_environment.galaxy_revision | h}</td></tr>
                <tr><td><b>Galaxy database version:</b> ${test_environment.galaxy_database_version | h}</td></tr>
                <tr><td><b>Tool shed revision:</b> ${test_environment.tool_shed_revision | h}</td></tr>
                <tr><td><b>Tool shed database version:</b> ${test_environment.tool_shed_database_version | h}</td></tr>
                <tr><td><b>Tool shed mercurial version:</b> ${test_environment.tool_shed_mercurial_version | h}</td></tr>
            </table>
        </td>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_valid_data_manager( data_manager, pad, parent, row_counter, row_is_header=False )">
    <%
        encoded_id = trans.security.encode_id( data_manager.id )
        if row_is_header:
            cell_type = 'th'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rvdm-${encoded_id}">
        <${cell_type} style="padding-left: ${pad+20}px;">${data_manager.name | h}</${cell_type}>
        <${cell_type}>${data_manager.version | h}</${cell_type}>
        <${cell_type}>${data_manager.data_tables | h}</${cell_type}>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_workflow( workflow, pad, parent, row_counter, row_is_header=False, render_repository_actions_for='tool_shed' )">
    <%
        from tool_shed.util.encoding_util import tool_shed_encode
        encoded_id = trans.security.encode_id( workflow.id )
        encoded_workflow_name = tool_shed_encode( workflow.workflow_name )
        if trans.webapp.name == 'tool_shed':
            encoded_repository_metadata_id = trans.security.encode_id( workflow.repository_metadata_id )
            encoded_repository_id = None
        else:
            encoded_repository_metadata_id = None
            encoded_repository_id = trans.security.encode_id( workflow.repository_id )
        if row_is_header:
            cell_type = 'th'
        else:
            cell_type = 'td'
    %>
    <tr class="datasetRow"
        %if parent is not None:
            parent="${parent}"
        %endif
        id="libraryItem-rw-${encoded_id}">
        <${cell_type} style="padding-left: ${pad+20}px;">
            %if row_is_header:
                ${workflow.workflow_name | h}
            %elif trans.webapp.name == 'tool_shed' and encoded_repository_metadata_id:
                <a href="${h.url_for( controller='repository', action='view_workflow', workflow_name=encoded_workflow_name, repository_metadata_id=encoded_repository_metadata_id, render_repository_actions_for=render_repository_actions_for )}">${workflow.workflow_name | h}</a>
            %elif trans.webapp.name == 'galaxy' and encoded_repository_id:
                <a href="${h.url_for( controller='admin_toolshed', action='view_workflow', workflow_name=encoded_workflow_name, repository_id=encoded_repository_id )}">${workflow.workflow_name | h}</a>
            %else:
                ${workflow.workflow_name | h}
            %endif
        </${cell_type}>
        <${cell_type}>${workflow.steps | h}</${cell_type}>
        <${cell_type}>${workflow.format_version | h}</${cell_type}>
        <${cell_type}>${workflow.annotation | h}</${cell_type}>
    </tr>
    <%
        my_row = row_counter.count
        row_counter.increment()
    %>
</%def>

<%def name="render_repository_items( metadata, containers_dict, can_set_metadata=False, render_repository_actions_for='tool_shed' )">
    <%
        from tool_shed.util.encoding_util import tool_shed_encode

        has_datatypes = metadata and 'datatypes' in metadata
        has_readme_files = metadata and 'readme_files' in metadata
        has_workflows = metadata and 'workflows' in metadata
        
        datatypes_root_folder = containers_dict.get( 'datatypes', None )
        invalid_data_managers_root_folder = containers_dict.get( 'invalid_data_managers', None )
        invalid_repository_dependencies_root_folder = containers_dict.get( 'invalid_repository_dependencies', None )
        invalid_tool_dependencies_root_folder = containers_dict.get( 'invalid_tool_dependencies', None )
        invalid_tools_root_folder = containers_dict.get( 'invalid_tools', None )
        missing_repository_dependencies_root_folder = containers_dict.get( 'missing_repository_dependencies', None )
        missing_tool_dependencies_root_folder = containers_dict.get( 'missing_tool_dependencies', None )
        readme_files_root_folder = containers_dict.get( 'readme_files', None )
        repository_dependencies_root_folder = containers_dict.get( 'repository_dependencies', None )
        test_environment_root_folder = containers_dict.get( 'test_environment', None )
        tool_dependencies_root_folder = containers_dict.get( 'tool_dependencies', None )
        tool_test_results_root_folder = containers_dict.get( 'tool_test_results', None )
        valid_data_managers_root_folder = containers_dict.get( 'valid_data_managers', None )
        valid_tools_root_folder = containers_dict.get( 'valid_tools', None )
        workflows_root_folder = containers_dict.get( 'workflows', None )
        
        has_contents = datatypes_root_folder or invalid_tools_root_folder or valid_tools_root_folder or workflows_root_folder
        has_dependencies = \
            invalid_repository_dependencies_root_folder or \
            invalid_tool_dependencies_root_folder or \
            missing_repository_dependencies_root_folder or \
            repository_dependencies_root_folder or \
            tool_dependencies_root_folder or \
            missing_tool_dependencies_root_folder

        class RowCounter( object ):
            def __init__( self ):
                self.count = 0
            def increment( self ):
                self.count += 1
            def __str__( self ):
                return str( self.count )
    %>
    %if readme_files_root_folder:
        ${render_table_wrap_style( "readme_files" )}
        <p/>
        <div class="toolForm">
            <div class="toolFormTitle">Repository README files - may contain important installation or license information</div>
            <div class="toolFormBody">
                <p/>
                <% row_counter = RowCounter() %>
                <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="readme_files">
                    ${render_folder( readme_files_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                </table>
            </div>
        </div>
    %endif
    %if has_dependencies:
        <div class="toolForm">
            <div class="toolFormTitle">Dependencies of this repository</div>
            <div class="toolFormBody">
                %if invalid_repository_dependencies_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="invalid_repository_dependencies">
                        ${render_folder( invalid_repository_dependencies_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if missing_repository_dependencies_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="missing_repository_dependencies">
                        ${render_folder( missing_repository_dependencies_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if repository_dependencies_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="repository_dependencies">
                        ${render_folder( repository_dependencies_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if invalid_tool_dependencies_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="invalid_tool_dependencies">
                        ${render_folder( invalid_tool_dependencies_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if tool_dependencies_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="tool_dependencies">
                        ${render_folder( tool_dependencies_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if missing_tool_dependencies_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="missing_tool_dependencies">
                        ${render_folder( missing_tool_dependencies_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
            </div>
        </div>
    %endif
    %if has_contents:
        <p/>
        <div class="toolForm">
            <div class="toolFormTitle">Contents of this repository</div>
            <div class="toolFormBody">
                %if valid_tools_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="valid_tools">
                        ${render_folder( valid_tools_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True, render_repository_actions_for=render_repository_actions_for )}
                    </table>
                %endif
                %if invalid_tools_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="invalid_tools">
                        ${render_folder( invalid_tools_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True, render_repository_actions_for=render_repository_actions_for )}
                    </table>
                %endif
                %if valid_data_managers_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="valid_data_managers">
                        ${render_folder( valid_data_managers_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if invalid_data_managers_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="invalid_data_managers">
                        ${render_folder( invalid_data_managers_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
                %if workflows_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="workflows">
                        ${render_folder( workflows_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True, render_repository_actions_for=render_repository_actions_for )}
                    </table>
                %endif
                %if datatypes_root_folder:
                    <p/>
                    <% row_counter = RowCounter() %>
                    <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="datatypes">
                        ${render_folder( datatypes_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                    </table>
                %endif
            </div>
        </div>
    %endif
    %if tool_test_results_root_folder:
        ##${render_table_wrap_style( "failed_test_table" )}
        ##${render_table_wrap_style( "missing_table" )}
        ##${render_table_wrap_style( "not_tested_table" )}
        ##${render_table_wrap_style( "passed_tests_table" )}
        ${render_table_wrap_style( "test_environment" )}
        <p/>
        <div class="toolForm">
            <div class="toolFormTitle">Automated tool test results</div>
            <div class="toolFormBody">
                <p/>
                <% row_counter = RowCounter() %>
                <table cellspacing="2" cellpadding="2" border="0" width="100%" class="tables container-table" id="test_environment">
                    ${render_folder( tool_test_results_root_folder, 0, parent=None, row_counter=row_counter, is_root_folder=True )}
                </table>
            </div>
        </div>
    %endif
</%def>
