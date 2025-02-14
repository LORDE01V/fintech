app.post('/register', async (req, res) => {
    const { firstName, lastName, dateOfBirth, email, phone, address } = req.body;
    
    try {
        const connection = await mysql.createConnection(config);
        const [result] = await connection.execute(
            `INSERT INTO Customers 
            (FirstName, LastName, DateOfBirth, Email, Phone, Address)
            VALUES (?, ?, ?, ?, ?, ?)`,
            [firstName, lastName, dateOfBirth, email, phone, address]
        );
        res.status(201).json({ success: true, customerId: result.insertId });
    } catch (error) {
        res.status(400).json({ success: false, error: error.message });
    }
}); 