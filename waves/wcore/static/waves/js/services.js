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


        document.submit_waves_api_form = function (form, token) {
            /***
             * Provide simple WAVES-core api form submission using ajax JQuery, based on a classic token base authentication scheme
             *
             * @type {FormData}
             */
            var form_data = new FormData(form);
            //return new Promise(function (resolve, reject) {
                if (token != null) {
                    return $.ajax({
                        type: 'POST',
                        url: form.action,
                        processData: false,
                        contentType: false,
                        data: form_data,
                        beforeSend: function (xhr) {
                            // Add auth token to XHR request
                            xhr.setRequestHeader("Authorization", "Token " + token);
                        },
                        /*success: function (response) {
                            // return the response data from WAVES-core api service
                            resolve(response);
                        },
                        error: function (jqXHR, textStatus, error) {
                            // retrieve detail error message provided by WAVES-core api service
                            reject(jqXHR, textStatus, error);
                        }*/
                    })
                } else {
                    console.error("Token not provided, it's required for WAVES-core token based submission process");
                }
            //})
        }
        $(document).on('submit', "form.submit-ajax", function (event) {
            /**
             * Avoid default behavior on all form.submit-ajax submit event, may force ajax submission
             */
            event.preventDefault();
        })
    })
})(jQuery || django.jQuery);

