let ESTAB_DATA = undefined;

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

const custom_select = () => {

	$('.config-menu select').each(function () {

		// Cache the number of options
		var $this = $(this),
			numberOfOptions = $(this).children('option').length;

		// Hides the select element
		$this.addClass('s-hidden');

		// Wrap the select element in a div
		$this.wrap('<div class="select"></div>');

		// Insert a styled div to sit over the top of the hidden select element
		$this.after('<div class="styledSelect z-depth-2"></div>');

		// Cache the styled div
		var $styledSelect = $this.next('div.styledSelect');

		// Show the first select option in the styled div
		$styledSelect.text($this.children('option').eq(0).text());

		// Insert an unordered list after the styled div and also cache the list
		var $list = $('<ul />', {
			'class': 'options'
		}).insertAfter($styledSelect);

		// Insert a list item into the unordered list for each select option
		for (var i = 0; i < numberOfOptions; i++) {
			$('<li />', {
				text: $this.children('option').eq(i).text(),
				rel: $this.children('option').eq(i).val()
			}).appendTo($list);
		}

		// Cache the list items
		var $listItems = $list.children('li');

		// Show the unordered list when the styled div is clicked (also hides it if the div is clicked again)
		$styledSelect.click(function (e) {
			e.stopPropagation();
			$('div.styledSelect.active').each(function () {
				$(this).removeClass('active').next('ul.options').hide();
			});
			$(this).toggleClass('active').next('ul.options').toggle();
		});

		// Hides the unordered list when a list item is clicked and updates the styled div to show the selected list item
		// Updates the select element to have the value of the equivalent option
		$listItems.click(function (e) {
			e.stopPropagation();
			$styledSelect.text($(this).text()).removeClass('active');
			$this.val($(this).attr('rel'));
			$list.hide();
			// alert($this.val());
			list_estab($this.val());
		});

		// Hides the unordered list when clicking outside of it
		$(document).click(function () {
			$styledSelect.removeClass('active');
			$list.hide();
		});

	});

}

const list_estab = (city = undefined) => {

	if (city == undefined)
		city = $("city").attr('value');
	else
		$(".estab-config").remove();

	$.get("/select_estab", { city: city }, (response) => {

		response = JSON.parse(response);
		ESTAB_DATA = response;
		response.map((value, index) => {
			$(`
				<div class="estab-config edit" id="ed-${value[1]}" value="${value[1]}">
					<p>${value[1]}</p>
					<div class="right">
						<a  id="e-${value[1]}" value="${value[1]}" class="btn-floating btn-large   primary_color edit" ><i class="fa fa-edit"></i></a>
						<a  value="${value[1]}" class="remove-estab btn-floating btn-large   red"><i class="fa fa-minus"></i></a>
					</div>
				</div>
			`).appendTo("#list-config").hide().fadeIn(1000);
		});

	});

}

const get_modal_content = (estab_name, cities) => {

	$('#edit-modal .modal-content').remove();
	var filtered_estab = ESTAB_DATA.filter((item, index) => {
		if (item[1] === estab_name)
			return item;
	});

	filtered_estab = filtered_estab[0];

	cities = cities.filter((item, index) => {
		if (item[0] !== filtered_estab[0])
			return item;
	});

	let modal = `
		<div class="modal-content">
			<primary_key style="display: none;" value="${filtered_estab[1]}" />
			<h5 class="modal-title">${filtered_estab[1]}</h5>
			<div class="row">
				<div style="margin: 20px 0;">
					<div class="input-field col s6">
						<select id="city_name" style="color: black !important;">
							<option value = "${filtered_estab[0]}" > ${filtered_estab[0]}</option>
							${cities.map((city_name, index) => { return `<option value="${city_name[0]}">${city_name[0]}</option>` })}
						</select>
						<label>Cidade</label>
					</div>
					<div class="input-field col s6">
						<input value="${filtered_estab[1]}" placeholder="Estabelecimento" id="estab_name" type="text" class="validate">
						<label class="active" for="estab_name">Estabelecimento</label>
					</div>
					<div class="input-field col s6">
						<input value="${filtered_estab[3]}" placeholder="Nome na Plataforma" id="web_name" type="text" class="validate">
						<label class="active" for="web_name">Nome na Plataforma</label>
					</div>
					<div class="input-field col s6">
						<input value="${filtered_estab[2]}" placeholder="Endereço" id="adress" type="text" class="validate">
						<label class="active" for="adress">Endereço</label>
					</div>
				</div>
				</div>
				<div class="modal-menu">
					<button id="cancel" class="primary_color btn-large" href="#" rel="modal:close">Cancelar</button>
					<button id="save-edit" class="primary_color   btn-large">Salvar Alterações</button>
				</div>
		</div>
	`

	$(modal).appendTo('#edit-modal');

	$("#edit-modal").modal({
		fadeDuration: 200,
	});
	$('select').formSelect();

}

const create_estab_element = (new_estab) => {

	var element =
		`
		<div class="estab-config edit" id="ed-${new_estab}" value="${new_estab}">
			<p>${new_estab}</p>
			<div class="right">
				<a  id="e-${new_estab}" value="${new_estab}" class="btn-floating btn-large   primary_color edit" ><i class="fa fa-edit"></i></a>
				<a  value="${new_estab}" class="remove-estab btn-floating btn-large   red"><i class="fa fa-minus"></i></a>
			</div>
		</div>
		`

	$("#list-config").prepend(element).hide().fadeIn(1000);

}

