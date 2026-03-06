const https = require('https');

https.get('https://aniporn.com/embed/150041/jk4/?campaign=11501', (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
        const matches = data.match(/https:\/\/aniporn\.com\/get_file\/[^"']+/g) || [];
        const mp4s = data.match(/https:\/\/[^"']+\.mp4[^"']*/g) || [];
        console.log("Found get_file URLs:", matches.length > 0 ? matches[0] : "None");
        console.log("Found mp4 URLs:", mp4s.length > 0 ? mp4s[0] : "None");
    });
}).on('error', (e) => {
    console.error(e);
});
