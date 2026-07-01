document.addEventListener('DOMContentLoaded', function(){

    const placeholders =
        document.querySelectorAll('.image-placeholder');

    placeholders.forEach(function(placeholder){

        const img =
            placeholder.querySelector('img');

        const uploadBtn =
            placeholder.querySelector('.upload-btn');

        const editBtn =
            placeholder.querySelector('.edit-btn');

        const fileInput =
            placeholder.querySelector('.image-input');

        //----------------------------------
        // INITIAL STATE
        //----------------------------------

        if(img && img.getAttribute('src')){

            uploadBtn.style.display = 'none';
            editBtn.style.display = 'block';

        }else{

            uploadBtn.style.display = 'block';
            editBtn.style.display = 'none';

        }

        //----------------------------------
        // OPEN FILE DIALOG
        //----------------------------------

        uploadBtn.addEventListener(
            'click',
            () => fileInput.click()
        );

        editBtn.addEventListener(
            'click',
            () => fileInput.click()
        );

        //----------------------------------
        // IMAGE SELECTED
        //----------------------------------

        fileInput.addEventListener(
            'change',
            function(){

                const file = this.files[0];

                if(!file) return;

                const reader =
                    new FileReader();

                reader.onload = function(e){

                    let image = placeholder.querySelector('img');

                    if(!image){

                        image = document.createElement('img');

                        placeholder.insertBefore(
                            image,
                            fileInput
                        );
                    }

                    image.src = e.target.result;

                    uploadBtn.style.display = 'none';
                    editBtn.style.display = 'block';
                };

                const hotspot =
                    placeholder.dataset.hotspot;

                const imageType =
                    placeholder.dataset.type;

                const formData =
                    new FormData();

                formData.append(
                    'image',
                    file
                );

                formData.append(
                    'hotspot',
                    hotspot
                );

                formData.append(
                    'type',
                    imageType
                );

                fetch(
                    '/upload-hotspot-image',
                    {
                        method: 'POST',
                        body: formData
                    }
                )
                .then(response => response.json())
                .then(result => {

                    if(result.success){

                        alert(
                            'Image uploaded successfully'
                        );

                    }else{

                        alert(
                            'Upload failed'
                        );
                    }

                });

                reader.readAsDataURL(file);

            }
        );

    });

});