$(document).ready(function () {

	var city = undefined;
	$("select").formSelect();
	list_estab();
	custom_select();

	$(".cancel").click((e) => {

		e.preventDefault();
		let id = $(e.currentTarget).attr('href');
		var modal = $(id).modal();
		modal.closeModal();
		$(".jquery-modal").fadeOut(500);

	});

	$("#add-city").click((e) => {
		e.preventDefault();

		var new_city = $("#save-city").val();
		console.log({ new_city });

		$.get("/insert_city", { city_name: new_city }, (response) => {

			if (response.success) {

				alert(response.message);
				var modal = $("#add-city-modal").modal();
				modal.closeModal();
				$(".jquery-modal").fadeOut(500);
				var element = `<option value="${new_city}">${new_city}</option>`
				$("#city-select").append(element);
				window.location.reload(false);

			} else {
				alert(response.message);
			}

		});


	});

	$("#save-add").click((e) => {

		var city_name = $("#city_name-save").val();
		var estab_name = $("#estab_name-save").val();
		var web_name = $("#web_name-save").val();
		var adress = $("#adress-save").val();

		$.get("/insert_estab", { city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {

			if (response.success) {

				alert(response.message);
				var modal = $("#add-modal").modal();
				modal.closeModal();
				$(".jquery-modal").fadeOut(500);
				// $(".estab-config").remove();
				// list_estab();
				create_estab_element(estab_name);

			} else {
				alert(response.message);
			}

		});

	});

	$('body').on('click', '.edit', (event) => {
		event.preventDefault();

		if ($("#edit-modal").find('.modal-content').length !== 0) {
			$('#edit-modal .modal-content').remove();
			$('#edit-modal .modal-title').remove();
		}

		$.get("/select_city", (response) => {

			let estab_name = $(event.currentTarget).attr('value');
			get_modal_content(estab_name, JSON.parse(response));

		});

	});

	$('body').on('click', '#cancel', (event) => {
		event.preventDefault();

		var modal = $("#edit-modal").modal();
		modal.closeModal();
		$(".jquery-modal").fadeOut(500);
	});

	$('body').on('click', '#save-edit', (event) => {
		event.stopPropagation();
		event.preventDefault();
		var city_name = $("#city_name").val();
		var estab_name = $("#estab_name").val();
		var primary_key = $("primary_key").attr("value");
		var web_name = $("#web_name").val();
		var adress = $("#adress").val();

		$.get("/update_estab", { primary_key: primary_key, city_name: city_name, estab_name: estab_name, web_name: web_name, adress: adress }, (response) => {

			if (response.success) {

				alert(response.message);
				var modal = $("#edit-modal").modal();
				modal.closeModal();
				$(".jquery-modal").fadeOut(500);
				$(".estab-config").remove();
				list_estab();

			} else {
				alert(response.message);
			}

		});
	});

	$('body').on('click', 'a.estab', (e) => {

		$('.city').removeClass("select-item-active")

		let id = $(e.currentTarget).attr('id');

		if ($(`#${id}`).hasClass('select-item-active')) {

			$(`#${id}`).removeClass('select-item-active');

		} else {

			$(`#${id}`).addClass('select-item-active');

		}

	});

	$('.city').click((e) => {

		let id = $(e.currentTarget).attr('id');
		$('.estab').removeClass("select-item-active");

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
			$('ul.tabs').tabs('select', 'progress');
		}

	});

	$("#select").click(() => {

		$("#loader").show();

		if (!$('.city').hasClass("select-item-active")) {
			Materialize.toast('Selecione pelo menos um item para prosseguir.', 2000);
		} else {
			Materialize.toast('Pesquisa iniciada ...', 1000);
			$('ul.tabs').tabs('select', 'listagem');
			$(".tabs a").addClass('disable');
		}
		let city_name = $('.select-item-active').html();
		// Exemplo de requisição para o python
		$.get("/select_estab", { city: city_name }, (response) => {

			response = JSON.parse(response);
			response.map((value, index) => {
				$("#listagem  .select_wrapper").append(`<a class="select-item estab" id="E${index}" >${value[1]}</a>`)
			});
			$("#loader").hide();

		});

	});

	$("#select-all").click(() => {

		if (!$('.estab').hasClass("select-item-active")) {
			$(`.estab`).addClass('select-item-active');
		} else {
			$(`.estab`).removeClass('select-item-active');
		}

	});

	$("#back").click(() => {
		$('ul.tabs').tabs('select', 'pesquisar');
		$(".tabs a").addClass('enable');
		$(".estab").remove();
	});

	$('body').on('click', 'a.remove-estab', (e) => {

		e.stopPropagation();
		e.preventDefault();
		console.log($(this).attr('value'));
		let estab_name = $(e.currentTarget).attr('value');
		if (window.confirm(`Realmente deseja deletar o estabelecimento ${estab_name} permanentemente ?`)) {
			$.get("/remove_estab", { estab_name: estab_name }, (response) => {

				if (response.success) {
					$(e.currentTarget).parent().parent().fadeOut(250, () => {
						$(this).remove();
					});
					alert(response.message);
					console.log(response);
				} else {
					alert(response.message);
					console.log(response);
				}


			});
		}


	});


});
