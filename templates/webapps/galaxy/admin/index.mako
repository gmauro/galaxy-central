<%inherit file="/webapps/galaxy/base_panels.mako"/>

## Default title
<%def name="title()">Galaxy Administration</%def>

<%def name="stylesheets()">
    ${parent.stylesheets()}    
    ## TODO: Clean up these styles and move into panel_layout.css (they are
    ## used here and in the editor).
    <style type="text/css">
    #left {
        background: #C1C9E5 url(${h.url_for('/static/style/menu_bg.png')}) top repeat-x;
    }
    div.toolMenu {
        margin: 5px;
        margin-left: 10px;
        margin-right: 10px;
    }
    div.toolSectionPad {
        margin: 0;
        padding: 0;
        height: 5px;
        font-size: 0px;
    }
    div.toolSectionDetailsInner { 
        margin-left: 5px;
        margin-right: 5px;
    }
    div.toolSectionTitle {
        padding-bottom: 0px;
        font-weight: bold;
    }
    div.toolMenuGroupHeader {
        font-weight: bold;
        padding-top: 0.5em;
        padding-bottom: 0.5em;
        color: #333;
        font-style: italic;
        border-bottom: dotted #333 1px;
        margin-bottom: 0.5em;
    }    
    div.toolTitle {
        padding-top: 5px;
        padding-bottom: 5px;
        margin-left: 16px;
        margin-right: 10px;
        display: list-item;
        list-style: square outside;
    }
    a:link, a:visited, a:active
    {
        color: #303030;
    }
    </style>
</%def>

<%def name="init()">
<%
    self.has_left_panel=True
    self.has_right_panel=False
    self.active_view="admin"
%>
</%def>

<%def name="left_panel()">
    <div class="unified-panel-header" unselectable="on">
        <div class='unified-panel-header-inner'>Administration</div>
    </div>
    <div class="unified-panel-body" style="overflow: auto;">
        <div class="toolMenu">
            <div class="toolSectionList">
                <div class="toolSectionTitle">
                  <span>Security</span>
                </div>
                <div class="toolSectionBody">
                  <div class="toolSectionBg">
                    <div class="toolTitle"><a href="${h.url_for( controller='admin', action='users', webapp=webapp )}" target="galaxy_main">Manage users</a></div>
                    <div class="toolTitle"><a href="${h.url_for( controller='admin', action='groups', webapp=webapp )}" target="galaxy_main">Manage groups</a></div>
                    <div class="toolTitle"><a href="${h.url_for( controller='admin', action='roles', webapp=webapp )}" target="galaxy_main">Manage roles</a></div>
                  </div>
                </div>
                <div class="toolSectionPad"></div>
                <div class="toolSectionTitle">
                  <span>Data</span>
                </div>
                <div class="toolSectionBody">
                  <div class="toolSectionBg">
                    <div class="toolTitle"><a href="${h.url_for( controller='library_admin', action='browse_libraries' )}" target="galaxy_main">Manage data libraries</a></div>
                  </div>
                </div>
                <div class="toolSectionPad"></div>
                <div class="toolSectionTitle">
                  <span>Server</span>
                </div>
                <div class="toolSectionBody">
                  <div class="toolSectionBg">
                    <div class="toolTitle"><a href="${h.url_for( controller='admin', action='reload_tool' )}" target="galaxy_main">Reload a tool's configuration</a></div>
                    <div class="toolTitle"><a href="${h.url_for( controller='admin', action='memdump' )}" target="galaxy_main">Profile memory usage</a></div>
                    <div class="toolTitle"><a href="${h.url_for( controller='admin', action='jobs' )}" target="galaxy_main">Manage jobs</a></div>
                  </div>
                </div>
                <div class="toolSectionPad"></div>
                <div class="toolSectionTitle">
                  <span>Form Definitions</span>
                </div>
                <div class="toolSectionBody">
                  <div class="toolSectionBg">
                    <div class="toolTitle"><a href="${h.url_for( controller='forms', action='browse_form_definitions' )}" target="galaxy_main">Manage form definitions</a></div>
                  </div>
                </div>
                <div class="toolSectionPad"></div>
                <div class="toolSectionTitle">
                  <span>Sample Tracking</span>
                </div>
                <div class="toolSectionBody">
                  <div class="toolSectionBg">
                    <div class="toolTitle"><a href="${h.url_for( controller='sequencer', action='browse_request_types' )}" target="galaxy_main">Manage sequencers</a></div>
                    <div class="toolTitle"><a href="${h.url_for( controller='requests_admin', action='browse_requests' )}" target="galaxy_main">Sequencing requests</a></div>
                    <div class="toolTitle"><a href="${h.url_for( controller='requests_common', action='find_samples', cntrller='requests_admin' )}" target="galaxy_main">Find samples</a></div>
                  </div>
                </div>
            </div>
        </div>    
    </div>
</%def>

<%def name="center_panel()">
    <%
        center_url = h.url_for( action='center', webapp='galaxy' )
    %>
    <iframe name="galaxy_main" id="galaxy_main" frameborder="0" style="position: absolute; width: 100%; height: 100%;" src="${center_url}"> </iframe>
</%def>
