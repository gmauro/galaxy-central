<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />
<%namespace file="/admin/requests/common.mako" import="*" />
<%namespace file="/common/template_common.mako" import="render_template_fields" />

<% form_type = trans.model.FormDefinition.types.RUN_DETAILS_TEMPLATE %>

<br/><br/>
<ul class="manage-table-actions">
    <li><a class="action-button" id="request_type-${request_type.id}-popup" class="menubutton">Configuration Actions</a></li>
    <div popupmenu="request_type-${request_type.id}-popup">
        <li><a class="action-button" href="${h.url_for( controller='request_type', action='view_request_type', id=trans.security.encode_id( request_type.id ) )}">Browse configuration</a></li>
        %if not request_type.deleted:
            %if not request_type.run_details:
                <a class="action-button" href="${h.url_for( controller='request_type', action='add_template', cntrller='requests_admin', item_type='request_type', form_type=form_type, request_type_id=trans.security.encode_id( request_type.id ) )}">Use run details template</a>
            %elif request_type.run_details:
                <a class="action-button" href="${h.url_for( controller='request_type', action='edit_template', cntrller='requests_admin', item_type='request_type', form_type=form_type, request_type_id=trans.security.encode_id( request_type.id ) )}">Edit run details template</a>
                <a class="action-button" href="${h.url_for( controller='request_type', action='delete_template', cntrller='requests_admin', item_type='request_type', form_type=form_type, request_type_id=trans.security.encode_id( request_type.id ) )}">Unuse run details template</a>
            %endif
            <li><a class="action-button" href="${h.url_for( controller='request_type', action='request_type_permissions', id=trans.security.encode_id( request_type.id ) )}">Edit permissions</a></li>
            <li><a class="action-button" href="${h.url_for( controller='request_type', action='delete_request_type', id=trans.security.encode_id( request_type.id ) )}">Delete configuration</a></li>
        %endif
        %if request_type.deleted:
            <li><a class="action-button" href="${h.url_for( controller='request_type', action='undelete_request_type', id=trans.security.encode_id( request_type.id ) )}">Undelete configuration</a></li>
        %endif
    </div>
</ul>

%if message:
    ${render_msg( message, status )}
%endif

<form name="edit_request_type" action="${h.url_for( controller='request_type', action='edit_request_type', id=trans.security.encode_id( request_type.id ) )}" method="post" >
    <div class="toolForm">
        <div class="toolFormTitle">"Edit ${request_type.name}" sequencer configuration</div>
        <div class="form-row">
            <label>Name:</label>
            <input type="text" name="name" value="${request_type.name}" size="40"/>
            <div style="clear: both"></div>
        </div>
        <div class="form-row">
            <label>Description:</label>
            <input type="text" name="desc" value="${request_type.desc}" size="40"/>
            <div style="clear: both"></div>
        </div>
        <div class="form-row">
            <label>Sequencing request form definition:</label>
            <a href="${h.url_for( controller='request_type', action='view_form_definition', id=trans.security.encode_id( request_type.request_form_id ) )}">${request_type.request_form.name}</a>
            ## Hidden field needed by the __save_request_type() method
            <input type="hidden" name="request_form_id" value="${trans.security.encode_id( request_type.request_form_id )}" size="40"/>
        </div>       
        <div class="form-row">
            <label>Sample form definition:</label>
            <a href="${h.url_for( controller='request_type', action='view_form_definition', id=trans.security.encode_id( request_type.sample_form_id ) )}">${request_type.sample_form.name}</a>
            ## Hidden field needed by the __save_request_type() method
            <input type="hidden" name="sample_form_id" value="${trans.security.encode_id( request_type.sample_form_id )}" size="40"/>
        </div>
    </div>
    <p/>
    <div class="toolForm">
        <div class="toolFormTitle">Sample states defined for this sequencer configuration</div>
        %for element_count, state in enumerate( request_type.states ):
		    <div class="repeat-group-item">
		        <div class="form-row">
		            <label>${1+element_count}. State name:</label>
		            <input type="text" name="state_name_${trans.security.encode_id( state.id )}" value="${state.name}" size="40"/>
		        </div>
		        <div class="form-row">
		            <label>Description:</label>
		            <input type="text" name="state_desc_${trans.security.encode_id( state.id )}" value="${state.desc}" size="40"/>
		            <div class="toolParamHelp" style="clear: both;">
		                optional
		            </div>
		        </div>
		        <div style="clear: both"></div>
		   </div>
        %endfor
    </div>
    <p/>
    <div class="toolForm">
        <div class="toolFormTitle">Sequencer login information</div>
        <div class="form-row">
            This information is needed only if you will transfer datasets from the sequencer to a target Galaxy data library
        </div>
        <div style="clear: both"></div>
        <div class="form-row">
            <label>Hostname or IP Address:</label>
            <input type="text" name="host" value="${request_type.datatx_info['host']}" size="40"/>
        </div>
        <div style="clear: both"></div>
        <div class="form-row">
            <label>Username:</label>
            <input type="text" name="username" value="${request_type.datatx_info['username']}" size="40"/>
        </div>
        <div style="clear: both"></div>
        <div class="form-row">
            <label>Password:</label>
            <input type="password" name="password" value="${request_type.datatx_info['password']}" size="40"/>
        </div>
        <div style="clear: both"></div>
        <div class="form-row">
            <label>Data directory:</label>
            <input type="text" name="data_dir" value="${request_type.datatx_info.get('data_dir', '')}" size="40"/>
        </div>
        <div style="clear: both"></div>
        <div class="form-row">
            <label>Prepend the experiment name and sample name to the dataset name?</label>
            ${rename_dataset_select_field.get_html()}
            <div class="toolParamHelp" style="clear: both;">
                Galaxy datasets are renamed by prepending the experiment name and sample name to the dataset name, ensuring
                dataset names remain unique in Galaxy even when multiple datasets have the same name on the sequencer.
            </div>
        </div>
        <div style="clear: both"></div>
    </div>
    <div class="form-row">
        <input type="submit" name="edit_request_type_button" value="Save"/>
    </div>
</form>

%if widgets:
    ${render_template_fields( cntrller='requests_admin', item_type='request_type', widgets=widgets, widget_fields_have_contents=widget_fields_have_contents, request_type_id=trans.security.encode_id( request_type.id ) )}
%endif
