/**
 * Created by marc on 22/09/16.
 */
(function ($) {
    $(document).ready(function () {
        var prev_val = $("#id_clazz").val();
        prev_val.focus(function () {
            prev_val = $(this).val();
            console.log('Prev val' + prev_val);
        }).change(function () {
            console.log('Changed triggered');
            if (prev_val) {
                if (confirm('Changing this value will disable related service and might cancel running jobs.\n\nAre you sure ?')) {
                    $("input[type='submit'][name='_continue']").trigger('click');
                } else {
                    $(this).val(prev_val);
                }
            } else {
                var id_name = $("#id_name")
                if (id_name.val() === "") {
                    id_name.val($(this).val().substring($(this).val().lastIndexOf('.') + 1));
                }
                //$("input[type='submit'][name='_continue']").trigger('click');
            }
        });
        $('#open_import_form').click(function (e) {
            console.log('Launch an import ' + $(this).attr('href'));
            e.preventDefault();
            $('#popup_modal').modal({backdrop: 'static', keyboard: false, show: true});
            $("#popup_modal_content > div.modal-body").html('<img src="/static/waves/img/progress-bar.gif">');
            $('#popup_modal_content').load($(this).attr('href'), function () {
                console.log('loaded')
            });
        });
        $('#popup_modal').on('toggle', function () {
            console.log('show raised');
            $(this).find('.modal-body').css({
                'max-height': '100%'
            });
        });
    })
})(jQuery || django.jQuery);