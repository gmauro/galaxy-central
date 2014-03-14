define(["mvc/dataset/hda-model","mvc/dataset/hda-edit","mvc/history/readonly-history-panel"],function(c,a,b){var d=b.ReadOnlyHistoryPanel.extend({HDAViewClass:a.HDAEditView,initialize:function(e){e=e||{};this.selectedHdaIds=[];this.tagsEditor=null;this.annotationEditor=null;this.selecting=e.selecting||false;this.annotationEditorShown=e.annotationEditorShown||false;this.tagsEditorShown=e.tagsEditorShown||false;b.ReadOnlyHistoryPanel.prototype.initialize.call(this,e)},_setUpModelEventHandlers:function(){b.ReadOnlyHistoryPanel.prototype._setUpModelEventHandlers.call(this);this.model.on("change:nice_size",this.updateHistoryDiskSize,this);this.model.hdas.on("change:deleted",this._handleHdaDeletionChange,this);this.model.hdas.on("change:visible",this._handleHdaVisibleChange,this);this.model.hdas.on("change:purged",function(e){this.model.fetch()},this)},renderModel:function(){var e=$("<div/>");e.append(d.templates.historyPanel(this.model.toJSON()));if(Galaxy.currUser.id&&Galaxy.currUser.id===this.model.get("user_id")){this._renderTags(e);this._renderAnnotation(e)}e.find(".history-secondary-actions").prepend(this._renderSelectButton());e.find(".history-dataset-actions").toggle(this.selecting);e.find(".history-secondary-actions").prepend(this._renderSearchButton());this._setUpBehaviours(e);this.renderHdas(e);return e},_renderTags:function(e){var f=this;this.tagsEditor=new TagsEditor({model:this.model,el:e.find(".history-controls .tags-display"),onshowFirstTime:function(){this.render()},onshow:function(){f.toggleHDATagEditors(true,f.fxSpeed)},onhide:function(){f.toggleHDATagEditors(false,f.fxSpeed)},$activator:faIconButton({title:_l("Edit history tags"),classes:"history-tag-btn",faIcon:"fa-tags"}).appendTo(e.find(".history-secondary-actions"))})},_renderAnnotation:function(e){var f=this;this.annotationEditor=new AnnotationEditor({model:this.model,el:e.find(".history-controls .annotation-display"),onshowFirstTime:function(){this.render()},onshow:function(){f.toggleHDAAnnotationEditors(true,f.fxSpeed)},onhide:function(){f.toggleHDAAnnotationEditors(false,f.fxSpeed)},$activator:faIconButton({title:_l("Edit history Annotation"),classes:"history-annotate-btn",faIcon:"fa-comment"}).appendTo(e.find(".history-secondary-actions"))})},_renderSelectButton:function(e){return faIconButton({title:_l("Operations on multiple datasets"),classes:"history-select-btn",faIcon:"fa-check-square-o"})},_setUpBehaviours:function(e){e=e||this.$el;b.ReadOnlyHistoryPanel.prototype._setUpBehaviours.call(this,e);if(!this.model){return}this._setUpDatasetActionsPopup(e);if((!Galaxy.currUser||Galaxy.currUser.isAnonymous())||(Galaxy.currUser.id!==this.model.get("user_id"))){return}var f=this;e.find(".history-name").attr("title",_l("Click to rename history")).tooltip({placement:"bottom"}).make_text_editable({on_finish:function(g){var h=f.model.get("name");if(g&&g!==h){f.$el.find(".history-name").text(g);f.model.save({name:g}).fail(function(){f.$el.find(".history-name").text(f.model.previous("name"))})}else{f.$el.find(".history-name").text(h)}}})},_setUpDatasetActionsPopup:function(e){var f=this;(new PopupMenu(e.find(".history-dataset-action-popup-btn"),[{html:_l("Hide datasets"),func:function(){var g=c.HistoryDatasetAssociation.prototype.hide;f.getSelectedHdaCollection().ajaxQueue(g)}},{html:_l("Unhide datasets"),func:function(){var g=c.HistoryDatasetAssociation.prototype.unhide;f.getSelectedHdaCollection().ajaxQueue(g)}},{html:_l("Delete datasets"),func:function(){var g=c.HistoryDatasetAssociation.prototype["delete"];f.getSelectedHdaCollection().ajaxQueue(g)}},{html:_l("Undelete datasets"),func:function(){var g=c.HistoryDatasetAssociation.prototype.undelete;f.getSelectedHdaCollection().ajaxQueue(g)}},{html:_l("Permanently delete datasets"),func:function(){if(confirm(_l("This will permanently remove the data in your datasets. Are you sure?"))){var g=c.HistoryDatasetAssociation.prototype.purge;f.getSelectedHdaCollection().ajaxQueue(g)}}}]))},_handleHdaDeletionChange:function(e){if(e.get("deleted")&&!this.storage.get("show_deleted")){this.removeHdaView(this.hdaViews[e.id])}},_handleHdaVisibleChange:function(e){if(e.hidden()&&!this.storage.get("show_hidden")){this.removeHdaView(this.hdaViews[e.id])}},_createHdaView:function(f){var e=f.get("id"),g=new this.HDAViewClass({model:f,linkTarget:this.linkTarget,expanded:this.storage.get("expandedHdas")[e],selectable:this.selecting,hasUser:this.model.ownedByCurrUser(),logger:this.logger,tagsEditorShown:(this.tagsEditor&&!this.tagsEditor.hidden),annotationEditorShown:(this.annotationEditor&&!this.annotationEditor.hidden)});this._setUpHdaListeners(g);return g},_setUpHdaListeners:function(f){var e=this;b.ReadOnlyHistoryPanel.prototype._setUpHdaListeners.call(this,f);f.on("selected",function(g){var h=g.model.get("id");e.selectedHdaIds=_.union(e.selectedHdaIds,[h])});f.on("de-selected",function(g){var h=g.model.get("id");e.selectedHdaIds=_.without(e.selectedHdaIds,h)})},toggleHDATagEditors:function(e){var f=arguments;_.each(this.hdaViews,function(g){if(g.tagsEditor){g.tagsEditor.toggle.apply(g.tagsEditor,f)}})},toggleHDAAnnotationEditors:function(e){var f=arguments;_.each(this.hdaViews,function(g){if(g.annotationEditor){g.annotationEditor.toggle.apply(g.annotationEditor,f)}})},removeHdaView:function(f){if(!f){return}var e=this;f.$el.fadeOut(e.fxSpeed,function(){f.off();f.remove();delete e.hdaViews[f.model.id];if(_.isEmpty(e.hdaViews)){e.$emptyMessage().fadeIn(e.fxSpeed,function(){e.trigger("empty-history",e)})}})},events:_.extend(_.clone(b.ReadOnlyHistoryPanel.prototype.events),{"click .history-select-btn":function(f){this.toggleSelectors(this.fxSpeed)},"click .history-select-all-datasets-btn":"selectAllDatasets","click .history-deselect-all-datasets-btn":"deselectAllDatasets"}),updateHistoryDiskSize:function(){this.$el.find(".history-size").text(this.model.get("nice_size"))},showSelectors:function(e){this.selecting=true;this.$el.find(".history-dataset-actions").slideDown(e);_.each(this.hdaViews,function(f){f.showSelector(e)});this.selectedHdaIds=[]},hideSelectors:function(e){this.selecting=false;this.$el.find(".history-dataset-actions").slideUp(e);_.each(this.hdaViews,function(f){f.hideSelector(e)});this.selectedHdaIds=[]},toggleSelectors:function(e){if(!this.selecting){this.showSelectors(e)}else{this.hideSelectors(e)}},selectAllDatasets:function(e){_.each(this.hdaViews,function(f){f.select(e)})},deselectAllDatasets:function(e){_.each(this.hdaViews,function(f){f.deselect(e)})},getSelectedHdaViews:function(){return _.filter(this.hdaViews,function(e){return e.selected})},getSelectedHdaCollection:function(){return new c.HDACollection(_.map(this.getSelectedHdaViews(),function(e){return e.model}),{historyId:this.model.id})},toString:function(){return"HistoryPanel("+((this.model)?(this.model.get("name")):(""))+")"}});return{HistoryPanel:d}});