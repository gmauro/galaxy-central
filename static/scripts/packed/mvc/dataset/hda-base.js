define(["mvc/dataset/states","mvc/history/history-content-base-view","mvc/data","utils/localization"],function(c,h,b,e){var f=h.HistoryContentBaseView;var d=f.extend({tagName:"div",className:"dataset hda history-panel-hda",id:function(){return"hda-"+this.model.get("id")},fxSpeed:"fast",initialize:function(i){if(i.logger){this.logger=this.model.logger=i.logger}this.log(this+".initialize:",i);f.prototype.initialize.call(this,i);this.defaultPrimaryActionButtonRenderers=[this._render_showParamsButton];this.linkTarget=i.linkTarget||"_blank";this.draggable=i.draggable||false;this._setUpListeners()},_setUpListeners:function(){this.model.on("change",function(j,i){if(this.model.changedAttributes().state&&this.model.inReadyState()&&this.expanded&&!this.model.hasDetails()){this.model.fetch()}else{this.render()}},this)},render:function(i){this.$el.find("[title]").tooltip("destroy");this.urls=this.model.urls();return f.prototype.render.call(this,i)},_render_titleButtons:function(){return[this._render_displayButton()]},_render_displayButton:function(){if((this.model.get("state")===c.NOT_VIEWABLE)||(this.model.get("state")===c.DISCARDED)||(!this.model.get("accessible"))){return null}var j={target:this.linkTarget,classes:"dataset-display"};if(this.model.get("purged")){j.disabled=true;j.title=e("Cannot display datasets removed from disk")}else{if(this.model.get("state")===c.UPLOAD){j.disabled=true;j.title=e("This dataset must finish uploading before it can be viewed")}else{if(this.model.get("state")===c.NEW){j.disabled=true;j.title=e("This dataset is not yet viewable")}else{j.title=e("View data");j.href=this.urls.display;var i=this;j.onclick=function(k){if(Galaxy.frame&&Galaxy.frame.active){Galaxy.frame.add({title:"Data Viewer: "+i.model.get("name"),type:"other",content:function(l){var m=new b.TabularDataset({id:i.model.get("id")});$.when(m.fetch()).then(function(){b.createTabularDatasetChunkedView({model:m,parent_elt:l,embedded:true,height:"100%"})})}});k.preventDefault()}}}}}j.faIcon="fa-eye";return faIconButton(j)},_render_downloadButton:function(){if(this.model.get("purged")||!this.model.hasData()){return null}var j=this.urls,k=this.model.get("meta_files");if(_.isEmpty(k)){return $(['<a href="'+j.download+'" title="'+e("Download")+'" ','class="icon-btn dataset-download-btn">','<span class="fa fa-floppy-o"></span>',"</a>"].join(""))}var l="dataset-"+this.model.get("id")+"-popup",i=['<div popupmenu="'+l+'">','<a href="'+j.download+'">',e("Download dataset"),"</a>","<a>"+e("Additional files")+"</a>",_.map(k,function(m){return['<a class="action-button" href="',j.meta_download+m.file_type,'">',e("Download")," ",m.file_type,"</a>"].join("")}).join("\n"),"</div>",'<div class="icon-btn-group">','<a href="'+j.download+'" title="'+e("Download")+'" ','class="icon-btn dataset-download-btn">','<span class="fa fa-floppy-o"></span>','</a><a class="icon-btn popup" id="'+l+'">','<span class="fa fa-caret-down"></span>',"</a>","</div>"].join("\n");return $(i)},_render_showParamsButton:function(){return faIconButton({title:e("View details"),classes:"dataset-params-btn",href:this.urls.show_params,target:this.linkTarget,faIcon:"fa-info-circle"})},_renderBody:function(){var j=$('<div>Error: unknown dataset state "'+this.model.get("state")+'".</div>'),i=this["_render_body_"+this.model.get("state")];if(_.isFunction(i)){j=i.call(this)}this._setUpBehaviors(j);if(this.expanded){j.show()}return j},_render_stateBodyHelper:function(i,l){l=l||[];var j=this,k=$(d.templates.body(_.extend(this.model.toJSON(),{body:i})));k.find(".dataset-actions .left").append(_.map(l,function(m){return m.call(j)}));return k},_render_body_new:function(){return this._render_stateBodyHelper("<div>"+e("This is a new dataset and not all of its data are available yet")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_noPermission:function(){return this._render_stateBodyHelper("<div>"+e("You do not have permission to view this dataset")+"</div>")},_render_body_discarded:function(){return this._render_stateBodyHelper("<div>"+e("The job creating this dataset was cancelled before completion")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_queued:function(){return this._render_stateBodyHelper("<div>"+e("This job is waiting to run")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_upload:function(){return this._render_stateBodyHelper("<div>"+e("This dataset is currently uploading")+"</div>")},_render_body_setting_metadata:function(){return this._render_stateBodyHelper("<div>"+e("Metadata is being auto-detected")+"</div>")},_render_body_running:function(){return this._render_stateBodyHelper("<div>"+e("This job is currently running")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_paused:function(){return this._render_stateBodyHelper("<div>"+e('This job is paused. Use the "Resume Paused Jobs" in the history menu to resume')+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_error:function(){var i=['<span class="help-text">',e("An error occurred with this dataset"),":</span>",'<div class="job-error-text">',$.trim(this.model.get("misc_info")),"</div>"].join("");if(!this.model.get("purged")){i="<div>"+this.model.get("misc_blurb")+"</div>"+i}return this._render_stateBodyHelper(i,[this._render_downloadButton].concat(this.defaultPrimaryActionButtonRenderers))},_render_body_empty:function(){return this._render_stateBodyHelper("<div>"+e("No data")+": <i>"+this.model.get("misc_blurb")+"</i></div>",this.defaultPrimaryActionButtonRenderers)},_render_body_failed_metadata:function(){var i=$('<div class="warningmessagesmall"></div>').append($("<strong/>").text(e("An error occurred setting the metadata for this dataset"))),j=this._render_body_ok();j.prepend(i);return j},_render_body_ok:function(){var i=this,k=$(d.templates.body(this.model.toJSON())),j=[this._render_downloadButton].concat(this.defaultPrimaryActionButtonRenderers);k.find(".dataset-actions .left").append(_.map(j,function(l){return l.call(i)}));if(this.model.isDeletedOrPurged()){return k}return k},events:_.extend(_.clone(f.prototype.events),{}),expand:function(){var i=this;function j(){i.$el.children(".dataset-body").replaceWith(i._renderBody());i.expanded=true;i.$el.children(".dataset-body").slideDown(i.fxSpeed,function(){i.trigger("expanded",i.model)})}if(this.model.inReadyState()&&!this.model.hasDetails()){this.model.fetch({silent:true}).always(function(k){i.urls=i.model.urls();j()})}else{j()}},remove:function(j){var i=this;this.$el.fadeOut(i.fxSpeed,function(){i.$el.remove();i.off();if(j){j()}})},toString:function(){var i=(this.model)?(this.model+""):("(no model)");return"HDABaseView("+i+")"}});var a=_.template(['<div class="dataset hda">','<div class="dataset-warnings">',"<% if( hda.error ){ %>",'<div class="errormessagesmall">',e("There was an error getting the data for this dataset"),":<%- hda.error %>","</div>","<% } %>","<% if( hda.deleted ){ %>","<% if( hda.purged ){ %>",'<div class="dataset-purged-msg warningmessagesmall"><strong>',e("This dataset has been deleted and removed from disk")+".","</strong></div>","<% } else { %>",'<div class="dataset-deleted-msg warningmessagesmall"><strong>',e("This dataset has been deleted")+".","</strong></div>","<% } %>","<% } %>","<% if( !hda.visible ){ %>",'<div class="dataset-hidden-msg warningmessagesmall"><strong>',e("This dataset has been hidden")+".","</strong></div>","<% } %>","</div>",'<div class="dataset-selector">','<span class="fa fa-2x fa-square-o"></span>',"</div>",'<div class="dataset-primary-actions"></div>','<div class="dataset-title-bar clear" tabindex="0">','<span class="dataset-state-icon state-icon"></span>','<div class="dataset-title">','<span class="hda-hid"><%- hda.hid %></span> ','<span class="dataset-name"><%- hda.name %></span>',"</div>","</div>",'<div class="dataset-body"></div>',"</div>"].join(""));var g=_.template(['<div class="dataset-body">',"<% if( hda.body ){ %>",'<div class="dataset-summary">',"<%= hda.body %>","</div>",'<div class="dataset-actions clear">','<div class="left"></div>','<div class="right"></div>',"</div>","<% } else { %>",'<div class="dataset-summary">',"<% if( hda.misc_blurb ){ %>",'<div class="dataset-blurb">','<span class="value"><%- hda.misc_blurb %></span>',"</div>","<% } %>","<% if( hda.data_type ){ %>",'<div class="dataset-datatype">','<label class="prompt">',e("format"),"</label>",'<span class="value"><%- hda.data_type %></span>',"</div>","<% } %>","<% if( hda.metadata_dbkey ){ %>",'<div class="dataset-dbkey">','<label class="prompt">',e("database"),"</label>",'<span class="value">',"<%- hda.metadata_dbkey %>","</span>","</div>","<% } %>","<% if( hda.misc_info ){ %>",'<div class="dataset-info">','<span class="value"><%- hda.misc_info %></span>',"</div>","<% } %>","</div>",'<div class="dataset-actions clear">','<div class="left"></div>','<div class="right"></div>',"</div>","<% if( !hda.deleted ){ %>",'<div class="tags-display"></div>','<div class="annotation-display"></div>','<div class="dataset-display-applications">',"<% _.each( hda.display_apps, function( app ){ %>",'<div class="display-application">','<span class="display-application-location"><%- app.label %></span> ','<span class="display-application-links">',"<% _.each( app.links, function( link ){ %>",'<a target="<%= link.target %>" href="<%= link.href %>">',"<% print( _l( link.text ) ); %>","</a> ","<% }); %>","</span>","</div>","<% }); %>","<% _.each( hda.display_types, function( app ){ %>",'<div class="display-application">','<span class="display-application-location"><%- app.label %></span> ','<span class="display-application-links">',"<% _.each( app.links, function( link ){ %>",'<a target="<%= link.target %>" href="<%= link.href %>">',"<% print( _l( link.text ) ); %>","</a> ","<% }); %>","</span>","</div>","<% }); %>","</div>",'<div class="dataset-peek">',"<% if( hda.peek ){ %>",'<pre class="peek"><%= hda.peek %></pre>',"<% } %>","</div>","<% } %>","<% } %>","</div>"].join(""));d.templates=d.prototype.templates={skeleton:function(i){return a({_l:e,hda:i})},body:function(i){return g({_l:e,hda:i})}};return{HDABaseView:d}});