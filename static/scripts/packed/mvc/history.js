function linkHTMLTemplate(b,a){if(!b){return"<a></a>"}a=a||"a";var c=["<"+a];for(key in b){var d=b[key];if(d===""){continue}switch(key){case"text":continue;case"classes":key="class";d=(b.classes.join)?(b.classes.join(" ")):(b.classes);default:c.push([" ",key,'="',d,'"'].join(""))}}c.push(">");if("text" in b){c.push(b.text)}c.push("</"+a+">");return c.join("")}var HistoryItem=BaseModel.extend(LoggableMixin).extend({defaults:{id:null,name:"",data_type:null,file_size:0,genome_build:null,metadata_data_lines:0,metadata_dbkey:null,metadata_sequences:0,misc_blurb:"",misc_info:"",model_class:"",state:"",deleted:false,purged:false,visible:true,for_editing:true,bodyIsShown:false},initialize:function(){this.log(this+".initialize",this.attributes);this.log("\tparent history_id: "+this.get("history_id"));if(!this.get("accessible")){this.set("state",HistoryItem.STATES.NOT_VIEWABLE)}},isEditable:function(){return(!(this.get("deleted")||this.get("purged")))},hasData:function(){return(this.get("file_size")>0)},toString:function(){var a=this.get("id")||"";if(this.get("name")){a+=':"'+this.get("name")+'"'}return"HistoryItem("+a+")"}});HistoryItem.STATES={NOT_VIEWABLE:"not_viewable",NEW:"new",UPLOAD:"upload",QUEUED:"queued",RUNNING:"running",OK:"ok",EMPTY:"empty",ERROR:"error",DISCARDED:"discarded",SETTING_METADATA:"setting_metadata",FAILED_METADATA:"failed_metadata"};var HistoryItemView=BaseView.extend(LoggableMixin).extend({tagName:"div",className:"historyItemContainer",initialize:function(){this.log(this+".initialize:",this,this.model)},render:function(){var d=this.model.get("id"),c=this.model.get("state");this.clearReferences();this.$el.attr("id","historyItemContainer-"+d);var a=$("<div/>").attr("id","historyItem-"+d).addClass("historyItemWrapper").addClass("historyItem").addClass("historyItem-"+c);a.append(this._render_warnings());a.append(this._render_titleBar());this.body=$(this._render_body());a.append(this.body);a.find(".tooltip").tooltip({placement:"bottom"});var b=a.find("[popupmenu]");b.each(function(e,f){f=$(f);make_popupmenu(f)});this.$el.children().remove();return this.$el.append(a)},clearReferences:function(){this.displayButton=null;this.editButton=null;this.deleteButton=null;this.errButton=null},_render_warnings:function(){return $(jQuery.trim(HistoryItemView.templates.messages(this.model.toJSON())))},_render_titleBar:function(){var a=$('<div class="historyItemTitleBar" style="overflow: hidden"></div>');a.append(this._render_titleButtons());a.append('<span class="state-icon"></span>');a.append(this._render_titleLink());return a},_render_titleButtons:function(){var a=$('<div class="historyItemButtons"></div>');a.append(this._render_displayButton());a.append(this._render_editButton());a.append(this._render_deleteButton());return a},_render_displayButton:function(){if(this.model.get("state")===HistoryItem.STATES.UPLOAD){return null}displayBtnData=(this.model.get("purged"))?({title:"Cannot display datasets removed from disk",enabled:false,icon_class:"display"}):({title:"Display data in browser",href:this.model.get("display_url"),target:(this.model.get("for_editing"))?("galaxy_main"):(null),icon_class:"display"});this.displayButton=new IconButtonView({model:new IconButton(displayBtnData)});return this.displayButton.render().$el},_render_editButton:function(){if((this.model.get("state")===HistoryItem.STATES.UPLOAD)||(!this.model.get("for_editing"))){return null}var c=this.model.get("purged"),a=this.model.get("deleted"),b={title:"Edit attributes",href:this.model.get("edit_url"),target:"galaxy_main",icon_class:"edit"};if(a||c){b.enabled=false}if(a){b.title="Undelete dataset to edit attributes"}else{if(c){b.title="Cannot edit attributes of datasets removed from disk"}}this.editButton=new IconButtonView({model:new IconButton(b)});return this.editButton.render().$el},_render_deleteButton:function(){if(!this.model.get("for_editing")){return null}var a={title:"Delete",href:this.model.get("delete_url"),target:"galaxy_main",id:"historyItemDeleter-"+this.model.get("id"),icon_class:"delete"};if((this.model.get("deleted")||this.model.get("purged"))&&(!this.model.get("delete_url"))){a={title:"Dataset is already deleted",icon_class:"delete",enabled:false}}this.deleteButton=new IconButtonView({model:new IconButton(a)});return this.deleteButton.render().$el},_render_titleLink:function(){return $(jQuery.trim(HistoryItemView.templates.titleLink(this.model.toJSON())))},_render_hdaSummary:function(){var a=this.model.toJSON();if(this.model.get("metadata_dbkey")==="?"&&this.model.isEditable()){_.extend(a,{dbkey_unknown_and_editable:true})}return HistoryItemView.templates.hdaSummary(a)},_render_primaryActionButtons:function(c){var b=$("<div/>"),a=this;_.each(c,function(d){b.append(d.call(a))});return b},_render_downloadButton:function(){if(this.model.get("purged")){return null}var a=linkHTMLTemplate({title:"Download",href:this.model.get("download_url"),classes:["icon-button","tooltip","disk"]});var d=this.model.get("download_meta_urls");if(!d){return a}var c=$('<div popupmenu="dataset-'+this.model.get("id")+'-popup"></div>');c.append(linkHTMLTemplate({text:"Download Dataset",title:"Download",href:this.model.get("download_url"),classes:["icon-button","tooltip","disk"]}));c.append("<a>Additional Files</a>");for(file_type in d){c.append(linkHTMLTemplate({text:"Download "+file_type,href:d[file_type],classes:["action-button"]}))}var b=$(('<div style="float:left;" class="menubutton split popup" id="dataset-${dataset_id}-popup"></div>'));b.append(a);c.append(b);return c},_render_errButton:function(){if((this.model.get("state")!==HistoryItem.STATES.ERROR)||(!this.model.get("for_editing"))){return null}this.errButton=new IconButtonView({model:new IconButton({title:"View or report this error",href:this.model.get("report_error_url"),target:"galaxy_main",icon_class:"bug"})});return this.errButton.render().$el},_render_showParamsButton:function(){this.showParamsButton=new IconButtonView({model:new IconButton({title:"View details",href:this.model.get("show_params_url"),target:"galaxy_main",icon_class:"information"})});return this.showParamsButton.render().$el},_render_rerunButton:function(){if(!this.model.get("for_editing")){return null}this.rerunButton=new IconButtonView({model:new IconButton({title:"Run this job again",href:this.model.get("rerun_url"),target:"galaxy_main",icon_class:"arrow-circle"})});return this.rerunButton.render().$el},_render_tracksterButton:function(){var a=this.model.get("trackster_urls");if(!(this.model.hasData())||!(this.model.get("for_editing"))||!(a)){return null}this.tracksterButton=new IconButtonView({model:new IconButton({title:"View in Trackster",icon_class:"chart_curve"})});this.errButton.render();this.errButton.$el.addClass("trackster-add").attr({"data-url":a["data-url"],"action-url":a["action-url"],"new-url":a["new-url"]});return this.errButton.$el},_render_secondaryActionButtons:function(b){var c=$('<div style="float: right;"></div>'),a=this;_.each(b,function(d){c.append(d.call(a))});return c},_render_tagButton:function(){if(!(this.model.hasData())||!(this.model.get("for_editing"))||(!this.model.get("retag_url"))){return null}this.tagButton=new IconButtonView({model:new IconButton({title:"Edit dataset tags",target:"galaxy_main",href:this.model.get("retag_url"),icon_class:"tags"})});return this.tagButton.render().$el},_render_annotateButton:function(){if(!(this.model.hasData())||!(this.model.get("for_editing"))||(!this.model.get("annotate_url"))){return null}this.annotateButton=new IconButtonView({model:new IconButton({title:"Edit dataset annotation",target:"galaxy_main",href:this.model.get("annotate_url"),icon_class:"annotate"})});return this.annotateButton.render().$el},_render_tagArea:function(){if(this.model.get("retag_url")){return null}return $(HistoryItemView.templates.tagArea(this.model.toJSON()))},_render_annotationArea:function(){if(!this.model.get("annotate_url")){return null}return $(HistoryItemView.templates.annotationArea(this.model.toJSON()))},_render_displayApps:function(){if(!this.model.get("display_apps")){return null}var a=this.model.get("displayApps"),c=$("<div/>"),b=$("<span/>");this.log(this+"displayApps:",a);return c},_render_peek:function(){if(!this.model.get("peek")){return null}return $("<div/>").append($("<pre/>").attr("id","peek"+this.model.get("id")).addClass("peek").append(this.model.get("peek")))},_render_body_not_viewable:function(a){a.append($("<div>You do not have permission to view dataset.</div>"))},_render_body_uploading:function(a){a.append($("<div>Dataset is uploading</div>"))},_render_body_queued:function(a){a.append($("<div>Job is waiting to run.</div>"));a.append(this._render_primaryActionButtons([this._render_showParamsButton,this._render_rerunButton]))},_render_body_running:function(a){a.append("<div>Job is currently running.</div>");a.append(this._render_primaryActionButtons([this._render_showParamsButton,this._render_rerunButton]))},_render_body_error:function(a){if(!this.model.get("purged")){a.append($("<div>"+this.model.get("misc_blurb")+"</div>"))}a.append(("An error occurred running this job: <i>"+$.trim(this.model.get("misc_info"))+"</i>"));a.append(this._render_primaryActionButtons([this._render_downloadButton,this._render_errButton,this._render_showParamsButton,this._render_rerunButton]))},_render_body_discarded:function(a){a.append("<div>The job creating this dataset was cancelled before completion.</div>");a.append(this._render_primaryActionButtons([this._render_showParamsButton,this._render_rerunButton]))},_render_body_setting_metadata:function(a){a.append($("<div>Metadata is being auto-detected.</div>"))},_render_body_empty:function(a){a.append($("<div>No data: <i>"+this.model.get("misc_blurb")+"</i></div>"));a.append(this._render_primaryActionButtons([this._render_showParamsButton,this._render_rerunButton]))},_render_body_failed_metadata:function(a){a.append($(HistoryItemView.templates.failedMetadata(this.model.toJSON())));this._render_body_ok(a)},_render_body_ok:function(a){a.append(this._render_hdaSummary());a.append(this._render_primaryActionButtons([this._render_downloadButton,this._render_errButton,this._render_showParamsButton,this._render_rerunButton]));a.append(this._render_secondaryActionButtons([this._render_tagButton,this._render_annotateButton]));a.append('<div class="clear"/>');a.append(this._render_tagArea());a.append(this._render_annotationArea());a.append(this._render_displayApps());a.append(this._render_peek())},_render_body:function(){var b=this.model.get("state");var a=$("<div/>").attr("id","info-"+this.model.get("id")).addClass("historyItemBody").attr("style","display: block");switch(b){case HistoryItem.STATES.NOT_VIEWABLE:this._render_body_not_viewable(a);break;case HistoryItem.STATES.UPLOAD:this._render_body_uploading(a);break;case HistoryItem.STATES.QUEUED:this._render_body_queued(a);break;case HistoryItem.STATES.RUNNING:this._render_body_running(a);break;case HistoryItem.STATES.ERROR:this._render_body_error(a);break;case HistoryItem.STATES.DISCARDED:this._render_body_discarded(a);break;case HistoryItem.STATES.SETTING_METADATA:this._render_body_setting_metadata(a);break;case HistoryItem.STATES.EMPTY:this._render_body_empty(a);break;case HistoryItem.STATES.FAILED_METADATA:this._render_body_failed_metadata(a);break;case HistoryItem.STATES.OK:this._render_body_ok(a);break;default:a.append($('<div>Error: unknown dataset state "'+b+'".</div>'))}a.append('<div style="clear: both"></div>');if(this.model.get("bodyIsShown")===false){a.hide()}return a},events:{"click .historyItemTitle":"toggleBodyVisibility","click a.icon-button.tags":"loadAndDisplayTags","click a.icon-button.annotate":"loadAndDisplayAnnotation"},loadAndDisplayTags:function(b){this.log(this+".loadAndDisplayTags",b);var c=this.$el.find(".tag-area"),a=c.find(".tag-elt");if(c.is(":hidden")){if(!a.html()){$.ajax({url:this.model.get("ajax_get_tag_url"),error:function(){alert("Tagging failed")},success:function(d){a.html(d);a.find(".tooltip").tooltip();c.slideDown("fast")}})}else{c.slideDown("fast")}}else{c.slideUp("fast")}return false},loadAndDisplayAnnotation:function(b){this.log(this+".loadAndDisplayAnnotation",b);var d=this.$el.find(".annotation-area"),c=d.find(".annotation-elt"),a=this.model.get("ajax_set_annotation_url");if(d.is(":hidden")){if(!c.html()){$.ajax({url:this.model.get("ajax_get_annotation_url"),error:function(){alert("Annotations failed")},success:function(e){if(e===""){e="<em>Describe or add notes to dataset</em>"}c.html(e);d.find(".tooltip").tooltip();async_save_text(c.attr("id"),c.attr("id"),a,"new_annotation",18,true,4);d.slideDown("fast")}})}else{d.slideDown("fast")}}else{d.slideUp("fast")}return false},toggleBodyVisibility:function(){this.log(this+".toggleBodyVisibility");this.$el.find(".historyItemBody").toggle()},toString:function(){var a=(this.model)?(this.model+""):("");return"HistoryItemView("+a+")"}});HistoryItemView.templates=CompiledTemplateLoader.getTemplates({"common-templates.html":{warningMsg:"template-warningmessagesmall"},"history-templates.html":{messages:"template-history-warning-messages",titleLink:"template-history-titleLink",hdaSummary:"template-history-hdaSummary",failedMetadata:"template-history-failedMetaData",tagArea:"template-history-tagArea",annotationArea:"template-history-annotationArea"}});var HistoryCollection=Backbone.Collection.extend({model:HistoryItem,toString:function(){return("HistoryCollection()")}});var History=BaseModel.extend(LoggableMixin).extend({defaults:{id:"",name:"",state:"",state_details:{discarded:0,empty:0,error:0,failed_metadata:0,ok:0,queued:0,running:0,setting_metadata:0,upload:0}},initialize:function(b,a){this.log(this+".initialize",b,a);this.items=new HistoryCollection()},loadDatasetsAsHistoryItems:function(c){var a=this,b=this.get("id"),d=this.get("state_details");_.each(c,function(f,e){a.log("loading dataset: ",f,e);var h=new HistoryItem(_.extend(f,{history_id:b}));a.log("as History:",h);a.items.add(h);var g=f.state;d[g]+=1});this.set("state_details",d);this._stateFromStateDetails();return this},_stateFromStateDetails:function(){this.set("state","");var a=this.get("state_details");if((a.error>0)||(a.failed_metadata>0)){this.set("state",HistoryItem.STATES.ERROR)}else{if((a.running>0)||(a.setting_metadata>0)){this.set("state",HistoryItem.STATES.RUNNING)}else{if(a.queued>0){this.set("state",HistoryItem.STATES.QUEUED)}else{if(a.ok===this.items.length){this.set("state",HistoryItem.STATES.OK)}else{throw ("_stateFromStateDetails: unable to determine history state from state details: "+this.state_details)}}}}return this},toString:function(){var a=(this.get("name"))?(","+this.get("name")):("");return"History("+this.get("id")+a+")"}});var HistoryView=BaseView.extend(LoggableMixin).extend({el:"body.historyPage",initialize:function(){this.log(this+".initialize");this.itemViews=[];var a=this;this.model.items.each(function(c){var b=new HistoryItemView({model:c});a.itemViews.push(b)})},render:function(){this.log(this+".render");var a=$("<div/>");_.each(this.itemViews,function(b){a.prepend(b.render())});this.$el.append(a.children());a.remove()},toString:function(){var a=this.model.get("name")||"";return"HistoryView("+a+")"}});function createMockHistoryData(){mockHistory={};mockHistory.data={template:{id:"a799d38679e985db",name:"template",data_type:"fastq",file_size:226297533,genome_build:"?",metadata_data_lines:0,metadata_dbkey:"?",metadata_sequences:0,misc_blurb:"215.8 MB",misc_info:"uploaded fastq file (misc_info)",model_class:"HistoryDatasetAssociation",download_url:"",state:"ok",visible:true,deleted:false,purged:false,hid:0,for_editing:true,accessible:true,undelete_url:"",purge_url:"",unhide_url:"",display_url:"example.com/display",edit_url:"example.com/edit",delete_url:"example.com/delete",show_params_url:"example.com/show_params",rerun_url:"example.com/rerun",retag_url:"example.com/retag",annotate_url:"example.com/annotate",peek:['<table cellspacing="0" cellpadding="3"><tr><th>1.QNAME</th><th>2.FLAG</th><th>3.RNAME</th><th>4.POS</th><th>5.MAPQ</th><th>6.CIGAR</th><th>7.MRNM</th><th>8.MPOS</th><th>9.ISIZE</th><th>10.SEQ</th><th>11.QUAL</th><th>12.OPT</th></tr>','<tr><td colspan="100%">@SQ	SN:gi|87159884|ref|NC_007793.1|	LN:2872769</td></tr>','<tr><td colspan="100%">@PG	ID:bwa	PN:bwa	VN:0.5.9-r16</td></tr>','<tr><td colspan="100%">HWUSI-EAS664L:15:64HOJAAXX:1:1:13280:968	73	gi|87159884|ref|NC_007793.1|	2720169	37	101M	=	2720169	0	NAATATGACATTATTTTCAAAACAGCTGAAAATTTAGACGTACCGATTTATCTACATCCCGCGCCAGTTAACAGTGACATTTATCAATCATACTATAAAGG	!!!!!!!!!!$!!!$!!!!!$!!!!!!$!$!$$$!!$!!$!!!!!!!!!!!$!</td></tr>','<tr><td colspan="100%">!!!$!$!$$!!$$!!$!!!!!!!!!!!!!!!!!!!!!!!!!!$!!$!!	XT:A:U	NM:i:1	SM:i:37	AM:i:0	X0:i:1	X1:i:0	XM:i:1	XO:i:0	XG:i:0	MD:Z:0A100</td></tr>','<tr><td colspan="100%">HWUSI-EAS664L:15:64HOJAAXX:1:1:13280:968	133	gi|87159884|ref|NC_007793.1|	2720169	0	*	=	2720169	0	NAAACTGTGGCTTCGTTNNNNNNNNNNNNNNNGTGANNNNNNNNNNNNNNNNNNNGNNNNNNNNNNNNNNNNNNNNCNAANNNNNNNNNNNNNNNNNNNNN	!!!!!!!!!!!!$!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!</td></tr>','<tr><td colspan="100%">!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!</td></tr>',"</table>"].join("")}};_.extend(mockHistory.data,{notAccessible:_.extend(_.clone(mockHistory.data.template),{accessible:false}),deleted:_.extend(_.clone(mockHistory.data.template),{deleted:true,delete_url:"",purge_url:"example.com/purge",undelete_url:"example.com/undelete"}),purgedNotDeleted:_.extend(_.clone(mockHistory.data.template),{purged:true,delete_url:""}),notvisible:_.extend(_.clone(mockHistory.data.template),{visible:false,unhide_url:"example.com/unhide"}),hasDisplayApps:_.extend(_.clone(mockHistory.data.template),{display_apps:{"display in IGB":{Web:"/display_application/63cd3858d057a6d1/igb_bam/Web",Local:"/display_application/63cd3858d057a6d1/igb_bam/Local"}}}),canTrackster:_.extend(_.clone(mockHistory.data.template),{trackster_urls:{"data-url":"example.com/trackster-data","action-url":"example.com/trackster-action","new-url":"example.com/trackster-new"}}),zeroSize:_.extend(_.clone(mockHistory.data.template),{file_size:0}),hasMetafiles:_.extend(_.clone(mockHistory.data.template),{download_meta_urls:{bam_index:"example.com/bam-index"}}),upload:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.UPLOAD}),queued:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.QUEUED}),running:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.RUNNING}),empty:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.EMPTY}),error:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.ERROR,report_error_url:"example.com/report_err"}),discarded:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.DISCARDED}),setting_metadata:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.SETTING_METADATA}),failed_metadata:_.extend(_.clone(mockHistory.data.template),{state:HistoryItem.STATES.FAILED_METADATA})});$(document).ready(function(){mockHistory.items={};mockHistory.views={};for(key in mockHistory.data){mockHistory.items[key]=new HistoryItem(mockHistory.data[key]);mockHistory.items[key].set("name",key);mockHistory.views[key]=new HistoryItemView({model:mockHistory.items[key]});$("body").append(mockHistory.views[key].render())}})};