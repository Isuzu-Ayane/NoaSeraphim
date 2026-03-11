const https = require('https');
const fs = require('fs');

const req = https.get('https://aniporn.com/embed/150041/jk4/?campaign=11501', (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
        fs.writeFileSync('k:\\GoogleAI\\Noaplugin\\aniporn.html', data);
        console.log("Written to aniporn.html. Status Code:", res.statusCode);
    });
});
req.on('error', (e) => {
    console.error(e);
});
