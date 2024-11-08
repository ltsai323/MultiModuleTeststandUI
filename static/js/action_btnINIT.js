document.getElementById("btnINIT").addEventListener("click", function() {
    fetch('/btn_initialize')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`[btnINIT] fetch current status ${JSON.stringify(data)}`);
            // function from static/js/function_buttonStatusMap.js
            updateButtonStates(data.btnSTATUS);
            Object.keys(data.LEDs).forEach(function(ledID) {
                var LEDstatus = data.LEDs[ledID];
                // function from static/js/function_LEDStatusMap.js
                updateLEDStatus(ledID,LEDstatus);
            });

            // update filled module ID
            Object.keys(data.moduleIDs).forEach(function(inputBOXid) {
                var moduleID = data.moduleIDs[inputBOXid];
                if ( moduleID )
                    document.getElementById(inputBOXid).value = moduleID;
            });
        })
        .catch(error => console.error('Error:', error));
});
