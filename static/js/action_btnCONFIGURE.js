// Ensure jQuery is loaded first
$(document).ready(function() {
    const storedMessage = sessionStorage.getItem('message');
    if (storedMessage) { 
        $('#messageInput').val(storedMessage); 
    }

    $('form').off('submit').on('submit', function(event) {
        event.preventDefault();  // Prevent default form submission
        var formData = $(this).serialize();
        console.log('Module IDs configured');

        $.ajax({
            type: 'POST',
            url: '/submit',
            data: formData,
            success: function(response) {
                if (response.status === 'success') {
                    console.log("Configure successfully: " + response.message);
                } else {
                    alert(response.message + "\n" + response.errors);
                    console.log("Configuration failed: " + response.errors);
                }
            },
            error: function() {
                alert('An error occurred. Please try again.');
            }
        });
    }); // end of submit handler
}); // end of document ready


