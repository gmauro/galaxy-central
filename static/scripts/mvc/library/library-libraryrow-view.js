// dependencies
define([
    "galaxy.masthead", 
    "utils/utils",
    "libs/toastr",
    "mvc/library/library-model"], 
function(mod_masthead, 
         mod_utils, 
         mod_toastr,
         mod_library_model) {

// galaxy library row view
var LibraryRowView = Backbone.View.extend({
  events: {
    'click .edit_library_btn'           : 'edit_button_clicked',
    'click .cancel_library_btn'         : 'cancel_library_modification',
    'click .save_library_btn'           : 'save_library_modification',
    'click .delete_library_btn'         : 'delete_library',
    'click .undelete_library_btn'       : 'undelete_library',
    'click .upload_library_btn'         : 'upload_to_library',
    'click .permission_library_btn'     : 'permissions_on_library'
  },

  edit_mode: false,
  
  element_visibility_config: {
    upload_library_btn: false,
    edit_library_btn: false,
    permission_library_btn: false,
    save_library_btn: false,
    cancel_library_btn: false,
    delete_library_btn: false,
    undelete_library_btn: false
  },

  initialize : function(library){
    this.render(library);
  },

  render: function(library){
    if (typeof library === 'undefined'){
      var library = Galaxy.libraries.libraryListView.collection.get(this.$el.data('id'));
    }
    this.prepareButtons(library);
    var tmpl = this.templateRow();
    this.setElement(tmpl({library:library, button_config: this.element_visibility_config, edit_mode: this.edit_mode}));
    this.$el.show();
    return this;
  },

  repaint: function(library){
    /* need to hide manually because of the element removal in setElement 
    invoked in render() */
    $(".tooltip").hide(); 
    /* we need to store the old element to be able to replace it with 
    new one */
    var old_element = this.$el;
    /* if user canceled the library param is undefined, 
      if user saved and succeeded the updated library is rendered */
    this.render(library);
    old_element.replaceWith(this.$el);
    /* now we attach new tooltips to the newly created row element */
    this.$el.find("[data-toggle]").tooltip();
  },

  prepareButtons: function(library){
    vis_config = this.element_visibility_config;

    if (this.edit_mode === false){
      vis_config.save_library_btn = false;
      vis_config.cancel_library_btn = false;
      vis_config.delete_library_btn = false;
      if (library.get('deleted') === true ){
        // if (Galaxy.currUser.isAdmin()){
          vis_config.undelete_library_btn = true;
          vis_config.upload_library_btn = false;
          vis_config.edit_library_btn = false;
          vis_config.permission_library_btn = false;
        // }
      } else if (library.get('deleted') === false ) {
        vis_config.save_library_btn = false;
        vis_config.cancel_library_btn = false;
        vis_config.undelete_library_btn = false;
        if (library.get('can_user_add') === true){
          vis_config.upload_library_btn = true;
        }    
        if (library.get('can_user_modify') === true){
          vis_config.edit_library_btn = true;
        }    
        if (library.get('can_user_manage') === true){
          vis_config.permission_library_btn = true;
        }    
      }
    } else if (this.edit_mode === true){
      vis_config.upload_library_btn = false;
      vis_config.edit_library_btn = false;
      vis_config.permission_library_btn = false;
      vis_config.save_library_btn = true;
      vis_config.cancel_library_btn = true;
      vis_config.delete_library_btn = true;
    }

    this.element_visibility_config = vis_config;
  },

  upload_to_library: function(){
    mod_toastr.info('Coming soon. Stay tuned.');
  },

  permissions_on_library: function(){
    mod_toastr.info('Coming soon. Stay tuned.');
  },

  /* User clicked the 'edit' button on row so we render a new row
    that allows editing */
  edit_button_clicked: function(){
    this.edit_mode = true;
    this.repaint();
  },

  /* User clicked the 'cancel' button so we render normal rowView */
  cancel_library_modification: function(){
    mod_toastr.info('Modifications canceled');
    this.edit_mode = false;
    this.repaint();
  },

  save_library_modification: function(){
    var library = Galaxy.libraries.libraryListView.collection.get(this.$el.data('id'));
    var is_changed = false;

    var new_name = this.$el.find('.input_library_name').val();
    if (typeof new_name !== 'undefined' && new_name !== library.get('name') ){
        if (new_name.length > 2){
            library.set("name", new_name);
            is_changed = true;
        } else{
            mod_toastr.warning('Library name has to be at least 3 characters long');
            return
        }
    }

    var new_description = this.$el.find('.input_library_description').val();
    if (typeof new_description !== 'undefined' && new_description !== library.get('description') ){
        library.set("description", new_description);
        is_changed = true;
    }

    var new_synopsis = this.$el.find('.input_library_synopsis').val();
    if (typeof new_synopsis !== 'undefined' && new_synopsis !== library.get('synopsis') ){
        library.set("synopsis", new_synopsis);
        is_changed = true;
    }

    if (is_changed){
      var row_view = this;
        library.save(null, {
          patch: true,
          success: function(library) {
            row_view.edit_mode = false;
            row_view.repaint(library);
            mod_toastr.success('Changes to library saved');
          },
          error: function(model, response){
            mod_toastr.error('An error occured during updating the library :(');
          }
        });
    } else {
      this.edit_mode = false;
      this.repaint(library);
      mod_toastr.info('Nothing has changed');
    }
  },

  delete_library: function(){
    var library = Galaxy.libraries.libraryListView.collection.get(this.$el.data('id'));
    var row_view = this;
    // mark the library deleted
    library.destroy({
      success: function (library) {
        library.set('deleted', true);
        // add the new deleted library back to the collection (Galaxy specialty)
        Galaxy.libraries.libraryListView.collection.add(library);
        row_view.edit_mode = false;
        if (Galaxy.libraries.preferences.get('with_deleted') === false){
          $(".tooltip").hide(); 
          row_view.$el.remove();
        } else if (Galaxy.libraries.preferences.get('with_deleted') === true){
          row_view.repaint(library);
        }
        mod_toastr.success('Library has been marked deleted');
      },
      error: function(){
        mod_toastr.error('An error occured during deleting the library :(');
      }
    });
  },

  undelete_library: function(){
    var library = Galaxy.libraries.libraryListView.collection.get(this.$el.data('id'));
    var row_view = this;

    // mark the library undeleted
    library.url = library.urlRoot + library.id + '?undelete=true';
    library.destroy({
      success: function (library) {
        // add the newly undeleted library back to the collection
        // backbone does not accept changes through destroy, so update it too
        library.set('deleted', false);
        Galaxy.libraries.libraryListView.collection.add(library);
        row_view.edit_mode = false;
        row_view.repaint(library);
        mod_toastr.success('Library has been undeleted');
      },
      error: function(){
        mod_toastr.error('An error occured while undeleting the library :(');
      }
    });
  },

  templateRow: function() {
    tmpl_array = [];

    tmpl_array.push('           <tr class="<% if(library.get("deleted") === true) { print("active") } %>" style="display:none;" data-id="<%- library.get("id") %>">');
    tmpl_array.push('               <% if(!edit_mode) { %>');
    tmpl_array.push('                 <td><a href="#folders/<%- library.get("root_folder_id") %>"><%- library.get("name") %></a></td>');
    tmpl_array.push('                 <td><%= _.escape(library.get("description")) %></td>');
    tmpl_array.push('                 <td><%= _.escape(library.get("synopsis")) %></td>');
    tmpl_array.push('               <% } else if(edit_mode){ %>');
    tmpl_array.push('                 <td><input type="text" class="form-control input_library_name" placeholder="name" value="<%- library.get("name") %>"></td>');
    tmpl_array.push('                 <td><input type="text" class="form-control input_library_description" placeholder="description" value="<%- library.get("description") %>"></td>');
    tmpl_array.push('                 <td><input type="text" class="form-control input_library_synopsis" placeholder="synopsis" value="<%- library.get("synopsis") %>"></td>');
    tmpl_array.push('               <% } %>');
    tmpl_array.push('               <td class="right-center">');
    tmpl_array.push('                   <% if(library.get("deleted") === true) { %>');
    tmpl_array.push('                       <span data-toggle="tooltip" data-placement="top" title="Marked deleted" style="color:grey;" class="fa fa-ban fa-lg deleted_lib_ico"> </span>');
    tmpl_array.push('                   <% } else if(library.get("public") === true) { %>');
    tmpl_array.push('                     <span data-toggle="tooltip" data-placement="top" title="Public" style="color:grey;" class="fa fa-globe fa-lg public_lib_ico"> </span>');
    tmpl_array.push('                   <% }%>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Upload to library" class="primary-button btn-xs upload_library_btn" type="button" style="<% if(button_config.upload_library_btn === false) { print("display:none;") } %>"><span class="fa fa-upload"></span></button>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Modify library" class="primary-button btn-xs edit_library_btn" type="button" style="<% if(button_config.edit_library_btn === false) { print("display:none;") } %>"><span class="fa fa-pencil"></span></button>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Modify permissions" class="primary-button btn-xs permission_library_btn" type="button" style="<% if(button_config.permission_library_btn === false) { print("display:none;") } %>"><span class="fa fa-group"></span></button>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Save changes" class="primary-button btn-xs save_library_btn" type="button" style="<% if(button_config.save_library_btn === false) { print("display:none;") } %>"><span class="fa fa-floppy-o"> Save</span></button>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Discard changes" class="primary-button btn-xs cancel_library_btn" type="button" style="<% if(button_config.cancel_library_btn === false) { print("display:none;") } %>"><span class="fa fa-times"> Cancel</span></button>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Delete library (can be undeleted later)" class="primary-button btn-xs delete_library_btn" type="button" style="<% if(button_config.delete_library_btn === false) { print("display:none;") } %>"><span class="fa fa-trash-o"> Delete</span></button>');
    tmpl_array.push('                   <button data-toggle="tooltip" data-placement="top" title="Undelete library" class="primary-button btn-xs undelete_library_btn" type="button" style="<% if(button_config.undelete_library_btn === false) { print("display:none;") } %>"><span class="fa fa-unlock"> Undelete</span></button>');
    tmpl_array.push('               </td>');
    tmpl_array.push('           </tr>');

    return _.template(tmpl_array.join('')); 
  }
   
});

  // return
return {
    LibraryRowView: LibraryRowView
};

});
