var library_router=null;define(["galaxy.masthead","utils/utils","libs/toastr","mvc/library/library-model","mvc/library/library-folderlist-view","mvc/library/library-librarylist-view","mvc/library/library-librarytoolbar-view"],function(e,c,g,h,a,f,d){var i=Backbone.Router.extend({routes:{"":"libraries","sort/:sort_by/:order":"sort_libraries","folders/:id":"folder_content","folders/:folder_id/download/:format":"download"}});var b=Backbone.View.extend({initialize:function(){toolbarView=new d.ToolbarView();galaxyLibraryview=new f.GalaxyLibraryview();library_router=new i();folderContentView=null;library_router.on("route:libraries",function(){toolbarView=new d.ToolbarView();galaxyLibraryview=new f.GalaxyLibraryview()});library_router.on("route:sort_libraries",function(k,j){galaxyLibraryview.sortLibraries(k,j);galaxyLibraryview.render()});library_router.on("route:folder_content",function(j){if(!folderContentView){folderContentView=new a.FolderContentView()}folderContentView.render({id:j})});library_router.on("route:download",function(j,k){if($("#center").find(":checked").length===0){library_router.navigate("folders/"+j,{trigger:true,replace:true})}else{folderContentView.download(j,k);library_router.navigate("folders/"+j,{trigger:false,replace:true})}});Backbone.history.start({pushState:false})}});return{GalaxyApp:b}});