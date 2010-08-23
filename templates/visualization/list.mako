<%inherit file="/webapps/galaxy/base_panels.mako"/>

<%def name="init()">
<%
    self.has_left_panel=False
    self.has_right_panel=False
    self.active_view="visualization"
    self.message_box_visible=False
%>
</%def>

<%def name="center_panel()">

    <div style="overflow: auto; height: 100%;">
        <div class="page-container" style="padding: 10px;">
            ${h.to_unicode( grid )}

			<br><br>
			<h2>Visualizations shared with you by others</h2>

			%if shared_by_others:
			    <table class="colored" border="0" cellspacing="0" cellpadding="0" width="100%">
			        <tr class="header">
			            <th>Title</th>
			            <th>Owner</th>
			            <th></th>
			        </tr>
			        %for i, association in enumerate( shared_by_others ):
			            <% visualization = association.visualization %>
			            <tr>
			                <td>
			                    <a class="menubutton" id="shared-${i}-popup" href="${h.url_for( action='display_by_username_and_slug', username=visualization.user.username, slug=visualization.slug)}">${visualization.title}</a>
			                </td>
			                <td>${visualization.user.username}</td>
			                <td>
			                    <div popupmenu="shared-${i}-popup">
									<a class="action-button" href="${h.url_for( action='display_by_username_and_slug', username=visualization.user.username, slug=visualization.slug)}" target="_top">View</a>
			                    </div>
			                </td>
			            </tr>    
			        %endfor
			    </table>
			%else:

			    No visualizations have been shared with you.

			%endif

        </div>
    </div>

</%def>
