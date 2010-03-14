<%!
    def inherit(context):
        if context.get('use_panels') is True:
            return '/base_panels.mako'
        else:
            return '/base.mako'
%>
<%inherit file="${inherit(context)}"/>
<% _=n_ %>

<%def name="init()">
<%
    self.has_left_panel=False
    self.has_right_panel=False
    self.active_view=active_view
    self.message_box_visible=False
%>
</%def>

<%def name="javascripts()">
    ${parent.javascripts()}
    <script type="text/javascript">
        %if 'masthead' in refresh_frames:
            ## if ( parent.frames && parent.frames.galaxy_masthead ) {
            ##     parent.frames.galaxy_masthead.location.href="${h.url_for( controller='root', action='masthead')}";
            ## }
            ## else if ( parent.parent && parent.parent.frames && parent.parent.frames.galaxy_masthead ) {
            ##     parent.parent.frames.galaxy_masthead.location.href="${h.url_for( controller='root', action='masthead')}";
            ## }
            
            ## Refresh masthead == user changes (backward compatibility)
            if ( parent.user_changed ) {
                %if trans.user:
                    parent.user_changed( "${trans.user.email}", ${int( app.config.is_admin_user( trans.user ) )} );
                %else:
                    parent.user_changed( null, false );
                %endif
            }
        %endif
        %if 'history' in refresh_frames:
            if ( parent.frames && parent.frames.galaxy_history ) {
                parent.frames.galaxy_history.location.href="${h.url_for( controller='root', action='history')}";
                if ( parent.force_right_panel ) {
                    parent.force_right_panel( 'show' );
                }
            }
        %endif
        %if 'tools' in refresh_frames:
            if ( parent.frames && parent.frames.galaxy_tools ) {
                parent.frames.galaxy_tools.location.href="${h.url_for( controller='root', action='tool_menu')}";
                if ( parent.force_left_panel ) {
                    parent.force_left_panel( 'show' );
                }
            }
        %endif

        if ( parent.handle_minwidth_hint )
        {
            parent.handle_minwidth_hint( -1 );
        }
    </script>
</%def>

##
## Override methods from base.mako and base_panels.mako
##

<%def name="center_panel()">
    ${render_large_message( message, message_type )}
</%def>

<%def name="body()">
    ${render_large_message( message, message_type )}
</%def>

## Render large message.
<%def name="render_large_message( message, message_type )">
    <div class="${message_type}messagelarge" style="margin: 1em">${_(message)}</div>
</%def>

## Render a message
<%def name="render_msg( msg, messagetype='done' )">
    <div class="${messagetype}message">${_(msg)}</div>
    <br/>
</%def>

