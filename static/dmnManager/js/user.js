function switchPhp(domain, phpv){
	$('#user-alert').text('Czekaj...');
	$.ajax({
		type: 'POST',
		url: '/php/',
		data: {
			'variable1': domain,
			'variable2': phpv,
			'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val()
		},
		success: function(data){
			$('#user-alert').html(data);
			if(data.split(' ')[0] == 'Pomyślnie')
				$('#6').text(phpv.substring(4));
		},
		dataType: 'html'
	});
}
