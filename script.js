document.getElementById('nameForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const nameId = document.getElementById('nameId').value;
    const action = document.getElementById('action').value;
    const responseMessage = document.getElementById('responseMessage');

    try {
        const response = await fetch('save_name.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, nameId, action })
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

function editName() {
    const name = prompt('Enter the new name:');
    if (name) {
        document.getElementById('name').value = name;
        document.getElementById('action').value = 'update';
        document.getElementById('nameForm').submit();
    }
}

function deleteName() {
    const confirmation = confirm('Are you sure you want to delete this name?');
    if (confirmation) {
        document.getElementById('action').value = 'delete';
        document.getElementById('nameForm').submit();
    }
}
