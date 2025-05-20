document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const postJobBtn = document.getElementById('post-job-btn');

    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    const closeButtons = document.querySelectorAll('.close-btn');

    // Get modal content areas to prevent click propagation
    const loginModalContent = loginModal.querySelector('.modal-content');
    const registerModalContent = registerModal.querySelector('.modal-content');

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    const userInfoDisplay = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');

    const jobBoardContent = document.getElementById('job-board-content');
    const loginPrompt = document.getElementById('login-prompt');
    const promptLoginLink = document.getElementById('prompt-login-link');
    const promptRegisterLink = document.getElementById('prompt-register-link');

    const TOKEN_KEY = 'fruitpie_token';
    let currentUser = null;

    // --- Modal Handling ---
    function openModal(modal) {
        if (modal) modal.style.display = 'block';
    }

    function closeModal(modal) {
        if (modal) modal.style.display = 'none';
    }

    loginBtn.addEventListener('click', () => openModal(loginModal));
    registerBtn.addEventListener('click', () => openModal(registerModal));
    promptLoginLink.addEventListener('click', (e) => { e.preventDefault(); openModal(loginModal); });
    promptRegisterLink.addEventListener('click', (e) => { e.preventDefault(); openModal(registerModal); });

    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(loginModal);
            closeModal(registerModal);
        });
    });

    // We will handle click-outside-to-close with a document mousedown listener below
    // Remove the direct mousedown listeners on modal backdrops from the previous attempt

    // Prevent clicks/mousedowns that start inside modal content from propagating to document listener
    if (loginModalContent) {
        loginModalContent.addEventListener('mousedown', (event) => {
            console.log('Mousedown inside login modal content. Target:', event.target);
            event.stopPropagation();
            console.log('Propagation stopped for login modal content mousedown.');
        });
    }
    if (registerModalContent) {
        registerModalContent.addEventListener('mousedown', (event) => {
            console.log('Mousedown inside register modal content. Target:', event.target);
            event.stopPropagation();
            console.log('Propagation stopped for register modal content mousedown.');
        });
    }

    // Close modal if user mousedowns anywhere outside the modal content area
    document.addEventListener('mousedown', (event) => {
        console.log('Document mousedown. Target:', event.target);
        // Check for login modal
        if (loginModal.style.display === 'block') { // If modal is open
            console.log('Login modal is open. Checking if click was outside content.');
            if (loginModalContent && !loginModalContent.contains(event.target)) {
                console.log('Mousedown was outside login modal content. Closing login modal.');
                closeModal(loginModal);
            } else {
                console.log('Mousedown was inside login modal content or on content itself. Not closing.');
            }
        }

        // Check for register modal
        if (registerModal.style.display === 'block') { // If modal is open
            console.log('Register modal is open. Checking if click was outside content.');
            if (registerModalContent && !registerModalContent.contains(event.target)) {
                console.log('Mousedown was outside register modal content. Closing register modal.');
                closeModal(registerModal);
            } else {
                console.log('Mousedown was inside register modal content or on content itself. Not closing.');
            }
        }
    });

    // --- Token Management ---
    function saveToken(token) {
        localStorage.setItem(TOKEN_KEY, token);
    }

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function removeToken() {
        localStorage.removeItem(TOKEN_KEY);
    }

    // --- UI Updates ---
    function updateUIForLoggedInState() {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
        userInfoDisplay.style.display = 'inline-block';
        usernameDisplay.textContent = currentUser ? currentUser.username : 'User';
        
        jobBoardContent.classList.remove('blurred');
        loginPrompt.style.display = 'none';

        if (currentUser && currentUser.is_poster) {
            postJobBtn.style.display = 'inline-block';
        } else {
            postJobBtn.style.display = 'none';
        }
    }

    function updateUIForLoggedOutState() {
        loginBtn.style.display = 'inline-block';
        registerBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        userInfoDisplay.style.display = 'none';
        usernameDisplay.textContent = '';
        postJobBtn.style.display = 'none';
        
        jobBoardContent.classList.add('blurred');
        loginPrompt.style.display = 'block';
        currentUser = null;
    }

    // --- API Calls ---
    async function fetchCurrentUser() {
        const token = getToken();
        if (!token) return null;

        try {
            const response = await fetch('/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                return await response.json();
            } else {
                removeToken(); // Invalid or expired token
                return null;
            }
        } catch (error) {
            console.error('Error fetching current user:', error);
            return null;
        }
    }

    // Registration
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const is_seeker = document.getElementById('is_seeker').checked;
        const is_poster = document.getElementById('is_poster').checked;
        const errorEl = document.getElementById('register-error');
        const successEl = document.getElementById('register-success');
        errorEl.textContent = '';
        successEl.textContent = '';

        try {
            const response = await fetch('/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password, is_seeker, is_poster })
            });
            const data = await response.json();
            if (response.ok) {
                successEl.textContent = 'Registration successful! Please login.';
                registerForm.reset();
                setTimeout(() => {
                    closeModal(registerModal);
                    openModal(loginModal); 
                }, 2000);
            } else {
                errorEl.textContent = data.detail || 'Registration failed.';
            }
        } catch (error) {
            console.error('Registration error:', error);
            errorEl.textContent = 'An unexpected error occurred.';
        }
    });

    // Login
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        const errorEl = document.getElementById('login-error');
        errorEl.textContent = '';

        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                saveToken(data.access_token);
                currentUser = await fetchCurrentUser(); // Fetch user details after login
                if (currentUser) {
                    updateUIForLoggedInState();
                    closeModal(loginModal);
                    loginForm.reset();
                } else {
                     errorEl.textContent = 'Login successful, but failed to fetch user details.';
                     removeToken(); // Clean up partial login
                     updateUIForLoggedOutState();
                }
            } else {
                errorEl.textContent = data.detail || 'Login failed.';
            }
        } catch (error) {
            console.error('Login error:', error);
            errorEl.textContent = 'An unexpected error occurred.';
        }
    });

    // Logout
    logoutBtn.addEventListener('click', () => {
        removeToken();
        updateUIForLoggedOutState();
    });

    // --- Initial Page Load ---
    async function initializeApp() {
        currentUser = await fetchCurrentUser();
        if (currentUser) {
            updateUIForLoggedInState();
        } else {
            updateUIForLoggedOutState();
        }
    }

    initializeApp();
}); 