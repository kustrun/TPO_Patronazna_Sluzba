$(document).ready(function(){

    function zdruziPodatke(objekt) {
        var result = new Array();
        $(objekt).each(function (i, item) {
            if ((typeof $(this).attr('aktivnost') != 'undefined') && ($(this).attr('aktivnost') != '') && ($(this).attr('aktivnost') != ' ')) {
                if (result.indexOf($(this).attr('aktivnost')) == -1) {
                    result.push(($(this).attr('aktivnost')));
                }
            }
        });

        for (i = 0; i < result.length; i++) {
            var len = $(objekt + '[aktivnost="' + result[i] + '"]').length
            $(objekt + '[aktivnost="' + result[i] + '"]').each(function (i) {
                if (i > 0) {
                    $(this).children().each(function (i) {
                        if (i == 0) {
                            $(this).remove();
                        }
                    });
                } else if (len > 1) {
                    $(this).children().each(function (i) {
                        if (i == 0) {
                            $(this).attr('rowspan', len);
                        }
                    });
                }
            });


        }
    }

    zdruziPodatke('.podatkiOtrocnice tr');
    zdruziPodatke('.podatkiNovorojencka tr');

});