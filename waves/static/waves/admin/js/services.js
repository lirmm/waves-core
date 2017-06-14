/**
 * Created by marc on 25/11/15.
 * Functions library for atgc service platform back-office
 */

(function ($) {
    $(document).ready(function () {
        var prev_val = $("#id_runner").val();
        $("#id_runner").select(function () {
            console.log('focus !');
            prev_val = $(this).val();
            console.log('Prev val' + prev_val);
        }).change(function () {
            console.log('Changed triggered');
            if (prev_val) {
                if (confirm('Changing this value might cancel running jobs.\n\nAre you sure ?')) {
                    $("input[type='submit'][name='_continue']").trigger('click');
                } else {
                    $(this).val(prev_val);
                    // for Django jet widget, reset text label
                    $('#select2-id_runner-container').text($("#id_runner option:selected").text());
                }
            } else {
                console.log('changed ?');
                $("input[type='submit'][name='_continue']").trigger('click');
            }
        });

        $('#open_import_form').click(function (e) {
            e.preventDefault();
            $('#popup_modal_content').load($(this).attr('href'), function () {
                $('#popup_modal').modal('toggle');
            });
        });

        $('input[id^="id_service_outputs"][id$="from_input"]').each(function () {
            console.log(this.id);
        });
    })
})(jQuery || django.jQuery);


