define(["utils/utils","mvc/ui/ui-select-default","mvc/ui/ui-slider","mvc/ui/ui-checkbox","mvc/ui/ui-radiobutton","mvc/ui/ui-button-menu","mvc/ui/ui-modal"],function(l,b,f,e,m,q,n){var d=Backbone.View.extend({optionsDefault:{url:"",cls:""},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options))},_template:function(r){return'<img class="ui-image '+r.cls+'" src="'+r.url+'"/>'}});var k=Backbone.View.extend({optionsDefault:{title:"",cls:""},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options))},title:function(r){this.$el.html(r)},_template:function(r){return'<label class="ui-label '+r.cls+'">'+r.title+"</label>"},value:function(){return options.title}});var c=Backbone.View.extend({optionsDefault:{floating:"right",icon:"",tooltip:"",placement:"bottom",title:"",cls:""},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options));$(this.el).tooltip({title:r.tooltip,placement:"bottom"})},_template:function(r){return'<div><span class="fa '+r.icon+'" class="ui-icon"/>&nbsp;'+r.title+"</div>"}});var h=Backbone.View.extend({optionsDefault:{id:null,title:"",floating:"right",cls:"btn btn-default",icon:""},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options));$(this.el).on("click",r.onclick);$(this.el).tooltip({title:r.tooltip,placement:"bottom"})},_template:function(r){var s='<button id="'+r.id+'" type="submit" style="float: '+r.floating+';" type="button" class="ui-button '+r.cls+'">';if(r.icon){s+='<i class="icon fa '+r.icon+'"></i>&nbsp;'}s+=r.title+"</button>";return s}});var i=Backbone.View.extend({optionsDefault:{id:null,title:"",floating:"right",cls:"icon-btn",icon:"",tooltip:"",onclick:null},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options));$(this.el).on("click",r.onclick);$(this.el).tooltip({title:r.tooltip,placement:"bottom"})},_template:function(r){var s="";if(r.title){s="width: auto;"}var t='<div id="'+r.id+'" style="float: '+r.floating+"; "+s+'" class="ui-button-icon '+r.cls+'">';if(r.title){t+='<div class="button"><i class="icon fa '+r.icon+'"/>&nbsp;<span class="title">'+r.title+"</span></div>"}else{t+='<i class="icon fa '+r.icon+'"/>'}t+="</div>";return t}});var g=Backbone.View.extend({optionsDefault:{title:"",cls:""},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options));$(this.el).on("click",r.onclick)},_template:function(r){return'<div><a href="javascript:void(0)" class="ui-anchor '+r.cls+'">'+r.title+"</a></div>"}});var o=Backbone.View.extend({optionsDefault:{message:"",status:"info",persistent:false},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement("<div></div>")},update:function(s){this.options=l.merge(s,this.optionsDefault);if(s.message!=""){this.$el.html(this._template(this.options));this.$el.find(".alert").append(s.message);this.$el.fadeIn();if(!s.persistent){var r=this;window.setTimeout(function(){if(r.$el.is(":visible")){r.$el.fadeOut()}else{r.$el.hide()}},3000)}}else{this.$el.fadeOut()}},_template:function(r){return'<div class="ui-message alert alert-'+r.status+'"/>'}});var a=Backbone.View.extend({optionsDefault:{onclick:null,searchword:""},initialize:function(s){this.options=l.merge(s,this.optionsDefault);this.setElement(this._template(this.options));var r=this;if(this.options.onclick){this.$el.on("submit",function(u){var t=r.$el.find("#search");r.options.onclick(t.val())})}},_template:function(r){return'<div class="ui-search"><form onsubmit="return false;"><input id="search" class="form-control input-sm" type="text" name="search" placeholder="Search..." value="'+r.searchword+'"><button type="submit" class="btn search-btn"><i class="fa fa-search"></i></button></form></div>'}});var j=Backbone.View.extend({optionsDefault:{value:"",type:"text",placeholder:"",disabled:false,visible:true,cls:"",area:false},initialize:function(s){this.options=l.merge(s,this.optionsDefault);this.setElement(this._template(this.options));if(this.options.disabled){this.$el.prop("disabled",true)}if(!this.options.visible){this.$el.hide()}var r=this;this.$el.on("input",function(){if(r.options.onchange){r.options.onchange(r.$el.val())}})},value:function(r){if(r!==undefined){this.$el.val(r)}return this.$el.val()},_template:function(r){if(r.area){return'<textarea id="'+r.id+'" class="ui-textarea '+r.cls+'"></textarea>'}else{return'<input id="'+r.id+'" type="'+r.type+'" value="'+r.value+'" placeholder="'+r.placeholder+'" class="ui-input '+r.cls+'">'}}});var p=Backbone.View.extend({optionsDefault:{value:""},initialize:function(r){this.options=l.merge(r,this.optionsDefault);this.setElement(this._template(this.options))},value:function(r){if(r!==undefined){this.$el.val(r)}return this.$el.val()},_template:function(r){return'<hidden id="'+r.id+'" value="'+r.value+'"/>'}});return{Anchor:g,Button:h,ButtonIcon:i,ButtonMenu:q,Icon:c,Image:d,Input:j,Label:k,Message:o,Modal:n,RadioButton:m,Checkbox:e,Searchbox:a,Select:b,Hidden:p,Slider:f}});