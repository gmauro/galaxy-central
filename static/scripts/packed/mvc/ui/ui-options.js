define(["utils/utils"],function(b){var a=Backbone.View.extend({initialize:function(g){this.optionsDefault={value:[],visible:true,data:[],id:b.uuid(),errorText:"No data available.",waitText:"Please wait..."};this.options=b.merge(g,this.optionsDefault);this.setElement('<div style="display: inline-block;"/>');this.$message=$("<div/>");this.$options=$(this._template(g));this.$el.append(this.$message);this.$el.append(this.$options);if(!this.options.visible){this.$el.hide()}this.update(this.options.data);if(this.options.value){this.value(this.options.value)}var f=this;this.on("change",function(){f._change()})},update:function(g){var j=this._getValue();this.$el.find(".ui-option").remove();for(var h in g){var i=$(this._templateOption(g[h]));i.addClass("ui-option");this.$options.append(i)}var f=this;this.$el.find("input").on("change",function(){f.value(f._getValue());f._change()});this._refresh();this.value(j)},exists:function(g){if(typeof g==="string"){g=[g]}for(var f in g){if(this.$el.find('input[value="'+g[f]+'"]').length>0){return true}}return false},first:function(){var f=this.$el.find("input");if(f.length>0){return f.val()}else{return undefined}},validate:function(){var g=this.value();if(!(g instanceof Array)){g=[g]}for(var f in g){if([null,"null",undefined].indexOf(g[f])>-1){return false}}return true},wait:function(){if(this._size()==0){this._messageShow(this.options.waitText,"info");this.$options.hide()}},unwait:function(){this._messageHide();this._refresh()},_change:function(){if(this.options.onchange){this.options.onchange(this._getValue())}},_refresh:function(){if(this._size()==0){this._messageShow(this.options.errorText,"danger");this.$options.hide()}else{this._messageHide();this.$options.css("display","inline-block")}},_getValue:function(){var g=this.$el.find(":checked");if(g.length==0){return"null"}if(this.options.multiple){var f=[];g.each(function(){f.push($(this).val())});return f}else{return g.val()}},_size:function(){return this.$el.find(".ui-option").length},_messageShow:function(g,f){this.$message.show();this.$message.removeClass();this.$message.addClass("ui-message alert alert-"+f);this.$message.html(g)},_messageHide:function(){this.$message.hide()}});var d={};d.View=a.extend({initialize:function(f){a.prototype.initialize.call(this,f)},value:function(f){if(typeof f==="string"){f=[f]}if(f!==undefined){this.$el.find("input").prop("checked",false);for(var g in f){this.$el.find('input[value="'+f[g]+'"]').prop("checked",true)}}return this._getValue()},_templateOption:function(f){return'<div><input type="radio" name="'+this.options.id+'" value="'+f.value+'"/>'+f.label+"<br></div>"},_template:function(){return'<div class="ui-options"/>'}});var c={};c.View=d.View.extend({initialize:function(f){f.multiple=true;d.View.prototype.initialize.call(this,f)},_templateOption:function(f){return'<div><input type="checkbox" name="'+this.options.id+'" value="'+f.value+'"/>'+f.label+"<br></div>"}});var e={};e.View=a.extend({initialize:function(f){a.prototype.initialize.call(this,f)},value:function(f){if(f!==undefined){this.$el.find("input").prop("checked",false);this.$el.find("label").removeClass("active");this.$el.find('[value="'+f+'"]').prop("checked",true).closest("label").addClass("active")}return this._getValue()},_templateOption:function(g){var f='<label class="btn btn-default">';if(g.icon){f+='<i class="fa '+g.icon+'"/>'}f+='<input type="radio" name="'+this.options.id+'" value="'+g.value+'">'+g.label+"</label>";return f},_template:function(){return'<div class="btn-group ui-radiobutton" data-toggle="buttons"/>'}});return{Radio:d,RadioButton:e,Checkbox:c}});