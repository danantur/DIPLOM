let hashed = window.location.hash.substr(1)

async function sendToken() {
    let response = await fetch('/auth/approve', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({"auth_data": hashed}),
    })

    if (response.ok) {
        let json = await response.json();
        window.location.replace(window.location.origin + json.redirect);
    }
    else {
        alert("Ошибка авторизации!");
        window.location.replace(window.location.origin);
    }
}

try {

    const res = sendToken()

} catch(err) {
    console.error(err);
    alert("Ошибка авторизации!");
    window.location.replace(window.location.origin);
}