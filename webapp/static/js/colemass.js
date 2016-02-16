$('#refusing').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var chore = button.data('chorename') // Extract info from data-* attributes
  var pk = button.data('chorepk')
  var modal = $(this)
  modal.find('.modal-title').text('Refusing “' + chore + '”')
  modal.find('[name="pk"]').val(pk)
})

$('#editChore').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var chore = button.data('chorename') // Extract info from data-* attributes
  var pk = button.data('chorepk')
  var active = (button.data('active') == 'True')
  var modal = $(this)
  modal.find('.modal-title').text('Editing “' + chore + '”')
  modal.find('[name="name"]').val(chore)
  modal.find('[name="pk"]').val(pk)
  modal.find('[name="active"]').prop("checked", active)
})

$('#deleteChore').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget) // Button that triggered the modal
  var chore = button.data('chorename') // Extract info from data-* attributes
  var pk = button.data('chorepk')
  var modal = $(this)
  modal.find('.modal-title').text('Deleting “' + chore + '”')
  modal.find('[name="pk"]').val(pk)
})