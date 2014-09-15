define(["utils/utils","mvc/ui/ui-misc","mvc/ui/ui-tabs"],function(b,d,a){var c=Backbone.View.extend({initialize:function(k,f){var e=this;var h=k.datasets.filterType();var j=[];for(var g in h){j.push({label:h[g].get("name"),value:h[g].get("id")})}this.select=new d.Select.View({data:j,value:j[0].value,onchange:function(){e.trigger("change")}});this.select_multiple=new d.Select.View({multiple:true,data:j,value:j[0].value,onchange:function(){e.trigger("change")}});this.select_collection=new d.Select.View({data:j,value:j[0].value,onchange:function(){e.trigger("change")}});this.on("change",function(){if(f.onchange){f.onchange(e.value())}});this.tabs=new a.View({onchange:function(){e.trigger("change")}});this.tabs.add({id:"single",title:"Select a dataset",$el:this.select.$el});this.tabs.add({id:"multiple",title:"Select multiple datasets",$el:this.select_multiple.$el});this.tabs.add({id:"collection",title:"Select a dataset collection",$el:this.select_collection.$el});this.setElement(this.tabs.$el)},value:function(e){var f=this.tabs.current();switch(f){case"multiple":return this.select_multiple.value();case"collection":return this.select_collection.value();default:return this.select.value()}},update:function(e){this.select.update(e)}});return{View:c}});