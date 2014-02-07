define(["galaxy.modal","utils/utils","mvc/upload/upload-button","mvc/upload/upload-model","mvc/upload/upload-row","mvc/upload/upload-ftp","mvc/ui.popover","mvc/ui","utils/uploadbox"],function(a,f,e,c,b,g,d){return Backbone.View.extend({options:{nginx_upload_path:""},modal:null,ui_button:null,uploadbox:null,current_history:null,upload_size:0,select_extension:[["Auto-detect","auto"]],select_genome:[["Unspecified (?)","?"]],collection:new c.Collection(),ftp:null,counter:{announce:0,success:0,error:0,running:0,reset:function(){this.announce=this.success=this.error=this.running=0}},initialize:function(i){var h=this;if(!Galaxy.currHistoryPanel||!Galaxy.currHistoryPanel.model){window.setTimeout(function(){h.initialize()},500);return}if(!Galaxy.currUser.get("id")){return}this.ui_button=new e.Model({icon:"fa-upload",tooltip:"Download from URL or upload files from disk",label:"Load Data",onclick:function(j){if(j){h._eventShow(j)}},onunload:function(){if(h.counter.running>0){return"Several uploads are still processing."}}});$("#left .unified-panel-header-inner").append((new e.View(this.ui_button)).$el);var h=this;f.jsonFromUrl(galaxy_config.root+"api/datatypes",function(j){for(key in j){h.select_extension.push([j[key],j[key]])}});f.jsonFromUrl(galaxy_config.root+"api/genomes",function(j){var k=h.select_genome[0];h.select_genome=[];for(key in j){if(j[key].length>1){if(j[key][1]!==k[1]){h.select_genome.push(j[key])}}}h.select_genome.sort(function(m,l){return m[0]>l[0]?1:m[0]<l[0]?-1:0});h.select_genome.unshift(k)});if(i){this.options=_.defaults(i,this.options)}this.collection.on("remove",function(j){h._eventRemove(j)});this.collection.on("change:genome",function(k){var j=k.get("genome");h.collection.each(function(l){if(l.get("status")=="init"&&l.get("genome")=="?"){l.set("genome",j)}})})},_eventShow:function(j){j.preventDefault();if(!this.modal){var h=this;this.modal=new a.GalaxyModal({title:"Download data directly from web or upload files from your disk",body:this._template("upload-box","upload-info"),buttons:{"Choose local file":function(){h.uploadbox.select()},"Choose FTP file":function(){h._eventFtp()},"Create new file":function(){h._eventCreate()},Start:function(){h._eventStart()},Pause:function(){h._eventStop()},Reset:function(){h._eventReset()},Close:function(){h.modal.hide()},},height:"400",width:"900",closing_events:true});this.setElement("#upload-box");var h=this;this.uploadbox=this.$el.uploadbox({announce:function(k,l,m){h._eventAnnounce(k,l,m)},initialize:function(k,l,m){return h._eventInitialize(k,l,m)},progress:function(k,l,m){h._eventProgress(k,l,m)},success:function(k,l,m){h._eventSuccess(k,l,m)},error:function(k,l,m){h._eventError(k,l,m)},complete:function(){h._eventComplete()}});this._updateScreen();if(this.options.ftp_upload_dir&&this.options.ftp_upload_site){var i=this.modal.getButton("Choose FTP file");this.ftp=new d.View({title:"FTP files",container:i})}else{this.modal.hideButton("Choose FTP file")}}this.modal.show()},_eventRemove:function(i){var h=i.get("status");if(h=="success"){this.counter.success--}else{if(h=="error"){this.counter.error--}else{this.counter.announce--}}this._updateScreen();this.uploadbox.remove(i.id)},_eventAnnounce:function(h,i,k){this.counter.announce++;this._updateScreen();var j=new b(this,{id:h,file_name:i.name,file_size:i.size,file_mode:i.mode,file_path:i.path});this.collection.add(j.model);$(this.el).find("tbody:first").append(j.$el);j.render()},_eventInitialize:function(m,j,s){var k=this.collection.get(m);k.set("status","running");var o=k.get("file_name");var n=k.get("file_path");var h=k.get("file_mode");var p=k.get("extension");var r=k.get("genome");var q=k.get("url_paste");var l=k.get("space_to_tabs");var i=k.get("to_posix_lines");if(!q&&!(j.size>0)){return null}this.uploadbox.configure({url:this.options.nginx_upload_path});if(h=="ftp"){this.uploadbox.configure({paramname:""})}else{this.uploadbox.configure({paramname:"files_0|file_data"})}tool_input={};tool_input.dbkey=r;tool_input.file_type=p;tool_input["files_0|type"]="upload_dataset";tool_input["files_0|url_paste"]=q;tool_input["files_0|ftp_files"]=n;tool_input.space_to_tabs=l;tool_input.to_posix_lines=i;data={};data.history_id=this.current_history;data.tool_id="upload1";data.inputs=JSON.stringify(tool_input);return data},_eventProgress:function(i,j,h){var k=this.collection.get(i);k.set("percentage",h);this.ui_button.set("percentage",this._upload_percentage(h,j.size))},_eventSuccess:function(i,j,l){var k=this.collection.get(i);k.set("status","success");var h=k.get("file_size");this.ui_button.set("percentage",this._upload_percentage(100,h));this.upload_completed+=h*100;this.counter.announce--;this.counter.success++;this._updateScreen();Galaxy.currHistoryPanel.refreshHdas()},_eventError:function(h,i,k){var j=this.collection.get(h);j.set("status","error");j.set("info",k);this.ui_button.set("percentage",this._upload_percentage(100,i.size));this.ui_button.set("status","danger");this.upload_completed+=i.size*100;this.counter.announce--;this.counter.error++;this._updateScreen()},_eventComplete:function(){this.collection.each(function(h){if(h.get("status")=="queued"){h.set("status","init")}});this.counter.running=0;this._updateScreen()},_eventFtp:function(){if(!this.ftp.visible){this.ftp.empty();this.ftp.append((new g(this)).$el);this.ftp.show()}else{this.ftp.hide()}},_eventCreate:function(){this.uploadbox.add([{name:"New File",size:0,mode:"new"}])},_eventStart:function(){if(this.counter.announce==0||this.counter.running>0){return}var h=this;this.upload_size=0;this.upload_completed=0;this.collection.each(function(i){if(i.get("status")=="init"){i.set("status","queued");h.upload_size+=i.get("file_size")}});this.ui_button.set("percentage",0);this.ui_button.set("status","success");this.current_history=Galaxy.currHistoryPanel.model.get("id");this.counter.running=this.counter.announce;this._updateScreen();this.uploadbox.start()},_eventStop:function(){if(this.counter.running==0){return}this.ui_button.set("status","info");this.uploadbox.stop();$("#upload-info").html("Queue will pause after completing the current file...")},_eventReset:function(){if(this.counter.running==0){this.collection.reset();this.counter.reset();this._updateScreen();this.uploadbox.reset();this.ui_button.set("percentage",0)}},_updateScreen:function(){if(this.counter.announce==0){if(this.uploadbox.compatible()){message="You can Drag & Drop files into this box."}else{message="Unfortunately, your browser does not support multiple file uploads or drag&drop.<br>Some supported browsers are: Firefox 4+, Chrome 7+, IE 10+, Opera 12+ or Safari 6+."}}else{if(this.counter.running==0){message="You added "+this.counter.announce+" file(s) to the queue. Add more files or click 'Start' to proceed."}else{message="Please wait..."+this.counter.announce+" out of "+this.counter.running+" remaining."}}$("#upload-info").html(message);if(this.counter.running==0&&this.counter.announce+this.counter.success+this.counter.error>0){this.modal.enableButton("Reset")}else{this.modal.disableButton("Reset")}if(this.counter.running==0&&this.counter.announce>0){this.modal.enableButton("Start")}else{this.modal.disableButton("Start")}if(this.counter.running>0){this.modal.enableButton("Pause")}else{this.modal.disableButton("Pause")}if(this.counter.running==0){this.modal.enableButton("Choose local file");this.modal.enableButton("Choose FTP file");this.modal.enableButton("Create new file")}else{this.modal.disableButton("Choose local file");this.modal.disableButton("Choose FTP file");this.modal.disableButton("Create new file")}if(this.counter.announce+this.counter.success+this.counter.error>0){$(this.el).find("#upload-table").show()}else{$(this.el).find("#upload-table").hide()}},_upload_percentage:function(h,i){return(this.upload_completed+(h*i))/this.upload_size},_template:function(i,h){return'<div id="'+i+'" class="upload-box"><table id="upload-table" class="table table-striped" style="display: none;"><thead><tr><th>Name</th><th>Size</th><th>Type</th><th>Genome</th><th>Settings</th><th>Status</th><th></th></tr></thead><tbody></tbody></table></div><h6 id="'+h+'" class="upload-info"></h6>'}})});