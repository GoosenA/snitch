function edit_sheet() {
    var state = document.getElementById("sheet_id").disabled
    if (state) {
        document.getElementById("sheet_id").disabled = false;
        document.getElementById("sheet_id_submit").style.display = "inline";
        document.getElementById("sheet_id_remove_btn").style.display = "inline";
        document.getElementById("sheet_id_edit").innerHTML = "Cancel";
    }
    else {
        document.getElementById("sheet_id").disabled = true;
        document.getElementById("sheet_id").value = document.getElementById("sheet_id_original").value;
        document.getElementById("sheet_id_submit").style.display = "none";
        document.getElementById("sheet_id_remove_btn").style.display = "none";
        document.getElementById("sheet_id_edit").innerHTML = "Edit";
    }
}

function remove_sheet_id() {
    alert('Disconnecting Sheet ID');
    var form = document.getElementById("edit_form");
    form.action = "/sheet/delete"
    form.submit()
}