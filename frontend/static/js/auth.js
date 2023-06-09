let hashed = window.location.hash.substr(1)

async function sendToken() {
    fetch('/auth/approve', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({"auth_data": hashed}),
    })
      .then(response => {
        if (response.ok)
            window.location.replace(window.location.origin + "/profile");
        else {
            alert("Ошибка авторизации!");
            window.location.replace(window.location.origin);
        }
      })
}

try {

    const res = sendToken()

} catch(err) {
    console.error(err);
    alert("Ошибка авторизации!");
    window.location.replace(window.location.origin);
}