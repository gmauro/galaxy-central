<%inherit file="/base.mako"/>

<% import os %>

<%def name="title()">Create New Library Dataset</%def>
%if msg:
  <p class="ok_bgr">${msg}</p></td></tr>
%endif
<div class="toolForm" id="new_dataset">
  <div class="toolFormTitle">Create a new Library Dataset</div>
  <div class="toolFormBody">
    <form name="tool_form" action="${h.url_for( controller='admin', action='dataset' )}" enctype="multipart/form-data" method="post">
      <input type="hidden" name="folder_id" value="${folder_id}">
      <div class="form-row">
        <label>File:</label>
        <div style="float: left; width: 250px; margin-right: 10px;"><input type="file" name="file_data"></div>
        <div style="clear: both"></div>
      </div>
      <div class="form-row">
        <label>URL/Text:</label>
        <div style="float: left; width: 250px; margin-right: 10px;"><textarea name="url_paste" rows="5" cols="35"></textarea></div>
        <div class="toolParamHelp" style="clear: both;">
          Here you may specify a list of URLs (one per line) or paste the contents of a file.
        </div>
        <div style="clear: both"></div>
      </div>
      %if trans.app.config.library_import_dir is not None:
      <div class="form-row">
        <label>Server Directory</label>
        <div style="float: left; width: 250px; margin-right: 10px;">
          <select name="server_dir">
            <option>None</option>
          %for dir in os.listdir( trans.app.config.library_import_dir ):
            <option>${dir}</option>
          %endfor
          </select>
        </div>
        <div class="toolParamHelp" style="clear: both;">
          You may also choose to upload all files in a subdirectory of <strong>${trans.app.config.library_import_dir}</strong> on the Galaxy server.
        </div>
        <div style="clear: both"></div>
      </div>
      %endif
      <div class="form-row">
        <label>Convert spaces to tabs:</label>
        <div style="float: left; width: 250px; margin-right: 10px;"><div><input type="checkbox" name="space_to_tab" value="Yes">Yes</div></div>
        <div class="toolParamHelp" style="clear: both;">
          Use this option if you are entering intervals by hand.
        </div>
        <div style="clear: both"></div>
      </div>
      <div class="form-row">
        <label>File Format:</label>
        <div style="float: left; width: 250px; margin-right: 10px;">
          <select name="extension">
            <option value="auto" selected>Auto-detect</option>
            %for file_format in file_formats:
              <option value="${file_format}">${file_format}</option>
            %endfor
          </select>
        </div>
        <div class="toolParamHelp" style="clear: both;">
          Which format? See help below
        </div>
        <div style="clear: both"></div>
      </div>
      <div class="form-row">
        <label>Genome:</label>
        <div style="float: left; width: 250px; margin-right: 10px;">
          <select name="dbkey">
            %for dbkey in dbkeys:
              %if dbkey[1] == last_used_build:
                <option value="${dbkey[1]}" selected>${dbkey[0]}</option>
              %else:
                <option value="${dbkey[1]}">${dbkey[0]}</option>
              %endif
            %endfor
          </select>
        </div>
        <div style="clear: both"></div>
      </div>
      <div class="form-row">
        <label>Allow public access:</label>
        <input type="checkbox" name="public" value="Yes">  This dataset can be accessed by anyone (make it public).<br/>
        <p/>
        <% user_groups = [ g for g in groups if g[1].endswith( ' private group' ) ] %>
        <% real_groups = [ g for g in groups if not g[1].endswith( ' private group' ) and g[1] != 'public' ] %>
        <div style="float: left; width: 250px; margin-right: 10px;">
          <label>Associate with users:</label>
          <select name="users" multiple="true" size="5">
            %for group in user_groups:
              <option value="${group[0]}">${group[1].replace( ' private group', '' )}</option>
            %endfor
          </select>
          %if len( real_groups ):
            <p/>
            <label>Associate with groups:</label>
            <select name="groups" multiple="true" size="5">
              %for group in real_groups:
                <option value="${group[0]}">${group[1]}</option>
              %endfor
            </select>
          %endif
        </div>
        <div class="toolParamHelp" style="clear: both;">
          To select multiple users or groups, hold ctrl or command while clicking.
        </div>
      </div>
      <div style="clear: both"></div>
      <div class="form-row">
        <input type="submit" class="primary-button" name="create_dataset" value="Add Dataset to Folder">
      </div>
    </form>
  </div>
</div>
