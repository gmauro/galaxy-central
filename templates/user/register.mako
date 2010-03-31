<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%def name="javascripts()">
    ${parent.javascripts()}
    <script type="text/javascript">
    $( function() {
        $( "select[refresh_on_change='true']").change( function() {
            var refresh = false;
            var refresh_on_change_values = $( this )[0].attributes.getNamedItem( 'refresh_on_change_values' )
            if ( refresh_on_change_values ) {
                refresh_on_change_values = refresh_on_change_values.value.split( ',' );
                var last_selected_value = $( this )[0].attributes.getNamedItem( 'last_selected_value' );
                for( i= 0; i < refresh_on_change_values.length; i++ ) {
                    if ( $( this )[0].value == refresh_on_change_values[i] || ( last_selected_value && last_selected_value.value == refresh_on_change_values[i] ) ){
                        refresh = true;
                        break;
                    }
                }
            }
            else {
                refresh = true;
            }
            if ( refresh ){
                $( "#registration" ).submit();
            }
        });
    });
    </script>
</%def>

<%
    from galaxy.web.form_builder import CheckboxField
    subscribe_check_box = CheckboxField( 'subscribe' )
%>
%if msg:
    ${render_msg( msg, messagetype )}
%endif
<div class="toolForm">
    <form name="registration" id="registration" action="${h.url_for( controller='user', action='create', admin_view=admin_view )}" method="post" >
        <div class="toolFormTitle">Create account</div>
        <div class="form-row">
            <label>Email address:</label>
            <input type="text" name="email" value="${email}" size="40"/>
            <input type="hidden" name="webapp" value="${webapp}" size="40"/>
        </div>
        <div class="form-row">
            <label>Password:</label>
            <input type="password" name="password" value="${password}" size="40"/>
        </div>
        <div class="form-row">
            <label>Confirm password:</label>
            <input type="password" name="confirm" value="${confirm}" size="40"/>
        </div>
        <div class="form-row">
            <label>Public user name:</label>
            <input type="text" name="username" size="40" value="${username}"/>
            <div class="toolParamHelp" style="clear: both;">
                When you share or publish items, this name is shown as the author.
            </div>
        </div>
        <div class="form-row">
            <label>Subscribe to mailing list:</label>
            %if subscribe_checked:
                <% subscribe_check_box.checked = True %>
            %endif
            ${subscribe_check_box.get_html()}
        </div>
        %if user_info_select:
            <div class="form-row">
                <label>User type</label>
                ${user_info_select.get_html()}
            </div>
        %endif
        %if user_info_form:
            %for field in widgets:
                <div class="form-row">
                    <label>${field['label']}</label>
                    ${field['widget'].get_html()}
                    <div class="toolParamHelp" style="clear: both;">
                        ${field['helptext']}
                    </div>
                    <div style="clear: both"></div>
                </div>
            %endfor
            %if not user_info_select:
                <input type="hidden" name="user_info_select" value="${user_info_form.id}"/>
            %endif   
        %endif
        <div class="form-row">
            <input type="submit" name="create_user_button" value="Submit"/>
        </div>
    </form>
</div>
