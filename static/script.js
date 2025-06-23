document.querySelector('#login-form').addEventListener('submit', (event) => {

    gtag('event','login_custom',{
        'page_title': 'Login Page',
        'page_location': window.location.href,
        'page_path': window.location.pathname,
        'page_category': 'Home'
    });

        // Delay form submission slightly to let GA send the event
        setTimeout(() => {
            event.target.submit();
        }, 200);  // 200 ms is usually enough


});