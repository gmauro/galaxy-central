define(["mvc/dataset/hda-model"],function(b){var a=Backbone.View.extend(LoggableMixin).extend({tagName:"div",className:"dataset hda history-panel-hda",id:function(){return"hda-"+this.model.get("id")},fxSpeed:"fast",initialize:function(c){if(c.logger){this.logger=this.model.logger=c.logger}this.log(this+".initialize:",c);this.defaultPrimaryActionButtonRenderers=[this._render_showParamsButton];this.selectable=c.selectable||false;this.selected=c.selected||false;this.expanded=c.expanded||false;this.draggable=c.draggable||false;this._setUpListeners()},_setUpListeners:function(){this.model.on("change",function(d,c){if(this.model.changedAttributes().state&&this.model.inReadyState()&&this.expanded&&!this.model.hasDetails()){this.model.fetch()}else{this.render()}},this)},render:function(e){e=(e===undefined)?(true):(e);var c=this;this.$el.find("[title]").tooltip("destroy");this.urls=this.model.urls();var d=$(a.templates.skeleton(this.model.toJSON()));d.find(".dataset-primary-actions").append(this._render_titleButtons());d.children(".dataset-body").replaceWith(this._render_body());this._setUpBehaviors(d);if(e){$(c).queue(function(f){this.$el.fadeOut(c.fxSpeed,f)})}$(c).queue(function(f){this.$el.empty().attr("class",c.className).addClass("state-"+c.model.get("state")).append(d.children());if(this.selectable){this.showSelector(0)}f()});if(e){$(c).queue(function(f){this.$el.fadeIn(c.fxSpeed,f)})}$(c).queue(function(f){this.trigger("rendered",c);if(this.model.inReadyState()){this.trigger("rendered:ready",c)}if(this.draggable){this.draggableOn()}f()});return this},_setUpBehaviors:function(c){c=c||this.$el;make_popup_menus(c);c.find("[title]").tooltip({placement:"bottom"})},_render_titleButtons:function(){return[this._render_displayButton()]},_render_displayButton:function(){if((this.model.get("state")===b.HistoryDatasetAssociation.STATES.NOT_VIEWABLE)||(this.model.get("state")===b.HistoryDatasetAssociation.STATES.DISCARDED)||(this.model.get("state")===b.HistoryDatasetAssociation.STATES.NEW)||(!this.model.get("accessible"))){return null}var d={target:"galaxy_main",classes:"dataset-display"};if(this.model.get("purged")){d.disabled=true;d.title=_l("Cannot display datasets removed from disk")}else{if(this.model.get("state")===b.HistoryDatasetAssociation.STATES.UPLOAD){d.disabled=true;d.title=_l("This dataset must finish uploading before it can be viewed")}else{d.title=_l("View data");d.href=this.urls.display;var c=this;d.onclick=function(){Galaxy.frame.add({title:"Data Viewer: "+c.model.get("name"),type:"url",target:"galaxy_main",content:c.urls.display})}}}d.faIcon="fa-eye";return faIconButton(d)},_render_downloadButton:function(){if(this.model.get("purged")||!this.model.hasData()){return null}var d=this.urls,e=this.model.get("meta_files");if(_.isEmpty(e)){return $(['<a href="'+d.download+'" title="'+_l("Download")+'" class="icon-btn">','<span class="fa fa-floppy-o"></span>',"</a>"].join(""))}var f="dataset-"+this.model.get("id")+"-popup",c=['<div popupmenu="'+f+'">','<a href="'+d.download+'">',_l("Download Dataset"),"</a>","<a>"+_l("Additional Files")+"</a>",_.map(e,function(g){return['<a class="action-button" href="',d.meta_download+g.file_type,'">',_l("Download")," ",g.file_type,"</a>"].join("")}).join("\n"),"</div>",'<div class="icon-btn-group">','<a href="'+d.download+'" title="'+_l("Download")+'" class="icon-btn">','<span class="fa fa-floppy-o"></span>','</a><a class="icon-btn popup" id="'+f+'">','<span class="fa fa-caret-down"></span>',"</a>","</div>"].join("\n");return $(c)},_render_showParamsButton:function(){return faIconButton({title:_l("View details"),href:this.urls.show_params,target:"galaxy_main",faIcon:"fa-info-circle"})},_render_body:function(){var d=$('<div>Error: unknown dataset state "'+this.model.get("state")+'".</div>'),c=this["_render_body_"+this.model.get("state")];if(_.isFunction(c)){d=c.call(this)}this._setUpBehaviors(d);if(this.expanded){d.show()}return d},_render_stateBodyHelper:function(c,f){f=f||[];var d=this,e=$(a.templates.body(_.extend(this.model.toJSON(),{body:c})));e.find(".dataset-actions .left").append(_.map(f,function(g){return g.call(d)}));return e},_render_body_new:function(){return this._render_stateBodyHelper("<div>"+_l("This is a new dataset and not all of its data are available yet")+"</div>")},_render_body_noPermission:function(){return this._render_stateBodyHelper("<div>"+_l("You do not have permission to view this dataset")+"</div>")},_render_body_discarded:function(){return this._render_stateBodyHelper("<div>"+_l("The job creating this dataset was cancelled before completion")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_queued:function(){return this._render_stateBodyHelper("<div>"+_l("This job is waiting to run")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_upload:function(){return this._render_stateBodyHelper("<div>"+_l("This dataset is currently uploading")+"</div>")},_render_body_setting_metadata:function(){return this._render_stateBodyHelper("<div>"+_l("Metadata is being auto-detected")+"</div>")},_render_body_running:function(){return this._render_stateBodyHelper("<div>"+_l("This job is currently running")+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_paused:function(){return this._render_stateBodyHelper("<div>"+_l('This job is paused. Use the "Resume Paused Jobs" in the history menu to resume')+"</div>",this.defaultPrimaryActionButtonRenderers)},_render_body_error:function(){var c=['<span class="help-text">',_l("An error occurred with this dataset"),":</span>",'<div class="job-error-text">',$.trim(this.model.get("misc_info")),"</div>"].join("");if(!this.model.get("purged")){c="<div>"+this.model.get("misc_blurb")+"</div>"+c}return this._render_stateBodyHelper(c,this.defaultPrimaryActionButtonRenderers.concat([this._render_downloadButton]))},_render_body_empty:function(){return this._render_stateBodyHelper("<div>"+_l("No data")+": <i>"+this.model.get("misc_blurb")+"</i></div>",this.defaultPrimaryActionButtonRenderers)},_render_body_failed_metadata:function(){var c=$('<div class="warningmessagesmall"></div>').append($("<strong/>").text(_l("An error occurred setting the metadata for this dataset"))),d=this._render_body_ok();d.prepend(c);return d},_render_body_ok:function(){var c=this,e=$(a.templates.body(this.model.toJSON())),d=[this._render_downloadButton].concat(this.defaultPrimaryActionButtonRenderers);e.find(".dataset-actions .left").append(_.map(d,function(f){return f.call(c)}));if(this.model.isDeletedOrPurged()){return e}return e},events:{"click .dataset-title-bar":"toggleBodyVisibility","keydown .dataset-title-bar":"toggleBodyVisibility","click .dataset-selector":"toggleSelect",},toggleBodyVisibility:function(f,d){var c=32,e=13;if((f.type==="keydown")&&!(f.keyCode===c||f.keyCode===e)){return true}var g=this.$el.find(".dataset-body");d=(d===undefined)?(!g.is(":visible")):(d);if(d){this.expandBody()}else{this.collapseBody()}return false},expandBody:function(){var c=this;function d(){c.$el.children(".dataset-body").replaceWith(c._render_body());c.$el.children(".dataset-body").slideDown(c.fxSpeed,function(){c.expanded=true;c.trigger("body-expanded",c.model.get("id"))})}if(this.model.inReadyState()&&!this.model.hasDetails()){this.model.fetch({silent:true}).always(function(e){d()})}else{d()}},collapseBody:function(){var c=this;this.$el.children(".dataset-body").slideUp(c.fxSpeed,function(){c.expanded=false;c.trigger("body-collapsed",c.model.get("id"))})},showSelector:function(e){if(this.$el.find(".dataset-selector").css("display")!=="none"){return}e=(e!==undefined)?(e):(this.fxSpeed);if(this.selected){this.select(null,true)}var d=this,c=32;if(e){this.$el.queue("fx",function(f){$(this).find(".dataset-primary-actions").fadeOut(e,f)});this.$el.queue("fx",function(f){$(this).find(".dataset-selector").show().animate({width:c},e,f);$(this).find(".dataset-title-bar").animate({"margin-left":c},e,f);d.selectable=true;d.trigger("selectable",true,d)})}else{this.$el.find(".dataset-primary-actions").hide();this.$el.find(".dataset-selector").show().css({width:c});this.$el.find(".dataset-title-bar").show().css({"margin-left":c});d.selectable=true;d.trigger("selectable",true,d)}},hideSelector:function(c){c=(c!==undefined)?(c):(this.fxSpeed);this.selectable=false;this.trigger("selectable",false,this);if(c){this.$el.queue("fx",function(d){$(this).find(".dataset-title-bar").show().css({"margin-left":"0"});$(this).find(".dataset-selector").animate({width:"0px"},c,function(){$(this).hide();d()})});this.$el.queue("fx",function(d){$(this).find(".dataset-primary-actions").fadeIn(c,d)})}else{$(this).find(".dataset-selector").css({width:"0px"}).hide();$(this).find(".dataset-primary-actions").show()}},toggleSelector:function(c){if(!this.$el.find(".dataset-selector").is(":visible")){this.showSelector(c)}else{this.hideSelector(c)}},select:function(c){this.$el.find(".dataset-selector span").removeClass("fa-square-o").addClass("fa-check-square-o");if(!this.selected){this.trigger("selected",this);this.selected=true}return false},deselect:function(c){this.$el.find(".dataset-selector span").removeClass("fa-check-square-o").addClass("fa-square-o");if(this.selected){this.trigger("de-selected",this);this.selected=false}return false},toggleSelect:function(c){if(this.selected){this.deselect(c)}else{this.select(c)}},draggableOn:function(){this.draggable=true;this.dragStartHandler=_.bind(this._dragStartHandler,this);this.dragEndHandler=_.bind(this._dragEndHandler,this);var c=this.$el.find(".dataset-title-bar").attr("draggable",true).get(0);c.addEventListener("dragstart",this.dragStartHandler,false);c.addEventListener("dragend",this.dragEndHandler,false)},draggableOff:function(){this.draggable=false;var c=this.$el.find(".dataset-title-bar").attr("draggable",false).get(0);c.removeEventListener("dragstart",this.dragStartHandler,false);c.removeEventListener("dragend",this.dragEndHandler,false)},toggleDraggable:function(){if(this.draggable){this.draggableOff()}else{this.draggableOn()}},_dragStartHandler:function(c){this.trigger("dragstart",this);c.dataTransfer.effectAllowed="move";c.dataTransfer.setData("text",JSON.stringify(this.model.toJSON()));return false},_dragEndHandler:function(c){this.trigger("dragend",this);return false},remove:function(d){var c=this;this.$el.fadeOut(c.fxSpeed,function(){c.$el.remove();c.off();if(d){d()}})},toString:function(){var c=(this.model)?(this.model+""):("(no model)");return"HDABaseView("+c+")"}});a.templates={skeleton:Handlebars.templates["template-hda-skeleton"],body:Handlebars.templates["template-hda-body"]};return{HDABaseView:a}});