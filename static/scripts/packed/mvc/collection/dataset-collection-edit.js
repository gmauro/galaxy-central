define(["mvc/dataset/hda-model","mvc/collection/dataset-collection-base","utils/localization"],function(c,d,b){var a=d.DatasetCollectionBaseView.extend({initialize:function(e){d.DatasetCollectionBaseView.prototype.initialize.call(this,e)},_render_titleButtons:function(){return d.DatasetCollectionBaseView.prototype._render_titleButtons.call(this).concat([this._render_deleteButton()])},_render_deleteButton:function(){if((this.model.get("state")===c.HistoryDatasetAssociation.STATES.NEW)||(this.model.get("state")===c.HistoryDatasetAssociation.STATES.NOT_VIEWABLE)||(!this.model.get("accessible"))){return null}var e=this,f={title:b("Delete"),classes:"dataset-delete",onclick:function(){e.$el.find(".icon-btn.dataset-delete").trigger("mouseout");e.model["delete"]()}};if(this.model.get("deleted")){f={title:b("Dataset collection is already deleted"),disabled:true}}f.faIcon="fa-times";return faIconButton(f)},toString:function(){var e=(this.model)?(this.model+""):("(no model)");return"HDCAEditView("+e+")"}});return{DatasetCollectionEditView:a}});