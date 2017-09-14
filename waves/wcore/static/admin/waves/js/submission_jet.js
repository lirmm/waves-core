var RelatedInlinePopup = function () {
    var inline_source = undefined
};

(function ($) {
    RelatedInlinePopup.prototype = {
        popupInline: function (href) {
            if (href.indexOf('?') === -1) {
                href += '?_popup=1';
            } else {
                href += '&_popup=1';
            }
            var $document = $(window.top.document);
            var $container = $document.find('.related-popup-container');
            var $loading = $container.find('.loading-indicator');
            var $body = $document.find('body');
            var $popup = $('<div>').addClass('related-popup');
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
            // var previousWindow = this.windowStorage.previous();
            var self = this;

            (function ($) {
                var $document = $(window.parent.document);
                var $popups = $document.find('.related-popup');
                var $container = $document.find('.related-popup-container');
                var $popup = $popups.last();

                if (response !== undefined) {
                    self.processPopupResponse($popup, response);
                } else {
                    console.log('no response');
                }

                // self.windowStorage.pop();

                if ($popups.length === 1) {
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
        }
    };
    $(document).ready(function () {
        var rel = new RelatedInlinePopup();
        $('#inputs-group').find('tr.add-row a').each(function () {
            $(this).off("click");
            $(this).on('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                $('#add_submission_input_link').trigger('click');
            });
        });
        $('#add_submission_input_link').click(function(event){
            event.preventDefault();
            event.stopImmediatePropagation();
            event.stopPropagation();
            rel.popupInline($('#add_submission_input_link').attr('href'));
        })
        $('a.inlinechangelink').click(function (e) {
            e.preventDefault();
            rel.popupInline(e.target.href)
        })
    })
})
(django.jQuery || jQuery);