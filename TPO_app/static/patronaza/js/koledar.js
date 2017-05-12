function posodobiKoledar(d_mesec) {
    var l = leto;
    var m = mesec+d_mesec;
    if(m >= 12) {
        l += Math.floor(m/12)
        m = m%12
    }else if(m < 0) {
        l += Math.ceil(m/12)
        m = m%12
    }
    
    narisiKoledar(new Date(l, m, 1));
}

function narisiKoledar(datum) {
    var meseci = new Array("Januar", "Februar", "Marec", "April", "Maj", "Junij", "Julij", "Avgust", "Septemeber", "Oktober", "November", "December");

    if(datum == null)
        datum = new Date();
    
    danes = new Date();
    mesec = datum.getMonth();
    leto = datum.getFullYear();
    
    var koledar_html = "";
	koledar_html += "<table id='koledar_table'>"
	
	var next_arrow = '<div class="arrow-right" onclick="posodobiKoledar(1)"></div>'
    var prev_arrow = mesec > danes.getMonth() || leto > danes.getFullYear() ? '<div class="arrow-left" onclick="posodobiKoledar(-1)"></div>' : ''
    koledar_html += "<tr>";
    koledar_html += "<th colspan='7' id='mesec'>" + prev_arrow + " " + meseci[mesec] + " " + leto + " " + next_arrow + "</th>";
    koledar_html += "</tr>";
    koledar_html += "<tr id='dnevi'>";
	koledar_html += "<th>Ned</th>";
    koledar_html += "<th>Pon</th>";
    koledar_html += "<th>Tor</th>";
    koledar_html += "<th>Sre</th>";
    koledar_html += "<th>Čet</th>";
    koledar_html += "<th>Pet</th>";
    koledar_html += "<th>Sob</th>";
    koledar_html += "</tr>";

    datum = new Date(leto, mesec, 1);
    var prvi_dan_meseca = datum.getDay();
    var st_dni = new Date(leto, mesec+1, 0).getDate() + prvi_dan_meseca;
	var visina = Math.ceil(st_dni/7)
    
	var dan = 1
	for(var teden = 0; teden < visina; teden++) {
		koledar_html += "<tr class='week'>"
		for(var dan_v_tednu = 0; dan_v_tednu < 7; dan_v_tednu++, dan++) {
			var iso_dan = dan - prvi_dan_meseca
			koledar_html += "<td class='day"
			if(dan_v_tednu % 6 == 0) koledar_html += " weekend"
            if(leto == danes.getFullYear() && (mesec == danes.getMonth() && iso_dan < danes.getDate() || mesec < danes.getMonth()) || leto < danes.getFullYear()) {
                koledar_html += " past_day"
			}else if(leto == danes.getFullYear() && (mesec == danes.getMonth() && iso_dan > danes.getDate() || mesec > danes.getMonth()) || leto > danes.getFullYear()){
                koledar_html += " future_day"
			}else {
                koledar_html += " today"
			}
			
			if(dan > st_dni) {
				koledar_html += " other_month_day"
				iso_dan = dan - st_dni
			}else if(dan <= prvi_dan_meseca) {
				koledar_html += " other_month_day"
				iso_dan = new Date(leto, mesec, 0).getDate() - prvi_dan_meseca + dan
			}
			
			koledar_html += "'>"
            koledar_html += "<a href='?page=1'>" + iso_dan + "</a>"
            koledar_html += "</td>"
		}
		
		koledar_html += "</tr>"
	}
	
	koledar_html += "</table>"

    document.getElementById("koledar").innerHTML = koledar_html;
}