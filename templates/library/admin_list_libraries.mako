<%inherit file="/base.mako"/>
<%def name="title()">View Libraries</%def>

  <div class="toolForm">
  <div class="toolFormTitle">Manage Libraries</div>
  <div class="toolFormBody">
  %for library in libraries:
  <div class="form-row">
  <a href="${h.url_for( 'manage_library', id = library.id )}">${library.name}</a>
  </div>
  %endfor
  <div class="form-row">
  <a href="${h.url_for( 'manage_library' )}">create new library</a>
  </div>
  </div>
  </div>
