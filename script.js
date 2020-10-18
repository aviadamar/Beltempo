function show(x) {
    document.querySelector(x).style.display = 'block';
}

function hide(x) {
    document.querySelector(x).style.display = 'none';
}


document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('#hamburger-bar').onclick =
        function () {
            var menu = document.querySelector("#hidden-menu");
            if (menu.style.display == 'flex') {
                menu.style.display = 'none';
            }
            else {
                menu.style.display = 'flex'
            }
        };
});



// https://stackoverflow.com/questions/5672320/trigger-events-when-the-window-is-scrolled-to-certain-positions
function hide_arrow() {

    if (document.body.scrollTop === 0) {
        document.getElementById("more-info-mark").style.display = "block";
    }

    if (window.pageYOffset > 300) {
        document.getElementById("more-info-mark").style.display = "none";
    }

    if (document.body.scrollTop > 1000) {
        document.getElementById("more-info-mark").style.display = "block";
    }
}

window.onscroll = hide_arrow

