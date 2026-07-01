document.addEventListener(
'DOMContentLoaded',
function(){

    const btn =
        document.getElementById('loginBtn');

    if(!btn) return;

    btn.addEventListener(
    'click',
    async function(){

        const username =
            prompt("Username");

        const password =
            prompt("Password");

        const formData =
            new FormData();

        formData.append(
            'username',
            username
        );

        formData.append(
            'password',
            password
        );

        const response =
            await fetch(
                '/login',
                {
                    method:'POST',
                    body:formData
                }
            );

        const result =
            await response.json();

        if(result.success){

            location.reload();

        }else{

            alert(
                'Đăng nhập thất bại\nSai tên đăng nhập hoặc mật khẩu.'
            );
        }

    });

});