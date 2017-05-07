/**
 * Created by David on 6. 05. 2017.
 */

$(document).ready(function() {
        var prejsna = null;
        var vsebina = null;
        $("#sestra").change(function () {
            if(prejsna == null) {
                prejsna = this.value;
                vsebina = this.options[this.selectedIndex].text;
                console.log(prejsna);
                console.log(vsebina);
                $('#nadomestnaSestra option[value="' + this.value + '"]').remove();
            }
            else{
                 $("#nadomestnaSestra").append('<option value="'+ prejsna +'">'+ vsebina +'</option>');
            prejsna = this.value;
            vsebina = this.options[this.selectedIndex].text;
            $('#nadomestnaSestra option[value="' + this.value + '"]').remove();
            }
        });
});