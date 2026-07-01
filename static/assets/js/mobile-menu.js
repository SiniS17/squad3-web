document.addEventListener("DOMContentLoaded", function () {

    const menuBtn = document.getElementById("mobile-menu-toggle");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("mobile-overlay");

    menuBtn.addEventListener("click", function () {

        sidebar.classList.toggle("mobile-active");
        overlay.classList.toggle("active");

    });

    overlay.addEventListener("click", function () {

        sidebar.classList.remove("mobile-active");
        overlay.classList.remove("active");

    });

});