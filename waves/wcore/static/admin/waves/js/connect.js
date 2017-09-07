/**
 * Created by marc on 20/02/17.
 */

(function ($) {
    $(document).ready(function () {

        $('#test_connect').click(function (e) {
            e.preventDefault();
            $('#modal_alert .modal-content .modal-header > h4').html('Connection test');
            $("#alert_modal_content > div.modal-body").html('<img src="/static/waves/img/progress-bar.gif">');
            $('#modal_alert').modal('toggle');
            $.getJSON($(this).attr('href'), function (data) {
                $('#modal_alert .modal-content .modal-body').html(data['connection_result'])
            })
        });


        var $loading = $('#loading').hide();
        $(document)
            .ajaxStart(function () {
                $loading.show();
            })
            .ajaxStop(function () {
                $loading.hide();
            });

        $('fieldset.collapse.open').removeClass('collapsed');
        var rel1 = new RelatedInlinePopup();
        rel1.findPopupResponse();
        $('fieldset.show-change-link-popup a.inlinechangelink').click(function (e) {
            var rel = new RelatedInlinePopup();
            e.preventDefault();
            rel.popupInline(e.target.href)
        });
        $('#add_submission_link').click(function (e) {
            e.preventDefault();
            console.log("submission link " + $(this) + ' / ' + e.target);
            var rel = new RelatedInlinePopup();
            rel.popupInline(e.target.href);
        });

    });

})(jQuery || django.jQuery);
