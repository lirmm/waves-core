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
    });
})(jQuery || django.jQuery);
