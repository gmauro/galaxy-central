<%inherit file="/webapps/galaxy/base_panels.mako"/>

<%def name="late_javascripts()">
    ${parent.late_javascripts()}
    <script type="text/javascript">
    // Set up GalaxyAsync object.
    var galaxy_async = new GalaxyAsync();
    galaxy_async.set_func_url(galaxy_async.set_user_pref, "${h.url_for( controller='user', action='set_user_pref_async' )}");
    
    $(function(){
        // Init history options.
        $("#history-options-button").css( "position", "relative" );
        make_popupmenu( $("#history-options-button"), {
            "History Lists": null,
            "Saved Histories": function() {
                galaxy_main.location = "${h.url_for( controller='history', action='list')}";
            },
            "Histories Shared with Me": function() {
                galaxy_main.location = "${h.url_for( controller='history', action='list_shared')}";
            },
            "Current History": null,
            "Create New": function() {
                galaxy_history.location = "${h.url_for( controller='root', action='history_new' )}";
            },
            "Clone": function() {
                galaxy_main.location = "${h.url_for( controller='history', action='clone')}";
            },
            "Share or Publish": function() {
                galaxy_main.location = "${h.url_for( controller='history', action='sharing' )}";
            },
            "Extract Workflow": function() {
                galaxy_main.location = "${h.url_for( controller='workflow', action='build_from_current_history' )}";
            },
            "Dataset Security": function() {
                galaxy_main.location = "${h.url_for( controller='root', action='history_set_default_permissions' )}";
            },
            "Show Deleted Datasets": function() {
                galaxy_history.location = "${h.url_for( controller='root', action='history', show_deleted=True)}";
            },
            "Show Hidden Datasets": function() {
                galaxy_history.location = "${h.url_for( controller='root', action='history', show_hidden=True)}";
            },
            "Show structure": function() {
                galaxy_main.location = "${h.url_for( controller='history', action='display_structured' )}";
            },
            "Export to File": function() {
                galaxy_main.location = "${h.url_for( controller='history', action='export_archive' )}";
            },
            "Delete": function()
            {
                if ( confirm( "Really delete the current history?" ) )
                {
                    galaxy_main.location = "${h.url_for( controller='history', action='delete_current' )}";
                }
            },
            ##"Other Actions": null,
            ##"Import from File": function() {
            ##    galaxy_main.location = "${h.url_for( controller='history', action='import_archive' )}";
            ##}
        });
        
        // Init tool options.
        make_popupmenu( $("#tools-options-button"), {
            ## Search tools menu item.
            %if trans.app.toolbox_search.enabled:
                <% 
                    show_tool_search = False
                    if trans.user:
                        show_tool_search = trans.user.preferences.get( "show_tool_search", "False" )
                        
                    if show_tool_search == "True":
                        initial_text = "Hide Search"
                    else:
                        initial_text = "Search Tools"
                %>
                "${initial_text}": function() {
                    // Show/hide menu and update vars, user preferences.
                    var menu = $("#galaxy_tools").contents().find('#tool-search');
                    if (menu.is(":visible"))
                    {
                        // Hide menu.
                        pref_value = "False";
                        menu_option_text = "Search Tools";
                        menu.toggle();
                        
                        // Reset search.
                        reset_tool_search(true);
                    }
                    else
                    {
                        // Show menu.
                        pref_value = "True";
                        menu_option_text = "Hide Search";
                        menu.toggle();
                    }
            
                    // Update menu option.
                    $("#tools-options-button-menu").find("li").eq(0).text(menu_option_text);
            
                    galaxy_async.set_user_pref("show_tool_search", pref_value);
                },
            %endif
            ## Recently used tools menu.
            %if trans.user:
                <%
                    if trans.user.preferences.get( 'show_recently_used_menu', 'False' ) == 'True':
                        action = "Hide"
                    else:
                        action = "Show"
                %>
                "${action} Recently Used": function() {
                    // Show/hide menu.
                    var ru_menu = $('#galaxy_tools').contents().find('#recently_used_wrapper');
                    var ru_menu_body = ru_menu.find(".toolSectionBody");
                    var pref_value = null;
                    var menu_option_text = null;
                    if (ru_menu.hasClass("user_pref_visible"))
                    {
                        // Hide menu.
                        ru_menu_body.slideUp();
                        ru_menu.slideUp();
                        
                        // Set vars used below and in tool menu frame.
                        pref_value = "False";
                        menu_option_text = "Show Recently Used";
                    }
                    else
                    {
                        // "Show" menu.
                        if (!$('#galaxy_tools').contents().find('#tool-search-query').hasClass("search_active"))
                            // Default.
                            ru_menu.slideDown();
                        else
                            // Search active: tf there are matching tools in RU menu, show menu.
                            if ( ru_menu.find(".toolTitle.search_match").length != 0 )
                            {
                                ru_menu.slideDown();
                                ru_menu_body.slideDown();
                            }
                        
                        // Set vars used below and in tool menu frame.
                        pref_value = "True";
                        menu_option_text = "Hide Recently Used";
                    }
                 
                    // Update menu class and option.
                    ru_menu.toggleClass("user_pref_hidden user_pref_visible");
                    $("#tools-options-button-menu").find("li").eq(1).text(menu_option_text);

                    galaxy_async.set_user_pref("show_recently_used_menu", pref_value);
                }
            %endif
        });
    });
    </script>
