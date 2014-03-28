define(["galaxy.masthead","mvc/base-mvc","utils/utils","libs/toastr","mvc/library/library-model","mvc/library/library-libraryrow-view"],function(c,h,e,f,d,a){var b=h.SessionStorageModel.extend({defaults:{with_deleted:false}});var g=Backbone.View.extend({el:"#libraries_element",events:{"click .edit_library_btn":"edit_button_event","click .save_library_btn":"save_library_modification","click .cancel_library_btn":"cancel_library_modification","click .delete_library_btn":"delete_library","click .undelete_library_btn":"undelete_library","click .sort-libraries-link":"sort_clicked"},modal:null,collection:null,preferences:null,rowViews:{},initialize:function(){var i=this;this.rowViews={};this.preferences=new b();this.collection=new d.Libraries();this.collection.fetch({success:function(j){i.render()},error:function(k,j){f.error("An error occured. Please try again.")}})},render:function(j){var k=this.templateLibraryList();var l=null;var i=this.preferences.get("with_deleted");var m=null;if(typeof j!=="undefined"){i=typeof j.with_deleted!=="undefined"?j.with_deleted:false;m=typeof j.models!=="undefined"?j.models:null}if(this.collection!==null&&m===null){if(i){l=this.collection.models}else{l=this.collection.where({deleted:false})}}else{if(m!==null){l=m}else{l=[]}}this.$el.html(k({length:l.length,order:this.collection.sort_order}));this.renderRows(l);$("#center [data-toggle]").tooltip();$("#center").css("overflow","auto")},renderRows:function(n){for(var m=0;m<n.length;m++){var l=n[m];var k=_.findWhere(this.rowViews,{id:l.get("id")});if(k!==undefined){this.$el.find("#library_list_body").append(k.el)}else{var j=new a.LibraryRowView(l);this.$el.find("#library_list_body").append(j.el);this.rowViews[l.get("id")]=j}}},sort_clicked:function(){if(this.collection.sort_order=="asc"){this.sortLibraries("name","desc")}else{this.sortLibraries("name","asc")}this.render()},sortLibraries:function(j,i){if(j==="name"){if(i==="asc"){this.collection.sort_order="asc";this.collection.comparator=function(l,k){if(l.get("name").toLowerCase()>k.get("name").toLowerCase()){return 1}if(k.get("name").toLowerCase()>l.get("name").toLowerCase()){return -1}return 0}}else{if(i==="desc"){this.collection.sort_order="desc";this.collection.comparator=function(l,k){if(l.get("name").toLowerCase()>k.get("name").toLowerCase()){return -1}if(k.get("name").toLowerCase()>l.get("name").toLowerCase()){return 1}return 0}}}this.collection.sort()}},templateLibraryList:function(){tmpl_array=[];tmpl_array.push('<div class="library_container table-responsive">');tmpl_array.push("<% if(length === 0) { %>");tmpl_array.push("<div>I see no libraries. Why don't you create one?</div>");tmpl_array.push("<% } else{ %>");tmpl_array.push('<table class="grid table table-condensed">');tmpl_array.push("   <thead>");tmpl_array.push('     <th style="width:30%;"><a class="sort-libraries-link" title="Click to reverse order" href="#">name</a> <span title="Sorted alphabetically" class="fa fa-sort-alpha-<%- order %>"></span></th>');tmpl_array.push('     <th style="width:22%;">description</th>');tmpl_array.push('     <th style="width:22%;">synopsis</th> ');tmpl_array.push('     <th style="width:26%;"></th> ');tmpl_array.push("   </thead>");tmpl_array.push('   <tbody id="library_list_body">');tmpl_array.push("   </tbody>");tmpl_array.push("</table>");tmpl_array.push("<% }%>");tmpl_array.push("</div>");return _.template(tmpl_array.join(""))},templateNewLibraryInModal:function(){tmpl_array=[];tmpl_array.push('<div id="new_library_modal">');tmpl_array.push("   <form>");tmpl_array.push('       <input type="text" name="Name" value="" placeholder="Name">');tmpl_array.push('       <input type="text" name="Description" value="" placeholder="Description">');tmpl_array.push('       <input type="text" name="Synopsis" value="" placeholder="Synopsis">');tmpl_array.push("   </form>");tmpl_array.push("</div>");return tmpl_array.join("")},save_library_modification:function(l){var k=$(l.target).closest("tr");var i=this.collection.get(k.data("id"));var j=false;var n=k.find(".input_library_name").val();if(typeof n!=="undefined"&&n!==i.get("name")){if(n.length>2){i.set("name",n);j=true}else{f.warning("Library name has to be at least 3 characters long");return}}var m=k.find(".input_library_description").val();if(typeof m!=="undefined"&&m!==i.get("description")){i.set("description",m);j=true}var o=k.find(".input_library_synopsis").val();if(typeof o!=="undefined"&&o!==i.get("synopsis")){i.set("synopsis",o);j=true}if(j){i.save(null,{patch:true,success:function(p){f.success("Changes to library saved");galaxyLibraryview.toggle_library_modification(k)},error:function(q,p){f.error("An error occured during updating the library :(")}})}},edit_button_event:function(i){this.toggle_library_modification($(i.target).closest("tr"))},toggle_library_modification:function(l){var i=this.collection.get(l.data("id"));l.find(".public_lib_ico").toggle();l.find(".deleted_lib_ico").toggle();l.find(".edit_library_btn").toggle();l.find(".upload_library_btn").toggle();l.find(".permission_library_btn").toggle();l.find(".save_library_btn").toggle();l.find(".cancel_library_btn").toggle();if(i.get("deleted")){}else{l.find(".delete_library_btn").toggle()}if(l.find(".edit_library_btn").is(":hidden")){var j=i.get("name");var n='<input type="text" class="form-control input_library_name" placeholder="name">';l.children("td").eq(0).html(n);if(typeof j!==undefined){l.find(".input_library_name").val(j)}var k=i.get("description");var n='<input type="text" class="form-control input_library_description" placeholder="description">';l.children("td").eq(1).html(n);if(typeof k!==undefined){l.find(".input_library_description").val(k)}var m=i.get("synopsis");var n='<input type="text" class="form-control input_library_synopsis" placeholder="synopsis">';l.children("td").eq(2).html(n);if(typeof m!==undefined){l.find(".input_library_synopsis").val(m)}}else{l.children("td").eq(0).html(i.get("name"));l.children("td").eq(1).html(i.get("description"));l.children("td").eq(2).html(i.get("synopsis"))}},cancel_library_modification:function(k){var j=$(k.target).closest("tr");var i=this.collection.get(j.data("id"));this.toggle_library_modification(j);j.children("td").eq(0).html(i.get("name"));j.children("td").eq(1).html(i.get("description"));j.children("td").eq(2).html(i.get("synopsis"))},undelete_library:function(k){var j=$(k.target).closest("tr");var i=this.collection.get(j.data("id"));this.toggle_library_modification(j);i.url=i.urlRoot+i.id+"?undelete=true";i.destroy({success:function(l){l.set("deleted",false);galaxyLibraryview.collection.add(l);j.removeClass("active");f.success("Library has been undeleted")},error:function(){f.error("An error occured while undeleting the library :(")}})},delete_library:function(k){var j=$(k.target).closest("tr");var i=this.collection.get(j.data("id"));this.toggle_library_modification(j);i.destroy({success:function(l){j.remove();l.set("deleted",true);galaxyLibraryview.collection.add(l);f.success("Library has been marked deleted")},error:function(){f.error("An error occured during deleting the library :(")}})},redirectToHome:function(){window.location="../"},redirectToLogin:function(){window.location="/user/login"},show_library_modal:function(j){j.preventDefault();j.stopPropagation();var i=this;this.modal=Galaxy.modal;this.modal.show({closing_events:true,title:"Create New Library",body:this.templateNewLibraryInModal(),buttons:{Create:function(){i.create_new_library_event()},Close:function(){i.modal.hide()}}})},create_new_library_event:function(){var k=this.serialize_new_library();if(this.validate_new_library(k)){var j=new d.Library();var i=this;j.save(k,{success:function(l){i.collection.add(l);i.modal.hide();i.clear_library_modal();i.render();f.success("Library created")},error:function(){f.error("An error occured :(")}})}else{f.error("Library's name is missing")}return false},clear_library_modal:function(){$("input[name='Name']").val("");$("input[name='Description']").val("");$("input[name='Synopsis']").val("")},serialize_new_library:function(){return{name:$("input[name='Name']").val(),description:$("input[name='Description']").val(),synopsis:$("input[name='Synopsis']").val()}},validate_new_library:function(i){return i.name!==""}});return{LibraryListView:g}});