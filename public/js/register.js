document.getElementById('registrationForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        firstName: e.target.firstName.value,
        lastName: e.target.lastName.value,
        dateOfBirth: e.target.dateOfBirth.value,
        email: e.target.email.value,
        phone: e.target.phone.value,
        address: e.target.address.value
    };

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        if (result.success) {
            document.getElementById('message').textContent = 'Registration successful!';
            e.target.reset();
        }
    } catch (error) {
        document.getElementById('message').textContent = 'Error: ' + error.message;
    }
}); 