## Because HDAs do not have many of the properties that other sharable items have, we need to override most of the default code for display.
<%inherit file="/display_base.mako"/>
<%namespace file="/display_common.mako" import="*" />
<%namespace file="/tagging_common.mako" import="render_individual_tagging_element, render_community_tagging_element" />

<%def name="javascripts()">
    ${parent.javascripts()}
</%def>

<%def name="init()">
<%
	self.has_left_panel=False
	self.has_right_panel=True
	self.message_box_visible=False
	self.active_view="user"
	self.overlay_visible=False
%>
</%def>

<%def name="title()">
    Galaxy | ${get_class_display_name( item.__class__ )} | ${get_item_name( item ) | h}
</%def>

<%def name="render_item_links( data )">
    ## Provide links to save data and import dataset.
    <a href="${h.url_for( controller='/dataset', action='display', dataset_id=trans.security.encode_id( data.id ), to_ext=data.ext )}" class="icon-button disk tooltip" title="Save dataset"></a>
        <a 
            href="${h.url_for( controller='/dataset', action='imp', dataset_id=trans.security.encode_id( data.id ) )}"
            class="icon-button import tooltip" 
            title="Import dataset"></a>
</%def>

<%def name="render_item( data, data_to_render )">
    %if truncated:
        <div class="warningmessagelarge">
            This dataset is large and only the first megabyte is shown below. | 
            <a href="${h.url_for( controller='dataset', action='display_by_username_and_slug', username=data.history.user.username, slug=trans.security.encode_id( data.id ), preview=False )}">Show all</a>
        </div>    
    %endif
    ## TODO: why is the default font size so small?
    <pre style="font-size: 135%">${ data_to_render | h }</pre>
</%def>


<%def name="center_panel()">
    <div class="unified-panel-header" unselectable="on">
		<div class="unified-panel-header-inner">
				${get_class_display_name( item.__class__ )}
			| ${get_item_name( item ) | h}
	    </div>
    </div>
    
    <div class="unified-panel-body">
        <div style="overflow: auto; height: 100%;">        
            <div class="page-body">
                <div style="float: right">
                    ${self.render_item_links( item )}
                </div>
                <div>
                    ${self.render_item_header( item )}
                </div>
                
                ${self.render_item( item, item_data )}
            </div>
        </div>
    </div>
</%def>

<%def name="right_panel()">
    <div class="unified-panel-header" unselectable="on">
        <div class="unified-panel-header-inner">
            About this ${get_class_display_name( item.__class__ )}
        </div>
    </div>
    
    <div class="unified-panel-body">
        <div style="overflow: auto; height: 100%;">
            <div style="padding: 10px;">
                <h4>Author</h4>
                
                <p>${item.history.user.username | h}</p>
                
                <div><img src="http://www.gravatar.com/avatar/${h.md5(item.history.user.email)}?d=identicon&s=150"></div>

                ## Page meta. 
                
                ## No links for datasets right now.
        
                ## Tags.
                <p>
                <h4>Tags</h4>
                <p>
                ## Community tags.
                <div>
                    Community:
                    ${render_community_tagging_element( tagged_item=item, tag_click_fn='community_tag_click', use_toggle_link=False )}
                    %if len ( item.tags ) == 0:
                        none
                    %endif
                </div>
                ## Individual tags.
                <p>
                <div>
                    Yours:
                    ${render_individual_tagging_element( user=trans.get_user(), tagged_item=item, elt_context='view.mako', use_toggle_link=False, tag_click_fn='community_tag_click' )}
                </div>
            </div>    
        </div>
    </div>

</%def>