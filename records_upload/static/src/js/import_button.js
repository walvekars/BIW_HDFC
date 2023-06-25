odoo.define('records_upload.import_button', function (require) {
"use strict";
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');
var ImportButton = ListController.extend({
    buttons_template: 'records_upload.buttons',
    events: _.extend({}, ListController.prototype.events, {
       'click .import_btn_action': '_ImportButton',
    }),
    _ImportButton: function () {
        var self = this;
        this.do_action({
           type: 'ir.actions.act_window',
           res_model: 'choose.file',
           name :'Import',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'new',
           res_id: false,
       });
    }
    });
    var TrialSheetListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ImportButton,
        }),
    });
    viewRegistry.add('import_btn', TrialSheetListView);
});