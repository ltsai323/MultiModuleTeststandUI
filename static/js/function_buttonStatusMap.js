const statusButtonMap = {
    "none": ["#btnCONN", ".jobmode"],
    "connected": ["#btnINIT", "#btnEXIT", ".jobmode"],
    "initialized": ["#btnCONF", "#btnEXIT"],
    "configured": ["#btnEXEC", "#btnCONF", "#btnEXIT"],
    "running": ["#btnSTOP", "#btnEXIT"],
    "stopped": ["#btnCONF", "#btnEXIT"],
    "idle": ["#btnCONF", "#btnEXIT"],
    "error": ["#btnEXIT"],
    "halt": ["#btnINIT", "#btnEXIT", ".jobmode"],
    "wait": ["#btnEXIT"]
};
//    "none":
//    "connected":
//    "initialized":
//    "configured":
//    "running": Once all jobs are reported as running.
//    "stopped": Once all jobs are reported as stopped.
//    "idle":
//    "error":
//    "halt": 
//    "wait": used for initialize / run / stop / destroy buttons clicked. waiting for the result.


function updateButtonStates(status) {
    console.log(`[updateButtonStatus] got status ${status}`);
    // Disable all buttons initially
    $(".ctrlbtn").prop("disabled", true);
    $(".jobmode").prop("disabled", true);

    // Get the buttons to enable for the current status
    const buttonsToEnable = statusButtonMap[status] || [];
    buttonsToEnable.forEach(btnIdentifier => {
        //console.log(`set button ${btnIdentifier} !`);
        //#("#" + btnIdentifier).prop("disabled", false);
        if ('#' === btnIdentifier[0]) // search ID
        { document.getElementById(btnIdentifier.slice(1)).disabled = false; }
        if ('.' === btnIdentifier[0]) // search class
        {
          const buttons = document.querySelectorAll(btnIdentifier);
          if (buttons.length > 0) { buttons.forEach(btn => btn.disabled = false); }
        }
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

