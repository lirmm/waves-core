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
        $('#popup_modal').on('shown.bs.modal', function () {
            $(this).find('.modal-dialog').css({
                width: 'auto',
                height: 'auto',
                'max-height': '90%'
            });
        });
        $('.js-popup-link').click(function (e) {
            e.preventDefault();
            console.log('Js-pop-up-modal called ' + $('#popup_modal'));
            if ($(this).attr('modal-title') != null) {
                $('#popup_modal_content .modal-header').html("<h4>" + $(this).attr('modal-title') + "</h4>");
            }
            $('#popup_modal_content .modal-body').load($(this).attr('href'), function () {
                $('#popup_modal').modal('toggle');
            });
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
