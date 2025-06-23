documentdocument.querySelector('#login-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Get the values from the input fields
    const username = document.querySelector('#username').value;
    const password = document.querySelector('#password').value;

    // Perform a simple validation
    if (username === '' || password === '') {
        alert('Please fill in both fields.');
        return;
    }

    // Simulate a login process (replace with actual authentication logic)
    console.log('Logging in with:', { username, password });
    
    // Redirect to the dashboard after "logging in"
    window.location.href = '/dashboard';

    gtag('js', new Date());
    gtag('config', 'G-X0LTZT2HG9',{ 'debug_mode':true });
    gtag('event','login_custom',{
        'page_title': 'Login Page',
        'page_location': window.location.href,
        'page_path': window.location.pathname,
        'page_category': 'Home'
    })
});