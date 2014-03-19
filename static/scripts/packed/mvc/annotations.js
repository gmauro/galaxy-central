define([],function(){var a=Backbone.View.extend(LoggableMixin).extend(HiddenUntilActivatedViewMixin).extend({tagName:"div",className:"annotation-display",initialize:function(b){b=b||{};this.tooltipConfig=b.tooltipConfig||{placement:"bottom"};this.listenTo(this.model,"change:annotation",function(){this.render()});this.hiddenUntilActivated(b.$activator,b)},render:function(){var b=this;this.$el.html(this._template());this.$el.find("[title]").tooltip(this.tooltipConfig);this.$annotation().make_text_editable({use_textarea:true,on_finish:function(c){b.$annotation().text(c);b.model.save({annotation:c},{silent:true}).fail(function(){b.$annotation().text(b.model.previous("annotation"))})}});return this},_template:function(){var b=this.model.get("annotation");return['<label class="prompt">',_l("Annotation"),"</label>",'<div class="annotation" title="',_l("Edit annotation"),'">',b,"</div>"].join("")},$annotation:function(){return this.$el.find(".annotation")},remove:function(){this.$annotation.off();this.stopListening(this.model);Backbone.View.prototype.remove.call(this)},toString:function(){return["AnnotationEditor(",this.model+"",")"].join("")}});return{AnnotationEditor:a}});