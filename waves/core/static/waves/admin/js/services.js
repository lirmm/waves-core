/**
 * Created by marc on 25/11/15.
 * Functions library for atgc service platform back-office
 */

(function ($) {
    $(document).ready(function () {
        let $runner_tag = $("#id_runner");
        let prev_val = $runner_tag.val();
        $runner_tag
            .on('select', function () {
                console.log('focus !');
                prev_val = $(this).val();
                console.log('Prev val' + prev_val);
            }).on('change', function () {
            let cur_val = $(this).val();
            console.log('Changed triggered');
            if (prev_val && prev_val !== cur_val && cur_val !== '') {
                if (confirm('Changing this value might cancel running jobs.\n\nAre you sure ?' + cur_val + '/' + prev_val)) {
                    $("input[type='submit'][name='_continue']").trigger('click');
                } else {
                    $(this).val(cur_val);
                    // for Django jet widget, reset text label
                    $('#select2-id_runner-container').text($("#id_runner option:selected").text());
                }
            }   /* else {
                    console.log('changed ?');
                    $("input[type='submit'][name='_continue']").trigger('click');
                }*/
        });

        $('#open_import_form').click(function (e) {
            e.preventDefault();
            $('#popup_modal_content').load($(this).attr('href'), function () {
                $('#popup_modal').modal({backdrop: 'static', keyboard: false, show: true});
            });
        });
        $('input[id^="id_service_outputs"][id$="from_input"]').each(function () {
            console.log(this.id);
        });
    })
})(jQuery || django.jQuery);


