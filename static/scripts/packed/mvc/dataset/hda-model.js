var HistoryDatasetAssociation=BaseModel.extend(LoggableMixin).extend({defaults:{history_id:null,model_class:"HistoryDatasetAssociation",hid:0,id:null,name:"",state:"",data_type:null,file_size:0,meta_files:[],misc_blurb:"",misc_info:"",deleted:false,purged:false,visible:false,accessible:false},url:function(){return"api/histories/"+this.get("history_id")+"/contents/"+this.get("id")},initialize:function(){this.log(this+".initialize",this.attributes);this.log("\tparent history_id: "+this.get("history_id"));if(!this.get("accessible")){this.set("state",HistoryDatasetAssociation.STATES.NOT_VIEWABLE)}this.on("change:state",function(b,a){this.log(this+" has changed state:",b,a);if(this.inReadyState()){this.trigger("state:ready",this.get("id"),a,this.previous("state"),b)}})},isDeletedOrPurged:function(){return(this.get("deleted")||this.get("purged"))},isVisible:function(b,c){var a=true;if((!b)&&(this.get("deleted")||this.get("purged"))){a=false}if((!c)&&(!this.get("visible"))){a=false}return a},inReadyState:function(){var a=this.get("state");return((a===HistoryDatasetAssociation.STATES.NEW)||(a===HistoryDatasetAssociation.STATES.OK)||(a===HistoryDatasetAssociation.STATES.EMPTY)||(a===HistoryDatasetAssociation.STATES.FAILED_METADATA)||(a===HistoryDatasetAssociation.STATES.NOT_VIEWABLE)||(a===HistoryDatasetAssociation.STATES.DISCARDED)||(a===HistoryDatasetAssociation.STATES.ERROR))},hasData:function(){return(this.get("file_size")>0)},toString:function(){var a=this.get("id")||"";if(this.get("name")){a+=':"'+this.get("name")+'"'}return"HistoryDatasetAssociation("+a+")"}});HistoryDatasetAssociation.STATES={UPLOAD:"upload",QUEUED:"queued",RUNNING:"running",SETTING_METADATA:"setting_metadata",NEW:"new",OK:"ok",EMPTY:"empty",FAILED_METADATA:"failed_metadata",NOT_VIEWABLE:"noPermission",DISCARDED:"discarded",ERROR:"error"};var HDACollection=Backbone.Collection.extend(LoggableMixin).extend({model:HistoryDatasetAssociation,initialize:function(){},ids:function(){return this.map(function(a){return a.id})},getVisible:function(a,b){return this.filter(function(c){return c.isVisible(a,b)})},getStateLists:function(){var a={};_.each(_.values(HistoryDatasetAssociation.STATES),function(b){a[b]=[]});this.each(function(b){a[b.get("state")].push(b.get("id"))});return a},running:function(){var a=[];this.each(function(b){if(!b.inReadyState()){a.push(b.get("id"))}});return a},update:function(a){this.log(this+"update:",a);if(!(a&&a.length)){return}var b=this;_.each(a,function(e,c){var d=b.get(e);d.fetch()})},toString:function(){return("HDACollection("+this.ids().join(",")+")")}});