</%def>

<%def name="init()">
<%
	if trans.app.config.cloud_controller_instance:
		self.has_left_panel=False
		self.has_right_panel=False
		self.active_view="cloud"
	else:
		self.has_left_panel=True
		self.has_right_panel=True
		self.active_view="analysis"
%>
%if trans.app.config.require_login and not trans.user:
    <script type="text/javascript">
        if ( window != top ) {
            top.location.href = location.href;
        }
    </script>
%endif
</%def>

<%def name="left_panel()">
    <div class="unified-panel-header" unselectable="on">
        <div class='unified-panel-header-inner'>
            <div style="float: right">
                <a class='panel-header-button popup' id="tools-options-button" href="#">${_('Options')}</a>
            </div>
            ${n_('Tools')}
        </div>
    </div>
    <div class="unified-panel-body" style="overflow: hidden;">
        <iframe name="galaxy_tools" id="galaxy_tools" src="${h.url_for( controller='root', action='tool_menu' )}" frameborder="0" style="position: absolute; margin: 0; border: 0 none; height: 100%; width: 100%;"> </iframe>
    </div>
</%def>

<%def name="center_panel()">

    ## If a specific tool id was specified, load it in the middle frame
    <%
    if trans.app.config.require_login and not trans.user:
        center_url = h.url_for( controller='user', action='login' )
    elif tool_id is not None:
        center_url = h.url_for( 'tool_runner', tool_id=tool_id, from_noframe=True )
    elif workflow_id is not None:
        center_url = h.url_for( controller='workflow', action='run', id=workflow_id )
    elif m_c is not None:
        center_url = h.url_for( controller=m_c, action=m_a )
    elif trans.app.config.cloud_controller_instance:
    	center_url = h.url_for( controller='cloud', action='list' )
    else:
        center_url = h.url_for( '/static/welcome.html' )
    %>
    
    <iframe name="galaxy_main" id="galaxy_main" frameborder="0" style="position: absolute; width: 100%; height: 100%;" src="${center_url}"> </iframe>

</%def>

<%def name="right_panel()">
    <div class="unified-panel-header" unselectable="on">
        <div class="unified-panel-header-inner">
            <div style="float: right">
                <a id="history-options-button" class='panel-header-button popup' href="${h.url_for( controller='root', action='history_options' )}" target="galaxy_main">${_('Options')}</a>
            </div>
            <div class="panel-header-text">${_('History')}</div>
        </div>
    </div>
    <div class="unified-panel-body" style="overflow: hidden;">
        <iframe name="galaxy_history" width="100%" height="100%" frameborder="0" style="position: absolute; margin: 0; border: 0 none; height: 100%;" src="${h.url_for( controller='root', action='history' )}"></iframe>
    </div>
</%def>
