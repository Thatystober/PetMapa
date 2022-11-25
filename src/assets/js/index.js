import "../style/style.scss";

function floatingLabel() {
    const form = document.getElementById('form');
    

    form.addEventListener('focusin', (event) => {
        event.target.parentElement.classList.add("focus");
    });


    form.addEventListener('focusout', (event) => {
        if (event.target.value === ""){
            event.target.parentElement.classList.remove("focus");
        }
        
        if(document.querySelector(".form-select")){
            let option = document.querySelector(".form-select");

            if (option.options[option.selectedIndex].value === " "){
                option.parentElement.classList.remove("focus");
            }
        }
        
    });
}

if (document.getElementById('form')){
    floatingLabel();
}


function showPassword(){
    let iconShowPasswordOff = document.querySelectorAll('.icon-show-password-off');
    iconShowPasswordOff = [...iconShowPasswordOff];

    iconShowPasswordOff.forEach(element => {
        element.addEventListener('click', function() {
            let input = element.previousElementSibling;

            if(input.getAttribute('type') == 'password') {
                element.setAttribute('src', 'https://s3.sa-east-1.amazonaws.com/cdn.petmapa.com.br/assets/images/icon-password-show.svg');
                input.setAttribute('type', 'text');
    
            } else {
                element.setAttribute('src', 'https://s3.sa-east-1.amazonaws.com/cdn.petmapa.com.br/assets/images/icon-password-show-off.svg');
                input.setAttribute('type', 'password');
            }
        });
    });
}

if (document.querySelector('.icon-show-password-off')){
    showPassword();
}

export function sendCasePhotoImage({
    key,
    awsAccessKeyId,
    policy,
    signature,
    s3PostUrl
}) {

    const logo_image = document.getElementById('case_photo_image');
    var formdata = new FormData();
    formdata.append("key", `${key}`);
    formdata.append("AWSAccessKeyId", `${awsAccessKeyId}`);
    formdata.append("policy", `${policy}`);
    formdata.append("signature", `${signature}`);
    formdata.append("file", logo_image.files[0], logo_image.value);

    let message = document.querySelector(".photo-message");

    fetch(`${s3PostUrl}`, {
        method: 'POST',
        body: formdata
    })
    .then((response) => {
        message.classList.add("add");
        message.classList.remove("error-add");
        message.innerHTML = "Foto Adicionada!";
        // return response.json();
    })
    .catch((error) => {
        message.classList.remove("add");
        message.classList.add("error-add");
            
        console.log("Respondendo erro")
        message.innerHTML = "Erro ao enviar a foto!";
    })
};

export function clipBoardShareCase(button, domain, lat, lon){
    let text = `${domain}/home/${lat}/${lon}`;

    navigator.clipboard.writeText(text);
    button.value = "Copiado!";
    button.innerHTML = "Copiado!";

    const myTimeout = setInterval(buttonCopy, 5000);

    function buttonCopy() {
        button.innerHTML = "Copiar";
    }
    
}

export function closeButton(){
    let modal = document.querySelector(".modal")
    modal.classList.remove("active");
}

export function modalDeleteCase(domain, user) {
    const modal = document.querySelector(".modal");
    const content = document.querySelector(".change-modal-content");
    modal.classList.add('active');
    content.innerHTML = `
        <h2>Deseja excluir esse caso?</h2>
        
        <form action="${domain}/${user}" method="POST">
            <div class="buttons-case">
                <div class="button-with-icon"> 
                    <button type="submit">Sim</button>
                </div>
                <div class="button-with-icon"> 
                    <a id="button" class="close" onclick="bundle.closeButton();"><button>Não</button></a>
                </div>
            </div>
        </form>
        `
}
