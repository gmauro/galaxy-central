define(["mvc/base-mvc","utils/localization"],function(a,b){var c=Backbone.View.extend(a.LoggableMixin).extend(a.HiddenUntilActivatedViewMixin).extend({tagName:"div",className:"tags-display",initialize:function(d){this.listenTo(this.model,"change:tags",function(){this.render()});this.hiddenUntilActivated(d.$activator,d)},render:function(){var d=this;this.$el.html(this._template());this.$input().select2({placeholder:"Add tags",width:"100%",tags:function(){return d._getTagsUsed()}});this._setUpBehaviors();return this},_template:function(){return['<label class="prompt">',b("Tags"),"</label>",'<input class="tags-input" value="',this.tagsToCSV(),'" />'].join("")},tagsToCSV:function(){var d=this.model.get("tags");if(!_.isArray(d)||_.isEmpty(d)){return""}return d.map(function(e){return _.escape(e)}).sort().join(",")},$input:function(){return this.$el.find("input.tags-input")},_getTagsUsed:function(){return Galaxy.currUser.get("tags_used")},_setUpBehaviors:function(){var d=this;this.$input().on("change",function(e){d.model.save({tags:e.val},{silent:true});if(e.added){d._addNewTagToTagsUsed(e.added.text+"")}})},_addNewTagToTagsUsed:function(d){var e=Galaxy.currUser.get("tags_used");if(!_.contains(e,d)){e.push(d);e.sort();Galaxy.currUser.set("tags_used",e)}},remove:function(){this.$input.off();this.stopListening(this.model);Backbone.View.prototype.remove.call(this)},toString:function(){return["TagsEditor(",this.model+"",")"].join("")}});return{TagsEditor:c}});