$(document).ready(function(){

    var result = new Array();
    $('tr').each(function(i,item) {
        console.log($(this).attr('aktivnost'));

        if( (typeof $(this).attr('aktivnost') != 'undefined') && ($(this).attr('aktivnost') != '') && ($(this).attr('aktivnost') != ' ') ) {
            if(result.indexOf($(this).attr('aktivnost')) == -1){
                result.push(($(this).attr('aktivnost')));
            }
        }
    });

    for (i = 0; i < result.length; i++) {
        var len = $('tr[aktivnost="' + result[i] + '"]').length
        $('tr[aktivnost="' + result[i] + '"]').each(function(i) {
            if (i > 0) {
                $(this).children().each(function(i){
                    if(i == 0) {
                        $(this).remove();
                    }
                });
            } else if(len > 1) {
                $(this).children().each(function(i){
                    if(i == 0) {
                        $(this).attr('rowspan',len);
                    }
                });
            }
         });


    }

});