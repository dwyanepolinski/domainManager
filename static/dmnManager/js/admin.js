var selectedDomain = '';

$(function(){
	$('#dmn-table > tbody').selectable({
		filter: 'tr',
		selected: getDomainDetails
	});
	$('#dmn-browser').keyup(searchDomain);
	searchDomain();
	$('#addModal').on('hidden.bs.modal', function () {
		$('#ldap-result').html('');
		$('#get-user-data').val('');
	});
	phpList();
	vhostList();
	servicesList();
})

function doAjax(address, func, value1, value2 = null, value3 = null){
	$.ajax({
		type: 'POST',
		url: address,
		data: {
			'variable1': value1,
			'variable2': value2,
			'variable3': value3,
			'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val()
		},
		success: func,
		dataType: 'html'
	});
}

function getDomainDetails(){
	selectedDomain = $.trim($('.ui-selected').find('td:first').text());
	doAjax('/details/', getDomainDetailsSuccess, selectedDomain);
}

function getDomainDetailsSuccess(data){
	$('#dmn-details').html(data);
}

function searchDomain(){
	doAjax('/search/', searchDomainSuccess, $('#dmn-browser').val());
}

function searchDomainSuccess(data){
	$('#search-result').html(data);
	if(selectedDomain)
		$('#dmn-table tr:has(td:contains(\'' + selectedDomain + '\'))').addClass('ui-selected');
}

function switchPhp(domain, toPhpv){
	$('#info-window').text('Czekaj...');
	doAjax('/php/', switchPhpSuccess, domain, toPhpv);
}

function switchPhpSuccess(data){
	$('#info-window').html(data);
	searchDomain();
	getDomainDetails();
}

function deleteDomain(){
	$('#info-window').text('Czekaj...');
	doAjax('/delete/', deleteDomainSuccess, selectedDomain);
}

function deleteDomainSuccess(data){
	$('#info-window').html(data);
	selectedDomain = '';
	searchDomain();
	getDomainDetails();
}

function editButton(property, tdNumber, button){
	if($(button).children().text().trim() == 'Edytuj'){
		$(button).children().text(' Zapisz');
		tdValue = $('#' + tdNumber).html().trim();
		if(tdValue == '--Brak--')
			tdValue = '';
		$('#' + tdNumber).html('<input type="text" value="'+ tdValue +'" class="form-control input-sm">');
		$('.edit-btn:contains("Edytuj")').css('visibility', 'hidden');
	} else {
		attr = 0;
		if(property == 'Nazwa domeny')
			attr = 'name';
		if(property == 'Właściciel')
			attr = 'email';
		if(property == 'Numer kontaktowy')
			attr = 'number';
		if(property == 'Opis')
			attr = 'description';
		if(property == 'Komentarz')
			attr = 'comment';
		newValue = $('#' + tdNumber).children().val().trim();
		if(attr == 'name')
			doAjax('/edit/', switchPhpSuccess, selectedDomain, attr, newValue);
		else
			doAjax('/edit/', deleteDomainSuccess, selectedDomain, attr, newValue);
	}
}

function ldap(){
	doAjax('/ldap/', ldapSuccess, $('#get-user-data').val());
}

function ldapSuccess(data){
	$('#ldap-result').html(data);
	$('#load').button('reset');
}

function loading(button){
	$('#load').button({loadingText: 'Czekaj...'});
	$('#load').button('loading');
}

function createDomain(){
	newDomain = $('tr.new-dmn-tr').map(function(){
		if(Boolean($(this).find('input').length))
			value = $(this).find('input').val();
		else if(Boolean($(this).find('select').length))
			value = $(this).find('select').val();
		else
			value =  $('.val', this).text();
		return {
			key: $('.key', this).text(), val: value
		}
	});
	var domain = {};
	$.each(newDomain, function(key, val){
		domain[key] = val;
	});

	doAjax('/add/', createDomainSuccess, JSON.stringify(domain));
}

function createDomainSuccess(data){
	$('#add-domain-info').html(data);
	$('#info-window').html($('#add-domain-info').text());
	searchDomain();
}

function phpList(button, tdNumber){
	if($(button).text().trim() == 'Edytuj'){
		$(button).children().text(' Zapisz');
		path = $('#p' + tdNumber).text();
		$('#p' + tdNumber).html('<input type="text" value="'+ path +'" class="form-control input-sm">');
		$('.settings-btn:contains("Edytuj")').css('visibility', 'hidden');
		$('.settings-btn:contains("Usuń")').css('visibility', 'hidden');
		$('.settings-btn:contains("Dodaj")').css('visibility', 'hidden');
	}
	else
		doAjax('/settings/php/', phpListSuccess, $('#v' + tdNumber).text(), $('#p' + tdNumber).children().val());
}

function phpListSuccess(data){
	$('#subtab1').html(data);
	getDomainDetails();
}

function addPhp(){
	doAjax('/settings/php/add/', phpListSuccess, $('#new-php-v').val(), $('#new-php-p').val(), 'createnew');
}

function delPhp(tdNumber){
	doAjax('/settings/php/del/', phpListSuccess, $('#v' + tdNumber).text(), null, 'remove');
}

function vhostList(){
	if (!$('#vhost-path').length)
		doAjax('/settings/vhosts/', vhostListSuccess, null);
	else
		doAjax('/settings/vhosts/', vhostListSuccess, $('#vhost-path').val());
}

function vhostListSuccess(data){
	$('#subtab2').html(data);
}

function servicesList(){
	doAjax('/settings/services/', servicesListSuccess, null);
}

function servicesListSuccess(data){
	$('#subtab3').html(data);
}

function addService(){
	doAjax('/settings/services/add/', servicesListSuccess, $('#new-service').val(), 'createnew');
}

function delService(tdNumber){
	doAjax('/settings/services/del/', servicesListSuccess, $('#s' + tdNumber).text(), 'remove');
}

function database(button){
	$('#info-window').text('Czekaj...');
	if($(button).text() == 'Dodaj bazę')
		doAjax('/settings/db/add/', switchPhpSuccess, selectedDomain);
	else
		doAjax('/settings/db/del/', switchPhpSuccess, selectedDomain);
}

function https(button){
	$('#info-window').text('Czekaj...');
	if($(button).text() == 'HTTPS')
		doAjax('/settings/https/add/', switchPhpSuccess, selectedDomain);
	else
		doAjax('/settings/https/del/', switchPhpSuccess, selectedDomain);
}
