define(["libs/underscore","viz/trackster/util","utils/config"],function(c,f,b){var d=Backbone.Model.extend({initialize:function(g){var h=this.get("key");this.set("id",h);var i=c.find(d.known_settings_defaults,function(j){return j.key===h});if(i){this.set(c.extend({},i,g))}if(this.get("value")===undefined){this.set_value(this.get("default_value"));if(!this.get("value")&&this.get("type")==="color"){this.set("value",f.get_random_color())}}},set_value:function(h){var g=this.get("type");if(g==="float"){h=parseFloat(h)}else{if(g==="int"){h=parseInt(h,10)}}this.set("value",h)}},{known_settings_defaults:[{key:"name",label:"Name",type:"text",default_value:""},{key:"color",label:"Color",type:"color",default_value:null},{key:"min_value",label:"Min Value",type:"float",default_value:null},{key:"max_value",label:"Max Value",type:"float",default_value:null},{key:"mode",type:"string",default_value:this.mode,hidden:true},{key:"height",type:"int",default_value:32,hidden:true},{key:"pos_color",label:"Positive Color",type:"color",default_value:"#FF8C00"},{key:"neg_color",label:"Negative Color",type:"color",default_value:"#4169E1"},{key:"block_color",label:"Block color",type:"color",default_value:null},{key:"label_color",label:"Label color",type:"color",default_value:"black"},{key:"show_insertions",label:"Show insertions",type:"bool",default_value:false},{key:"show_counts",label:"Show summary counts",type:"bool",default_value:true},{key:"mode",type:"string",default_value:this.mode,hidden:true},{key:"reverse_strand_color",label:"Antisense strand color",type:"color",default_value:null},{key:"show_differences",label:"Show differences only",type:"bool",default_value:true},{key:"mode",type:"string",default_value:this.mode,hidden:true}]});var e=Backbone.Collection.extend({model:d,to_key_value_dict:function(){var g={};this.each(function(h){g[h.get("key")]=h.get("value")});return g},get_value:function(g){var h=this.get(g);if(h){return h.get("value")}return undefined},set_value:function(g,i){var h=this.get(g);if(h){return h.set_value(i)}return undefined},set_default_value:function(h,g){var i=this.get(h);if(i){return i.set("default_value",g)}return undefined}},{from_models_and_saved_values:function(h,g){if(g){h=c.map(h,function(i){return c.extend({},i,{value:g[i.key]})})}return new e(h)}});var a=Backbone.View.extend({className:"config-settings-view",render:function(){var g=this.$el;this.collection.each(function(j,n){if(j.get("hidden")){return}var i="param_"+n,o=j.get("type"),s=j.get("value");var t=$("<div class='form-row' />").appendTo(g);t.append($("<label />").attr("for",i).text(j.get("label")+":"));if(o==="bool"){t.append($('<input type="checkbox" />').attr("id",i).attr("name",i).attr("checked",s))}else{if(o==="text"){t.append($('<input type="text"/>').attr("id",i).val(s).click(function(){$(this).select()}))}else{if(o==="select"){var q=$("<select />").attr("id",i);c.each(j.get("options"),function(v){$("<option/>").text(v.label).attr("value",v.value).appendTo(q)});q.val(s);t.append(q)}else{if(o==="color"){var u=$("<div/>").appendTo(t),p=$("<input />").attr("id",i).attr("name",i).val(s).css("float","left").appendTo(u).click(function(w){$(".tooltip").removeClass("in");var v=$(this).siblings(".tooltip").addClass("in");v.css({left:$(this).position().left+$(this).width()+5,top:$(this).position().top-($(v).height()/2)+($(this).height()/2)}).show();v.click(function(x){x.stopPropagation()});$(document).bind("click.color-picker",function(){v.hide();$(document).unbind("click.color-picker")});w.stopPropagation()}),m=$("<a href='javascript:void(0)'/>").addClass("icon-button arrow-circle").appendTo(u).attr("title","Set new random color").tooltip(),r=$("<div class='tooltip right' style='position: absolute;' />").appendTo(u).hide(),k=$("<div class='tooltip-inner' style='text-align: inherit'></div>").appendTo(r),h=$("<div class='tooltip-arrow'></div>").appendTo(r),l=$.farbtastic(k,{width:100,height:100,callback:p,color:s});u.append($("<div/>").css("clear","both"));(function(v){m.click(function(){v.setColor(f.get_random_color())})})(l)}else{t.append($("<input />").attr("id",i).attr("name",i).val(s))}}}}if(j.help){t.append($("<div class='help'/>").text(j.help))}});return this},render_in_modal:function(k){var g=this,j=function(){Galaxy.modal.hide();$(window).unbind("keypress.check_enter_esc")},h=function(){Galaxy.modal.hide();$(window).unbind("keypress.check_enter_esc");g.update_from_form()},i=function(l){if((l.keyCode||l.which)===27){j()}else{if((l.keyCode||l.which)===13){h()}}};$(window).bind("keypress.check_enter_esc",i);if(this.$el.children().length===0){this.render()}Galaxy.modal.show({title:k||"Configure",body:this.$el,buttons:{Cancel:j,OK:h}})},update_from_form:function(){var g=this;this.collection.each(function(i,h){if(!i.get("hidden")){var k="param_"+h;var j=g.$el.find("#"+k).val();if(i.get("type")==="bool"){j=g.$el.find("#"+k).is(":checked")}i.set_value(j)}})}});return{ConfigSetting:d,ConfigSettingCollection:e,ConfigSettingCollectionView:a}});