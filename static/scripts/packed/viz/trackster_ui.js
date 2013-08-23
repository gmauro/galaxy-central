define(["base","libs/underscore","viz/trackster/slotting","viz/trackster/painters","viz/trackster/tracks","viz/visualization"],function(a,f,e,c,d,h){var j=d.object_from_template;var b=function(l,k){if(!k){k={}}var m=new IconButtonCollection(f.map(l,function(n){return new IconButton(f.extend(n,k))}));return new IconButtonMenuView({collection:m})};var g=a.Base.extend({initialize:function(k){this.baseURL=k},createButtonMenu:function(){var k=this,l=b([{icon_class:"plus-button",title:"Add tracks",on_click:function(){h.select_datasets(galaxy_config.root+"visualization/list_current_history_datasets",galaxy_config.root+"api/datasets",{"f-dbkey":view.dbkey},function(m){f.each(m,function(n){view.add_drawable(j(n,view,view))})})}},{icon_class:"block--plus",title:"Add group",on_click:function(){view.add_drawable(new d.DrawableGroup(view,view,{name:"New Group"}))}},{icon_class:"bookmarks",title:"Bookmarks",on_click:function(){force_right_panel(($("div#right").css("right")=="0px"?"hide":"show"))}},{icon_class:"globe",title:"Circster",on_click:function(){window.location=k.baseURL+"visualization/circster?id="+view.vis_id}},{icon_class:"disk--arrow",title:"Save",on_click:function(){show_modal("Saving...","progress");var m=[];$(".bookmark").each(function(){m.push({position:$(this).children(".position").text(),annotation:$(this).children(".annotation").text()})});var n=(view.overview_drawable?view.overview_drawable.name:null),o={view:view.to_dict(),viewport:{chrom:view.chrom,start:view.low,end:view.high,overview:n},bookmarks:m};$.ajax({url:galaxy_config.root+"visualization/save",type:"POST",dataType:"json",data:{id:view.vis_id,title:view.name,dbkey:view.dbkey,type:"trackster",vis_json:JSON.stringify(o)}}).success(function(p){hide_modal();view.vis_id=p.vis_id;view.has_changes=false;window.history.pushState({},"",p.url+window.location.hash)}).error(function(){show_modal("Could Not Save","Could not save visualization. Please try again later.",{Close:hide_modal})})}}],{tooltip_config:{placement:"bottom"}});this.buttonMenu=l;return l},add_bookmarks:function(){var k=this,l=this.baseURL;show_modal("Select dataset for new bookmarks","progress");$.ajax({url:this.baseURL+"/visualization/list_histories",data:{"f-dbkey":view.dbkey},error:function(){alert("Grid failed")},success:function(m){show_modal("Select dataset for new bookmarks",m,{Cancel:function(){hide_modal()},Insert:function(){$("input[name=id]:checked,input[name=ldda_ids]:checked").first().each(function(){var n,o=$(this).val();if($(this).attr("name")==="id"){n={hda_id:o}}else{n={ldda_id:o}}$.ajax({url:this.baseURL+"/visualization/bookmarks_from_dataset",data:n,dataType:"json"}).then(function(p){for(i=0;i<p.data.length;i++){var q=p.data[i];k.add_bookmark(q[0],q[1])}})});hide_modal()}})}})},add_bookmark:function(o,m,k){var q=$("#right .unified-panel-body"),s=$("<div/>").addClass("bookmark").appendTo(q);var t=$("<div/>").addClass("position").appendTo(s),p=$("<a href=''/>").text(o).appendTo(t).click(function(){view.go_to(o);return false}),n=$("<div/>").text(m).appendTo(s);if(k){var r=$("<div/>").addClass("delete-icon-container").prependTo(s).click(function(){s.slideUp("fast");s.remove();view.has_changes=true;return false}),l=$("<a href=''/>").addClass("icon-button delete").appendTo(r);n.make_text_editable({num_rows:3,use_textarea:true,help_text:"Edit bookmark note"}).addClass("annotation")}view.has_changes=true;return s},create_visualization:function(p,k,o,q,n){var m=this,l=new d.TracksterView(p);l.editor=true;$.when(l.load_chroms_deferred).then(function(B){if(k){var z=k.chrom,r=k.start,w=k.end,t=k.overview;if(z&&(r!==undefined)&&w){l.change_chrom(z,r,w)}else{l.change_chrom(B[0].chrom)}}else{l.change_chrom(B[0].chrom)}if(o){var u,s,v;for(var x=0;x<o.length;x++){l.add_drawable(j(o[x],l,l))}}l.update_intro_div();var A;for(var x=0;x<l.drawables.length;x++){if(l.drawables[x].name===t){l.set_overview(l.drawables[x]);break}}if(q){var y;for(var x=0;x<q.length;x++){y=q[x];m.add_bookmark(y.position,y.annotation,n)}}l.has_changes=false});return l},init_keyboard_nav:function(k){$(document).keydown(function(l){if($(l.srcElement).is(":input")){return}switch(l.which){case 37:k.move_fraction(0.25);break;case 38:var m=Math.round(k.viewport_container.height()/15);k.viewport_container.scrollTop(k.viewport_container.scrollTop()-20);break;case 39:k.move_fraction(-0.25);break;case 40:var m=Math.round(k.viewport_container.height()/15);k.viewport_container.scrollTop(k.viewport_container.scrollTop()+20);break}})}});return{object_from_template:j,TracksterUI:g}});