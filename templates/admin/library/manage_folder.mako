<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/dataset/security_common.mako" import="render_permission_form" />
<%namespace file="/admin/library/common.mako" import="render_available_templates" />
<%namespace file="/admin/library/common.mako" import="render_existing_library_item_info" />

%if msg:
    ${render_msg( msg, messagetype )}
%endif

<div class="toolForm">
    <div class="toolFormTitle">Edit folder name and description</div>
    <div class="toolFormBody">
        <form name="folder" action="${h.url_for( controller='admin', action='folder', manage=True, id=folder.id, library_id=library_id )}" method="post" >
            <div class="form-row">
                <label>Name:</label>
                <div style="float: left; width: 250px; margin-right: 10px;">
                    <input type="text" name="name" value="${folder.name}" size="40"/>
                </div>
                <div style="clear: both"></div>
            </div>
            <div class="form-row">
                <label>Description:</label>
                <div style="float: left; width: 250px; margin-right: 10px;">
                    <input type="text" name="description" value="${folder.description}" size="40"/>
                </div>
                <div style="clear: both"></div>
            </div>
            <input type="submit" name="rename_folder_button" value="Save"/>
        </form>
    </div>
</div>

<p/>

<%
    roles = trans.app.model.Role.filter( trans.app.model.Role.table.c.deleted==False ).order_by( trans.app.model.Role.table.c.name ).all()
%>

${render_permission_form( folder, folder.name, h.url_for( controller='admin', action='folder', id=folder.id, library_id=library_id ), roles )}

${render_existing_library_item_info( folder )}

${render_available_templates( folder )}
