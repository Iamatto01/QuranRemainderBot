document.getElementById('nameForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const responseMessage = document.getElementById('responseMessage');

    try {
        const response = await fetch('save_name.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });

        if (response.ok) {
            const result = await response.json();
            responseMessage.textContent = result.message;
        } else {
            responseMessage.textContent = 'Error saving your name. Please try again.';
        }
    } catch (error) {
        responseMessage.textContent = 'An error occurred. Please try again later.';
    }
});
