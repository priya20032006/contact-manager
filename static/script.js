function confirmDelete() {

    return confirm(
        "Are you sure you want to delete this contact?"
    );

}


setTimeout(function () {

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        alert.style.display = "none";

    });

}, 4000);
