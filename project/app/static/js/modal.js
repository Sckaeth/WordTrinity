// Modal.js

// JQuery objects
let alert_div = $(".account__alert");
let results_modal = $("#results-modal");
let info_modal = $("#info-modal");

// Event listeners
info_modal.on("show.bs.modal", triggerModal);
info_modal.on("hidden.bs.modal", () => { $(".modal-section").hide() });

// Prevent button focus on modal close
$(".modal").on("hidden.bs.modal", (event) => { event.stopImmediatePropagation() });

// Vary modal content based on button data-attributes
function triggerModal(event) {
    let target = event.relatedTarget;
    $(target.getAttribute("data-bs-show")).show();
}

// Displays alert for modal
function displayAlert(msg) {
	let btn = "<button type = 'button' class='btn-close' data-bs-dismiss='alert' aria-label='Close'></button>";
	alert_div.html("<div class='alert alert-dismissible' role='alert'>" + msg + btn + "</div>");
}

// Activate twitter button
results_modal.one("show.bs.modal", async function () {
    !(function (d, s, id) {
        var js,
            fjs = d.getElementsByTagName(s)[0];
        if (!d.getElementById(id)) {
            js = d.createElement(s);
            js.id = id;
            js.src = "https://platform.twitter.com/widgets.js";
            fjs.parentNode.insertBefore(js, fjs);
        }
    })(document, "script", "twitter-wjs");
});