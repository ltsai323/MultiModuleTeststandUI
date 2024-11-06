const statusButtonMap = {
    "none": ["btnINITIALIZE"],
    "initialized": ["btnCONNECT", "btnDESTROY"],
    "connected": ["btnCONFIGURE", "btnDESTROY"],
    "configured": ["btnRUN", "btnCONFIGURE", "btnDESTROY"],
    "running": ["btnSTOP", "btnDESTROY"],
    "idle": ["btnCONFIGURE", "btnDESTROY"],
    "error": ["btnDESTROY"],
    "halt": ["btnCONNECT", "btnDESTROY"]
};

function updateButtonStates(status) {
    // Disable all buttons initially
    $(".ctrlbtn").prop("disabled", true);

    // Get the buttons to enable for the current status
    const buttonsToEnable = statusButtonMap[status] || [];
    buttonsToEnable.forEach(buttonId => {
        $("#" + buttonId).prop("disabled", false);
    });
}

$(document).ready(function() {
    // Initial status check
    $.getJSON('/status', function(data) {
        updateButtonStates(data.status);
    });

    // Poll the status every 5 seconds for real-time updates
    setInterval(function() {
        $.getJSON('/status', function(data) {
            updateButtonStates(data.status);
        });
    }, 5000);
});

