var i = 0;
function move() {
	if (i == 0) {
		i = 1;
		var elem = document.getElementById("myBar");
		var width = 10;
		var id = setInterval(frame, 10);
		function frame() {
			if (width >= 100) {
				clearInterval(id);
				i = 0;
			} else {
				width++;
				elem.style.width = width + "%";
				elem.innerHTML = width + "%";
			}
		}
	}
}


$(document).ready(function () {

	var city = undefined;

	$('.estab').click((e) => {

		let id = $(e.currentTarget).attr('id');

		if ($(`#${id}`).hasClass('select-item-active')) {

			$(`#${id}`).removeClass('select-item-active');

		} else {

			$(`#${id}`).addClass('select-item-active');

		}

	});

	$('.city').click((e) => {

		let id = $(e.currentTarget).attr('id');
		console.log(city);
		if (city === undefined) {
			city = id;
			$(`#${id}`).addClass('select-item-active');
		} else {

			if (city === id) {
				$(`#${id}`).removeClass('select-item-active');
				city = undefined;
			} else {
				Materialize.toast('Você só pode selecionar um municipio por vez ...', 1000);
			}

		}

	});


	$("#start").click(() => {

		if (!$('.estab').hasClass("select-item-active")) {
			Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000);
		} else {
			Materialize.toast('Pesquisa iniciada ...', 1000);
			$('ul.tabs').tabs('select_tab', 'progress');
		}

	});

	$("#select").click(() => {

		if (!$('.city').hasClass("select-item-active")) {
			Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000);
		} else {
			Materialize.toast('Pesquisa iniciada ...', 1000);
			$('ul.tabs').tabs('select_tab', 'listagem');
			$(".tabs a").addClass('disable');
		}

	});

	$("#select-all").click(() => {

		if (!$('.estab').hasClass("select-item-active")) {
			$(`.estab`).addClass('select-item-active');
		} else {
			$(`.estab`).removeClass('select-item-active');
		}

	});

	$("#back").click(() => {
		$('ul.tabs').tabs('select_tab', 'pesquisar');
		$(".tabs a").addClass('enable');
	});

	// Exemplo de requisição para o python
	// $.get("/batatinha", function (data) {
	// 	console.log('batata');
	// });
});
