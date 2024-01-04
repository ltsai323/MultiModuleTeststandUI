<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clickable Buttons</title>
</head>
<body>

<!-- Button 1 -->
<div id='messageBox'>Orig</div>
<button id="btn1" onclick="clickBTN_disableMe('btn1',['btn1','btn2','btn3'])">access test module1</button>
<button id="btn2" onclick="clickBTN_disableMe('btn2',['btn1','btn2','btn3'])">access test module0</button>
<button id="btn3" onclick="clickBTN_disableMe('btn3',['btn1','btn2','btn3'])">nothing</button>


<script>
    function send_cmd(btnID) {
        fetch('/buttonClick_hub', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'button_id': btnID,
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Handle the response if needed
            console.log(data);
            //alert(data.status);
            showMessage(data.status);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    function clickBTN_disableMe(clickedBUTTONid, connectedBUTTONs) {
        // Disable the clicked button
        document.getElementById(clickedBUTTONid).disabled = true;

        // Enable all other buttons
        connectedBUTTONs.forEach(function(buttonId) {
            if (buttonId !== clickedBUTTONid) {
                document.getElementById(buttonId).disabled = false;
            }
        });
        send_cmd(clickedBUTTONid);

        // Add your additional logic here based on the clicked button
        console.log(clickedBUTTONid + " was clicked!");
    }
    function showMessage(mesg) {
        document.getElementById('messageBox').innerText = mesg;
    }
</script>

</body>
</html>
