let form = document.forms.user_settings;

form.onsubmit = function(event) {
    event.preventDefault();
    return false;
}

document.getElementById("save").onclick = (ev) => {
    let data = new FormData()

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