/**
 * Created by marc on 22/11/16.
 */
(function ($) {
    $(document).ready(function () {
        $('.btn-file :file').on('fileselect', function (event, numFiles, label) {

            var input = $(this).parents('.input-group').find(':text'),
                log = numFiles > 1 ? numFiles + ' files selected' : label;

            if (input.length) {
                input.val(log);
            } else {
                if (log) alert(log);
            }

        });
        $(document).on('change', '.btn-file :file', function () {
            var input = $(this),
                numFiles = input.get(0).files ? input.get(0).files.length : 1,
                label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
            input.trigger('fileselect', [numFiles, label]);
        });

        $(".has_dependent").change(function (elem) {
            /*
              * for each inputs with related_inputs, hide all except the one corresponding
              * to input value
             */
            var dependents = $("[dependent-on='" + $(this).attr("name") + "']");
            var has_dep = $(this).val();
            console.log('Type obj:', $(this).attr('type'));
            if ($(this).attr('type') === 'checkbox' || $(this).attr('type') === 'radio') {
                if ($(this).prop('checked') === true)
                    has_dep = 'True';
                else
                    has_dep = 'False';
                console.log('In Array ', $(this).attr('type'), $(this).val());
            }
            console.log('Event fired ! ' + has_dep);
            dependents.each(function () {
                console.log($(this), $(this).attr('dependent-4-value'), has_dep);
                if ($(this).attr('dependent-4-value') === has_dep) {
                    $('#div_id_' + $(this).attr('name')).removeClass('hid_dep_parameter');
                    $('#tab_pane_' + $(this).attr('name')).removeClass('hid_dep_parameter');
                    $(this).removeAttr('disabled');
                } else {
                    $('#div_id_' + $(this).attr('name')).addClass('hid_dep_parameter');
                    $('#tab_pane_' + $(this).attr('name')).addClass('hid_dep_parameter');
                    $(this).attr('disabled', '');
                }
            });
        });
        window.wavesSuccessCallBack = function (response) {
            alert ('Initial');
            console.info("You job has been correctly submitted [id:" + response.slug + ']');
        }
        window.wavesErrorCallBack = function (error) {
            console.error("Job submission failed " + error.data)
        }
        function getCookie(cname) {
            var name = cname + "=";
            var decodedCookie = decodeURIComponent(document.cookie);
            var ca = decodedCookie.split(';');
            for (var i = 0; i < ca.length; i++) {
                var c = ca[i];
                while (c.charAt(0) == ' ') {
                    c = c.substring(1);
                }
                if (c.indexOf(name) == 0) {
                    return c.substring(name.length, c.length);
                }
            }
            return "";
        }
        window.submit_form = function (form) {
            return new Promise(function (resolve, reject) {
                var form_data = new FormData(form[0])
                $.ajax({
                    type: 'POST',
                    url: form.attr("action"),
                    processData: false,
                    contentType: false,
                    async: false,
                    cache: false,
                    data: form_data,
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader ("Authorization", "Token " + getCookie('waves_token'));
                    },
                    success: function (response) {
                        resolve(response)
                    },
                    error: function (error) {
                        reject(error)
                    }
                })
            })
        }

    })
})(jQuery || django.jQuery);

