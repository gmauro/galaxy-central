define(["mvc/history/history-panel","mvc/history/history-contents","mvc/dataset/states","mvc/history/hda-model","mvc/history/hda-li-edit","mvc/history/hdca-li-edit","mvc/tags","mvc/annotations","utils/localization"],function(f,h,k,d,c,g,j,a,b){var i=f.HistoryPanel;var e=i.extend({HDAViewClass:c.HDAListItemEdit,HDCAViewClass:g.HDCAListItemEdit,initialize:function(l){l=l||{};i.prototype.initialize.call(this,l);this.tagsEditor=null;this.annotationEditor=null;this.purgeAllowed=l.purgeAllowed||false;this.annotationEditorShown=l.annotationEditorShown||false;this.tagsEditorShown=l.tagsEditorShown||false;this.multiselectActions=l.multiselectActions||this._getActions()},_setUpCollectionListeners:function(){i.prototype._setUpCollectionListeners.call(this);this.collection.on("change:deleted",this._handleHdaDeletionChange,this);this.collection.on("change:visible",this._handleHdaVisibleChange,this);this.collection.on("change:purged",function(l){this.model.fetch()},this);return this},_setUpModelListeners:function(){i.prototype._setUpModelListeners.call(this);this.model.on("change:nice_size",this.updateHistoryDiskSize,this);return this},_buildNewRender:function(){var l=i.prototype._buildNewRender.call(this);if(!this.model){return l}if(Galaxy&&Galaxy.currUser&&Galaxy.currUser.id&&Galaxy.currUser.id===this.model.get("user_id")){this._renderTags(l);this._renderAnnotation(l)}return l},_renderTags:function(l){var m=this;this.tagsEditor=new j.TagsEditor({model:this.model,el:l.find(".controls .tags-display"),onshowFirstTime:function(){this.render()},onshow:function(){m.toggleHDATagEditors(true,m.fxSpeed)},onhide:function(){m.toggleHDATagEditors(false,m.fxSpeed)},$activator:faIconButton({title:b("Edit history tags"),classes:"history-tag-btn",faIcon:"fa-tags"}).appendTo(l.find(".controls .actions"))})},_renderAnnotation:function(l){var m=this;this.annotationEditor=new a.AnnotationEditor({model:this.model,el:l.find(".controls .annotation-display"),onshowFirstTime:function(){this.render()},onshow:function(){m.toggleHDAAnnotationEditors(true,m.fxSpeed)},onhide:function(){m.toggleHDAAnnotationEditors(false,m.fxSpeed)},$activator:faIconButton({title:b("Edit history annotation"),classes:"history-annotate-btn",faIcon:"fa-comment"}).appendTo(l.find(".controls .actions"))})},_setUpBehaviors:function(l){l=l||this.$el;i.prototype._setUpBehaviors.call(this,l);if(!this.model){return}if(this.multiselectActions.length){this.actionsPopup=new PopupMenu(l.find(".list-action-popup-btn"),this.multiselectActions)}if((!Galaxy.currUser||Galaxy.currUser.isAnonymous())||(Galaxy.currUser.id!==this.model.get("user_id"))){return}var m=this,n=".controls .name";l.find(n).attr("title",b("Click to rename history")).tooltip({placement:"bottom"}).make_text_editable({on_finish:function(o){var p=m.model.get("name");if(o&&o!==p){m.$el.find(n).text(o);m.model.save({name:o}).fail(function(){m.$el.find(n).text(m.model.previous("name"))})}else{m.$el.find(n).text(p)}}})},_getActions:function(){var l=this,m=[{html:b("Hide datasets"),func:function(){var n=d.HistoryDatasetAssociation.prototype.hide;l.getSelectedModels().ajaxQueue(n)}},{html:b("Unhide datasets"),func:function(){var n=d.HistoryDatasetAssociation.prototype.unhide;l.getSelectedModels().ajaxQueue(n)}},{html:b("Delete datasets"),func:function(){var n=d.HistoryDatasetAssociation.prototype["delete"];l.getSelectedModels().ajaxQueue(n)}},{html:b("Undelete datasets"),func:function(){var n=d.HistoryDatasetAssociation.prototype.undelete;l.getSelectedModels().ajaxQueue(n)}}];if(l.purgeAllowed){m.push({html:b("Permanently delete datasets"),func:function(){if(confirm(b("This will permanently remove the data in your datasets. Are you sure?"))){var n=d.HistoryDatasetAssociation.prototype.purge;l.getSelectedModels().ajaxQueue(n)}}})}m.push({html:b("Build Dataset List"),func:function(){l.getSelectedModels().promoteToHistoryDatasetCollection(l.model,"list")}});m.push({html:b("Build Dataset Pair"),func:function(){l.getSelectedModels().promoteToHistoryDatasetCollection(l.model,"paired")}});m.push({html:b("Build List of Dataset Pairs"),func:_.bind(l._showPairedCollectionModal,l)});return m},_showPairedCollectionModal:function(){var l=this,m=l.getSelectedModels().toJSON().filter(function(n){return n.history_content_type==="dataset"&&n.state===k.OK});if(m.length){require(["mvc/collection/paired-collection-creator"],function(n){window.creator=n.pairedCollectionCreatorModal(m,{historyId:l.model.id})})}else{}},_getItemViewOptions:function(m){var l=i.prototype._getItemViewOptions.call(this,m);_.extend(l,{purgeAllowed:this.purgeAllowed,tagsEditorShown:(this.tagsEditor&&!this.tagsEditor.hidden),annotationEditorShown:(this.annotationEditor&&!this.annotationEditor.hidden)});return l},_handleHdaDeletionChange:function(l){if(l.get("deleted")&&!this.storage.get("show_deleted")){this.removeItemView(l)}},_handleHdaVisibleChange:function(l){if(l.hidden()&&!this.storage.get("show_hidden")){this.removeItemView(l)}},toggleHDATagEditors:function(l){var m=Array.prototype.slice.call(arguments,1);_.each(this.views,function(n){if(n.tagsEditor){n.tagsEditor.toggle.apply(n.tagsEditor,m)}})},toggleHDAAnnotationEditors:function(l){var m=Array.prototype.slice.call(arguments,1);_.each(this.views,function(n){if(n.annotationEditor){n.annotationEditor.toggle.apply(n.annotationEditor,m)}})},events:_.extend(_.clone(i.prototype.events),{"click .show-selectors-btn":"toggleSelectors"}),updateHistoryDiskSize:function(){this.$el.find(".history-size").text(this.model.get("nice_size"))},toString:function(){return"HistoryPanelEdit("+((this.model)?(this.model.get("name")):(""))+")"}});return{HistoryPanelEdit:e}});