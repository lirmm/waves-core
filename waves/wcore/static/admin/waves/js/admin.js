/**
 * Created by marc on 23/09/16.
 */
var RelatedInlinePopup = function () {
    inline_source = undefined
};

(function ($) {
    RelatedInlinePopup.prototype = {
        popupInline: function (href) {
            //console.log(href.href, typeof href);
            if (href.indexOf('?') === -1) {
                href += '?_popup=1';
            } else {
                href += '&_popup=1';
            }
            var $document = $(window.top.document);
            var $container = $document.find('.related-popup-container');
            var $loading = $container.find('.loading-indicator');
            var $body = $document.find('body');
            var $popup = $('<div>')
                .addClass('related-popup');
            //.data('input', $input);
            var $iframe = $('<iframe>')
                .attr('src', href)
                .on('load', function () {
                    $popup.add($document.find('.related-popup-back')).fadeIn(200, 'swing', function () {
                        $loading.hide();
                    });
                });

            $popup.append($iframe);
            $loading.show();
            $document.find('.related-popup').add($document.find('.related-popup-back')).fadeOut(200, 'swing');
            $container.fadeIn(200, 'swing', function () {
                $container.append($popup);
            });
            $body.addClass('non-scrollable');
        },
        closePopup: function (response) {
            console.log('in closepopup');
            // var previousWindow = this.windowStorage.previous();
            var self = this;

            (function ($) {
                var $document = $(window.parent.document);
                var $popups = $document.find('.related-popup');
                var $container = $document.find('.related-popup-container');
                var $popup = $popups.last();

                if (response != undefined) {
                    self.processPopupResponse($popup, response);
                } else {
                    console.log('no response');
                }

                // self.windowStorage.pop();

                if ($popups.length == 1) {
                    $container.fadeOut(200, 'swing', function () {
                        $document.find('.related-popup-back').hide();
                        $document.find('body').removeClass('non-scrollable');
                        $popup.remove();
                    });
                } else if ($popups.length > 1) {
                    $popup.remove();
                    $popups.eq($popups.length - 2).show();
                }
            })($);
        },
        processPopupResponse: function ($popup, response) {
            console.log('need to process response ' + response + " document " + $popup);
            window.parent.location.reload();
        },
        findPopupResponse: function () {
            var self = this;

            $('#django-waves-admin-inline-popup-response-constants').each(function () {
                var $constants = $(this);
                var response = $constants.data('popup-response');
                self.closePopup(response);
            });
        },
    };

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
            if ($(this).attr('modal-title') !== null) {
                modalContent.find('.modal-header').html("<h4>" + $(this).attr('modal-title') + "</h4>");
            }
            modalContent.find('.modal-body').load($(this).attr('href'), function () {
                console.log('open modal')
                $('#popup_modal').modal('toggle');
            });
        });
        $('fieldset.collapse.open').removeClass('collapsed');
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
})(jQuery || django.jQuery);



