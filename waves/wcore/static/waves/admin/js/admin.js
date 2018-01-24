/**
 * Created by marc on 23/09/16.
 */
(function ($) {
    $(document).ready(function () {
        $('#popup_modal').on('shown.bs.modal', function () {
            $(this).find('.modal-dialog').css({
                width: 'auto',
                height: 'auto',
                'max-height': '80%'
            });
        });

        $('.js-popup-link').click(function (e) {
            e.preventDefault();
            // language=JQuery-CSS
            var modalContent = $('#popup_modal_content');
            console.log('Js-pop-up-modal called ' + $('#popup_modal'));
            if ($(this).attr('js-modal-title') !== null) {
                modalContent.find('.modal-header').html("<h4>" + $(this).attr('js-modal-title') + "</h4>");
            }
            modalContent.find('.modal-body').load($(this).attr('href'), function () {
                console.log('open modal');
                $('#popup_modal').modal({backdrop: 'static', keyboard: false, show:true});
            })
        })
        $('#modal_alert').on('show.bs.modal', function () {
            console.log('opened !');
            $(this).find('.modal-dialog').css({
                'max-height': '50%'
            });
        }).on('hidden.bs.modal', function () {
            $(this).find('.modal-body').html("");
            console.log("closed");
        });


    });
    $(window).load(function () {
        $('fieldset.collapse.open').each(function () {
            $(this).removeClass('collapsed');
            $(this).find('a.collapse-toggle').html('Hide');
        })
        $('.errorlist').parents('fieldset.collapsed').each(function () {
            $(this).removeClass('collapsed');
        });
    })

})(jQuery || django.jQuery);



