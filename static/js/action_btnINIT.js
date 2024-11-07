document.getElementById("btnINIT").addEventListener("click", function() {
    fetch('/btn_initialize')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateButtonStates(data.btnSTATUS);
            // to do 
            // 1. Add LED status
            // 2. Add filled module ID
        })
        .catch(error => console.error('Error:', error));
});
