const socket = io.connect();

socket.on('business_data', (data) => {
    console.log('Received data:', data); // Debugging
    const table = document.getElementById('dataTable');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${data.name || 'None'}</td>
        <td>${data.address || 'None'}</td>
        <td><a href="${data.website || '#'}" target="_blank">${data.website || 'N/A'}</a></td>
        <td>${data.phone_number || 'None'}</td>
        <td>${data.email || 'None'}</td>
        <td>${data.facebook || 'None'}</td>
        <td>${data.instagram || 'None'}</td>
        <td>${data.twitter || 'None'}</td>
        <td>${data.linkedin || 'None'}</td>
    `;
    table.appendChild(row);
});


document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const response = await fetch('/start_scraping', {
        method: 'POST',
        body: formData
    });
    const result = await response.json();
    alert(result.message);
});