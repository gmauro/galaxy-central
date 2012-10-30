(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['template-history-warning-messages'] = template(function (Handlebars,depth0,helpers,partials,data) {
  helpers = helpers || Handlebars.helpers;
  var buffer = "", stack1, functionType="function", escapeExpression=this.escapeExpression, self=this, blockHelperMissing=helpers.blockHelperMissing;

function program1(depth0,data) {
  
  var stack1;
  stack1 = depth0.purged;
  stack1 = helpers.unless.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(2, program2, data)});
  if(stack1 || stack1 === 0) { return stack1; }
  else { return ''; }}
function program2(depth0,data) {
  
  var buffer = "", stack1, foundHelper;
  buffer += "\n";
  foundHelper = helpers.warningmessagesmall;
  if (foundHelper) { stack1 = foundHelper.call(depth0, {hash:{},inverse:self.noop,fn:self.program(3, program3, data)}); }
  else { stack1 = depth0.warningmessagesmall; stack1 = typeof stack1 === functionType ? stack1() : stack1; }
  if (!helpers.warningmessagesmall) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(3, program3, data)}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n";
  return buffer;}
function program3(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "\n    This dataset has been deleted.\n    ";
  stack1 = depth0.urls;
  stack1 = stack1 == null || stack1 === false ? stack1 : stack1.undelete;
  stack1 = helpers['if'].call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(4, program4, data)});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n";
  return buffer;}
function program4(depth0,data) {
  
  var buffer = "", stack1, foundHelper;
  buffer += "\n        Click <a href=\"";
  stack1 = depth0.urls;
  stack1 = stack1 == null || stack1 === false ? stack1 : stack1.undelete;
  stack1 = typeof stack1 === functionType ? stack1() : stack1;
  buffer += escapeExpression(stack1) + "\" class=\"historyItemUndelete\" id=\"historyItemUndeleter-";
  foundHelper = helpers.id;
  if (foundHelper) { stack1 = foundHelper.call(depth0, {hash:{}}); }
  else { stack1 = depth0.id; stack1 = typeof stack1 === functionType ? stack1() : stack1; }
  buffer += escapeExpression(stack1) + "\"\n                 target=\"galaxy_history\">here</a> to undelete it\n        ";
  stack1 = depth0.urls;
  stack1 = stack1 == null || stack1 === false ? stack1 : stack1.purge;
  stack1 = helpers['if'].call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(5, program5, data)});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n    ";
  return buffer;}
function program5(depth0,data) {
  
  var buffer = "", stack1, foundHelper;
  buffer += "\n        or <a href=\"";
  stack1 = depth0.urls;
  stack1 = stack1 == null || stack1 === false ? stack1 : stack1.purge;
  stack1 = typeof stack1 === functionType ? stack1() : stack1;
  buffer += escapeExpression(stack1) + "\" class=\"historyItemPurge\" id=\"historyItemPurger-";
  foundHelper = helpers.id;
  if (foundHelper) { stack1 = foundHelper.call(depth0, {hash:{}}); }
  else { stack1 = depth0.id; stack1 = typeof stack1 === functionType ? stack1() : stack1; }
  buffer += escapeExpression(stack1) + "\"\n           target=\"galaxy_history\">here</a> to immediately remove it from disk\n        ";
  return buffer;}

function program7(depth0,data) {
  
  var stack1, foundHelper;
  foundHelper = helpers.warningmessagesmall;
  if (foundHelper) { stack1 = foundHelper.call(depth0, {hash:{},inverse:self.noop,fn:self.program(8, program8, data)}); }
  else { stack1 = depth0.warningmessagesmall; stack1 = typeof stack1 === functionType ? stack1() : stack1; }
  if (!helpers.warningmessagesmall) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(8, program8, data)}); }
  if(stack1 || stack1 === 0) { return stack1; }
  else { return ''; }}
function program8(depth0,data) {
  
  
  return "\n    This dataset has been deleted and removed from disk.\n";}

function program10(depth0,data) {
  
  var stack1, foundHelper;
  foundHelper = helpers.warningmessagesmall;
  if (foundHelper) { stack1 = foundHelper.call(depth0, {hash:{},inverse:self.noop,fn:self.program(11, program11, data)}); }
  else { stack1 = depth0.warningmessagesmall; stack1 = typeof stack1 === functionType ? stack1() : stack1; }
  if (!helpers.warningmessagesmall) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(11, program11, data)}); }
  if(stack1 || stack1 === 0) { return stack1; }
  else { return ''; }}
function program11(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "\n    This dataset has been hidden.\n    ";
  stack1 = depth0.urls;
  stack1 = stack1 == null || stack1 === false ? stack1 : stack1.unhide;
  stack1 = helpers['if'].call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(12, program12, data)});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n";
  return buffer;}
function program12(depth0,data) {
  
  var buffer = "", stack1, foundHelper;
  buffer += "\n        Click <a href=\"";
  stack1 = depth0.urls;
  stack1 = stack1 == null || stack1 === false ? stack1 : stack1.unhide;
  stack1 = typeof stack1 === functionType ? stack1() : stack1;
  buffer += escapeExpression(stack1) + "\" class=\"historyItemUnhide\" id=\"historyItemUnhider-";
  foundHelper = helpers.id;
  if (foundHelper) { stack1 = foundHelper.call(depth0, {hash:{}}); }
  else { stack1 = depth0.id; stack1 = typeof stack1 === functionType ? stack1() : stack1; }
  buffer += escapeExpression(stack1) + "\"\n                 target=\"galaxy_history\">here</a> to unhide it\n    ";
  return buffer;}

  stack1 = depth0.deleted;
  stack1 = helpers['if'].call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(1, program1, data)});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n";
  stack1 = depth0.purged;
  stack1 = helpers['if'].call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(7, program7, data)});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n";
  stack1 = depth0.visible;
  stack1 = helpers.unless.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(10, program10, data)});
  if(stack1 || stack1 === 0) { buffer += stack1; }
  return buffer;});
})();