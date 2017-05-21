$(document).ready(function(){

    if(window.location.href.indexOf("meritve") > 0) {
        $("select").each(function( index ) {
            var vrednost = $(this).attr("izbran");
            $("option[value*='"+vrednost+"']").attr('selected', 'selected');
        });
    }

});