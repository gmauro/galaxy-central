define(["mvc/collection/collection-li","utils/localization"],function(b,a){var c=b.DCListItemView;var d=c.extend({toString:function(){var e=(this.model)?(this.model+""):("(no model)");return"DCEListItemEdit("+e+")"}});return{DCEListItemEdit:d}});