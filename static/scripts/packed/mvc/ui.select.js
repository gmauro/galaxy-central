define(["utils/utils"],function(a){var b=Backbone.View.extend({optionsDefault:{css:"",placeholder:"No data available",data:[]},initialize:function(d){this.options=a.merge(d,this.optionsDefault);this.setElement(this._template(this.options));this.options.container.append(this.$el);this.select_data=this.options.data;this._refresh();if(this.options.value){this._setValue(this.options.value)}var c=this;if(this.options.onchange){this.$el.on("change",function(){c.options.onchange(c.value())})}},value:function(c){var d=this._getValue();if(c!==undefined){this._setValue(c)}var e=this._getValue();if(e===undefined){return null}else{if((e!=d&&this.options.onchange)){this.options.onchange(e)}return e}},text:function(){return this.$el.select2("data").text},disabled:function(){return !this.$el.select2("enable")},enable:function(){this.$el.select2("enable",true)},disable:function(){this.$el.select2("enable",false)},add:function(c){this.select_data.push({id:c.id,text:c.text});this._refresh()},remove:function(d){var c=this._getIndex(d);if(c!=-1){this.select_data.splice(c,1);this._refresh()}},update:function(c){this.select_data=[];for(var d in c.data){this.select_data.push(c.data[d])}this._refresh()},_refresh:function(){var e=this.select_data;if(!e||e.length==0){e=[]}var d=this._getValue();this.$el.select2({data:e,containerCssClass:this.options.css,placeholder:this.options.placeholder});var c=this._getIndex(d);if(c!=-1){this._setValue(d)}},_getIndex:function(d){for(var c in this.select_data){if(this.select_data[c].id==d){return c}}return -1},_getValue:function(){return this.$el.select2("val")},_setValue:function(c){this.$el.select2("val",c)},_template:function(c){return'<input type="hidden"/>'}});return{View:b}});