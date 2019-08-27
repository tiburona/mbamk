//grab a form
const form = document.querySelector('.form-inline');

//grab an input
const inputEmail = form.querySelector('#inputEmail');

//config your firebase push
// const config = {
//     apiKey: "AIzaSyADO1Hwljz12mxUARkeks8Oz7s5xJX2zFs",
//     authDomain: "mbam-project.firebaseapp.com",
//     databaseURL: "https://mbam-project.firebaseio.com",
//     projectId: "mbam-project",
//     storageBucket: "mbam-project.appspot.com",
//     messagingSenderId: "308177551143"
// };

//create a functions to push
function firebasePush(input) {
    //prevents from braking
    if (!firebase.apps.length) {
        firebase.initializeApp(config);
    }

    //push itself
    var mailsRef = firebase.database().ref('emails').push().set(
        {
            mail: input.value
        }
    );

}

//push on form submit
if (form) {
    form.addEventListener('submit', function (evt) {
        evt.preventDefault();
        firebasePush(inputEmail);

        //shows alert if everything went well.
        return alert('Email address successfully submitted. Thank you!');
    })
}
