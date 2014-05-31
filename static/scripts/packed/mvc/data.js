define(["mvc/ui/ui-modal","mvc/ui/ui-frames"],function(j,i){var g=Backbone.Model.extend({});var b=Backbone.Model.extend({defaults:{id:"",type:"",name:"",hda_ldda:"hda",metadata:null},initialize:function(){this._set_metadata();this.on("change",this._set_metadata,this)},_set_metadata:function(){var m=new g();_.each(_.keys(this.attributes),function(n){if(n.indexOf("metadata_")===0){var o=n.split("metadata_")[1];m.set(o,this.attributes[n]);delete this.attributes[n]}},this);this.set("metadata",m,{silent:true})},get_metadata:function(m){return this.attributes.metadata.get(m)},urlRoot:galaxy_config.root+"api/datasets"});var h=b.extend({defaults:_.extend({},b.prototype.defaults,{chunk_url:null,first_data_chunk:null,chunk_index:-1,at_eof:false}),initialize:function(m){b.prototype.initialize.call(this);this.attributes.chunk_index=(this.attributes.first_data_chunk?1:0);this.attributes.chunk_url=galaxy_config.root+"dataset/display?dataset_id="+this.id;this.attributes.url_viz=galaxy_config.root+"visualization"},get_next_chunk:function(){if(this.attributes.at_eof){return null}var m=this,n=$.Deferred();$.getJSON(this.attributes.chunk_url,{chunk:m.attributes.chunk_index++}).success(function(o){var p;if(o.ck_data!==""){p=o}else{m.attributes.at_eof=true;p=null}n.resolve(p)});return n}});var e=Backbone.Collection.extend({model:b});var a=Backbone.View.extend({initialize:function(m){this.row_count=0;this.header_color="#AAA";this.dark_row_color="#DDD";new d({model:m.model,$el:this.$el})},render:function(){var s=$("<div/>").attr("id","loading_indicator");this.$el.append(s);var q=$("<table/>").attr({id:"content_table",cellpadding:0});this.$el.append(q);var m=this.model.get_metadata("column_names"),r=$("<tr/>").css("background-color",this.header_color).appendTo(q);if(m){r.append("<th>"+m.join("</th><th>")+"</th>")}var o=this,n=this.model.get("first_data_chunk");if(n){this._renderChunk(n)}else{$.when(o.model.get_next_chunk()).then(function(t){o._renderChunk(t)})}var p=false;this.scroll_elt.scroll(function(){if(!p&&o.scrolled_to_bottom()){p=true;s.show();$.when(o.model.get_next_chunk()).then(function(t){if(t){o._renderChunk(t);p=false;s.hide()}})}})},scrolled_to_bottom:function(){return false},_renderCell:function(p,m,q){var n=$("<td>").text(p);var o=this.model.get_metadata("column_types");if(q!==undefined){n.attr("colspan",q).addClass("stringalign")}else{if(o){if(m<o.length){if(o[m]==="str"||o[m]==="list"){n.addClass("stringalign")}}}}return n},_renderRow:function(m){var n=m.split("\t"),p=$("<tr>"),o=this.model.get_metadata("columns");if(this.row_count%2!==0){p.css("background-color",this.dark_row_color)}if(n.length===o){_.each(n,function(r,q){p.append(this._renderCell(r,q))},this)}else{if(n.length>o){_.each(n.slice(0,o-1),function(r,q){p.append(this._renderCell(r,q))},this);p.append(this._renderCell(n.slice(o-1).join("\t"),o-1))}else{if(o>5&&n.length===o-1){_.each(n,function(r,q){p.append(this._renderCell(r,q))},this);p.append($("<td>"))}else{p.append(this._renderCell(m,0,o))}}}this.row_count++;return p},_renderChunk:function(m){var n=this.$el.find("table");_.each(m.ck_data.split("\n"),function(o,p){n.append(this._renderRow(o))},this)}});var f=a.extend({initialize:function(m){a.prototype.initialize.call(this,m);scroll_elt=_.find(this.$el.parents(),function(n){return $(n).css("overflow")==="auto"});if(!scroll_elt){scroll_elt=window}this.scroll_elt=$(scroll_elt)},scrolled_to_bottom:function(){return(this.$el.height()-this.scroll_elt.scrollTop()-this.scroll_elt.height()<=0)}});var l=a.extend({initialize:function(m){a.prototype.initialize.call(this,m);this.scroll_elt=this.$el.css({position:"relative",overflow:"scroll",height:this.options.height||"500px"})},scrolled_to_bottom:function(){return this.$el.scrollTop()+this.$el.innerHeight()>=this.el.scrollHeight}});var d=Backbone.View.extend({col:{chrom:null,start:null,end:null},url_viz:null,dataset_id:null,genome_build:null,data_type:null,initialize:function(o){var r=parent.Galaxy;if(r&&r.modal){this.modal=r.modal}if(r&&r.frame){this.frame=r.frame}if(!this.modal||!this.frame){return}var n=o.model;var q=n.get("metadata");if(!n.get("data_type")){return}this.data_type=n.get("data_type");if(this.data_type=="bed"){if(q.get("chromCol")&&q.get("startCol")&&q.get("endCol")){this.col.chrom=q.get("chromCol")-1;this.col.start=q.get("startCol")-1;this.col.end=q.get("endCol")-1}else{console.log("TabularButtonTrackster : Bed-file metadata incomplete.");return}}if(this.data_type=="vcf"){function p(t,u){for(var s=0;s<u.length;s++){if(u[s].match(t)){return s}}return -1}this.col.chrom=p("Chrom",q.get("column_names"));this.col.start=p("Pos",q.get("column_names"));this.col.end=null;if(this.col.chrom==-1||this.col.start==-1){console.log("TabularButtonTrackster : VCF-file metadata incomplete.");return}}if(this.col.chrom===undefined){return}if(n.id){this.dataset_id=n.id}else{console.log("TabularButtonTrackster : Dataset identification is missing.");return}if(n.get("url_viz")){this.url_viz=n.get("url_viz")}else{console.log("TabularButtonTrackster : Url for visualization controller is missing.");return}if(n.get("genome_build")){this.genome_build=n.get("genome_build")}var m=new IconButtonView({model:new IconButton({title:"Visualize",icon_class:"chart_curve",id:"btn_viz"})});this.setElement(o.$el);this.$el.append(m.render().$el);this.hide()},events:{"mouseover tr":"show",mouseleave:"hide"},show:function(r){function q(w){return !isNaN(parseFloat(w))&&isFinite(w)}if(this.col.chrom===null){return}var v=$(r.target).parent();var s=v.children().eq(this.col.chrom).html();var m=v.children().eq(this.col.start).html();var o=this.col.end?v.children().eq(this.col.end).html():m;if(!s.match("^#")&&s!==""&&q(m)){var u={dataset_id:this.dataset_id,gene_region:s+":"+m+"-"+o};var p=v.offset();var n=p.left-10;var t=p.top-$(window).scrollTop()+3;$("#btn_viz").css({position:"fixed",top:t+"px",left:n+"px"});$("#btn_viz").off("click");$("#btn_viz").click(this.create_trackster_action(this.url_viz,u,this.genome_build));$("#btn_viz").show()}else{$("#btn_viz").hide()}},hide:function(){this.$el.find("#btn_viz").hide()},create_trackster_action:function(m,p,o){var n=this;return function(){var q={};if(o){q["f-dbkey"]=o}$.ajax({url:m+"/list_tracks?"+$.param(q),dataType:"html",error:function(){n.modal.show({title:"Something went wrong!",body:"Unfortunately we could not add this dataset to the track browser. Please try again or contact us.",buttons:{Cancel:function(){n.modal.hide()}}})},success:function(r){n.modal.show({title:"View Data in a New or Saved Visualization",buttons:{Cancel:function(){n.modal.hide()},"View in saved visualization":function(){n.modal.show({title:"Add Data to Saved Visualization",body:r,buttons:{Cancel:function(){n.modal.hide()},"Add to visualization":function(){n.modal.hide();n.modal.$el.find("input[name=id]:checked").each(function(){var s=$(this).val();p.id=s;n.frame.add({title:"Trackster",type:"url",content:m+"/trackster?"+$.param(p)})})}}})},"View in new visualization":function(){n.modal.hide();n.frame.add({title:"Trackster",type:"url",content:m+"/trackster?"+$.param(p)})}}})}});return false}}});var k=function(p,n,q,m){var o=new n({model:new p(q)});o.render();if(m){m.append(o.$el)}return o};var c=function(o){if(!o.model){o.model=new h(o.dataset_config)}var n=o.parent_elt;var p=o.embedded;delete o.embedded;delete o.parent_elt;delete o.dataset_config;var m=(p?new l(o):new f(o));m.render();if(n){n.append(m.$el)}return m};return{Dataset:b,TabularDataset:h,DatasetCollection:e,TabularDatasetChunkedView:a,createTabularDatasetChunkedView:c}});