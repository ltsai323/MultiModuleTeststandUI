const statusButtonMap = {
    "none": ["btnINIT"],
    "initialized": ["btnCON", "btnEXIT"],
    "connected": ["btnCONF", "btnEXIT"],
    "configured": ["btnEXEC", "btnCONF", "btnEXIT"],
    "running": ["btnSTOP", "btnEXIT"],
    "idle": ["btnCONF", "btnEXIT"],
    "error": ["btnEXIT"],
    "halt": ["btnCONN", "btnEXIT"]
};

function updateButtonStates(status) {
    console.log(`[updateButtonStatus] got status ${status}`);
    // Disable all buttons initially
    $(".ctrlbtn").prop("disabled", true);

    // Get the buttons to enable for the current status
    const buttonsToEnable = statusButtonMap[status] || [];
    buttonsToEnable.forEach(buttonId => {
        //console.log(`set button ${buttonId} !`);
        $("#" + buttonId).prop("disabled", false);
    });
}

//$(document).ready(function() {
//    // Initial status check
//    updateButtonStates("none");
//    //$.getJSON('/status', function(data) {
//    //    updateButtonStates(data.status);
//    //});
//
//    // Poll the status every 5 seconds for real-time updates
//    setInterval(function() {
//        updateButtonStates("connected"); }, 5000);
//    // getJSON for low frequency updating
//    //setInterval(function() {
//    //    $.getJSON('/status', function(data) {
//    //        updateButtonStates(data.status);
//    //    });
//    //}, 5000);
//});

