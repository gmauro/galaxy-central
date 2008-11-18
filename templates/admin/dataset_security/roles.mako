<%inherit file="/base.mako"/>

<% 
    import galaxy.model
%>

## Render a row
<%def name="render_row( role, ctr, anchored, curr_anchor )">
    %if ctr % 2 == 1:
        <tr class="odd_row">
    %else:
        <tr>
    %endif
        <td>
            ${role.name}
            <a id="role-${role.id}-popup" class="popup-arrow" style="display: none;">&#9660;</a>
            <div popupmenu="role-${role.id}-popup">
                <a class="action-button" href="${h.url_for( action='role', role_id=role.id )}">Change associated users and groups</a>
                <a class="action-button" href="${h.url_for( action='mark_role_deleted', role_id=role.id )}">Mark role deleted</a>
            </div>
        </td>
        <td>${role.type}</td>
        <td>
            <ul>
                %for ura in role.users:
                    <li><a href="${h.url_for( action='user_groups_edit', user_id=ura.user.id )}">${ura.user.email}</a></li>
                %endfor
            </ul>
        </td>
        <td>
            <ul>
                %for gra in role.groups:
                    <li><a href="${h.url_for( action='group_members_edit', group_id=gra.group.id )}">${gra.group.name}</a></li>
                %endfor
            </ul>
            %if not anchored:
                <a name="${curr_anchor}"></a>
                <div style="float: right;"><a href="#TOP">top</a></div>
            %endif
        </td>
    </tr>
</%def>

%if msg:
    <div class="donemessage">${msg}</div>
%endif

<a name="TOP"><h2>Non-private Roles</h2></a>

<ul class="manage-table-actions">
    <li><a class="action-button" href="${h.url_for( controller='admin', action='create_role' )}">Create a new role</a></li>
    <li><a class="action-button" href="${h.url_for( controller='admin', action='deleted_roles' )}">Manage deleted roles</a></li>
</ul>

%if len( roles ) == 0:
    There are no non-private Galaxy roles
%else:
    <table class="manage-table colored" border="0" cellspacing="0" cellpadding="0" width="100%">
        <% 
            render_quick_find = len( roles ) > 50
            ctr = 0
        %>
        %if render_quick_find:
            <%
                anchors = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
                anchor_loc = 0
                anchored = False
                curr_anchor = 'A'
            %>
            <tr style="background: #EEE">
                <td colspan="4" style="text-align: center; border-bottom: 1px solid #D8B365">
                    Jump to letter:
                    %for a in anchors:
                        | <a href="#${a}">${a}</a>
                    %endfor
                </td>
            </tr>
        %endif
        <tr class="header">
            <td>Name</td>
            <td>Type</td>
            <td>Users</td>
            <td>Groups</td>
        </tr>
        %for ctr, role in enumerate( roles ):
            %if render_quick_find and not role.name.upper().startswith( curr_anchor ):
                <% anchored = False %>
            %endif
            %if render_quick_find and role.name.upper().startswith( curr_anchor ):
                %if not anchored:
                    ${render_row( role, ctr, anchored, curr_anchor )}
                    <% anchored = True %>
                %else:
                    ${render_row( role, ctr, anchored, curr_anchor )}
                %endif
            %elif render_quick_find:
                %for anchor in anchors[ anchor_loc: ]:
                    %if role.name.upper().startswith( anchor ):
                        %if not anchored:
                            <% curr_anchor = anchor %>
                            ${render_row( role, ctr, anchored, curr_anchor )}
                            <% anchored = True %>
                        %else:
                            ${render_row( role, ctr, anchored, curr_anchor )}
                        %endif
                        <% 
                            anchor_loc = anchors.index( anchor )
                            break 
                        %>
                    %endif
                %endfor
            %else:
                ${render_row( role, ctr, True, '' )}
            %endif
        %endfor
    </table>
%endif
