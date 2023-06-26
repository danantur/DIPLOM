document.getElementById("save").onclick = (ev) => {
    let hashed = window.location.hash.substr(1);
    alert(hashed);

    let form = null;
    switch(hashed) {
      case 'settings':
        form = document.forms.settings;
        break;
      default:
        form = document.forms.settings;
        break;
    }

    let data = new FormData();

    let inputs = form.getElementsByTagName("input")

    for (let i in inputs) {
        let input = inputs[i];
        if (input.type == "checkbox")
            data.set(input.name, input.checked)
        else
            data.set(input.name, input.value)
    }

    fetch(form.action, {method:'post', body: data});
}