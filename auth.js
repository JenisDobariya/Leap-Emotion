// Firebase Configuration
const firebaseConfig = {
  apiKey: "AIzaSyC3YxeC7aLNsftjMIrZDZJwnfAf6Q_ByCg",
  authDomain: "leap-emotion.firebaseapp.com",
  projectId: "leap-emotion",
  storageBucket: "leap-emotion.firebasestorage.app",
  messagingSenderId: "518255542758",
  appId: "1:518255542758:web:563def6409131579589627"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
window.db = typeof firebase.firestore === 'function' ? firebase.firestore() : null;
const googleProvider = new firebase.auth.GoogleAuthProvider();

// Helper: show error message
function showError(message) {
  const errorDiv = document.getElementById('auth-error');
  if (errorDiv) {
    errorDiv.style.display = 'block';
    errorDiv.textContent = message;
  } else {
    alert(message);
  }
}

// Helper: clear error message
function clearError() {
  const errorDiv = document.getElementById('auth-error');
  if (errorDiv) errorDiv.style.display = 'none';
}

// ========== SIGNUP ==========
const signupForm = document.getElementById('signup-form');
if (signupForm) {
  signupForm.addEventListener('submit', function (e) {
    e.preventDefault();
    clearError();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showError("Email and password are required.");
      return;
    }

    if (password.length < 6) {
      showError("Password must be at least 6 characters.");
      return;
    }

    auth.createUserWithEmailAndPassword(email, password)
      .then(function (userCredential) {
        console.log("User created:", userCredential.user);
        window.location.href = "dashboard.html";
      })
      .catch(function (error) {
        console.error("Signup error:", error);
        if (error.code === 'auth/email-already-in-use') {
          showError("This email is already registered. Please sign in instead.");
        } else if (error.code === 'auth/weak-password') {
          showError("Password is too weak. Use at least 6 characters.");
        } else if (error.code === 'auth/invalid-email') {
          showError("Please enter a valid email address.");
        } else {
          showError(error.message);
        }
      });
  });
}

// ========== LOGIN ==========
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', function (e) {
    e.preventDefault();
    clearError();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    auth.signInWithEmailAndPassword(email, password)
      .then(function (userCredential) {
        console.log("User logged in:", userCredential.user);
        window.location.href = "dashboard.html";
      })
      .catch(function (error) {
        console.error("Login error:", error);
        if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password' || error.code === 'auth/invalid-credential') {
          showError("Invalid email or password. Please try again.");
        } else {
          showError(error.message);
        }
      });
  });
}

// ========== GOOGLE SIGN-IN ==========
var googleBtns = document.querySelectorAll('.btn-google');
googleBtns.forEach(function (btn) {
  btn.addEventListener('click', function (e) {
    e.preventDefault();
    e.stopPropagation();
    clearError();

    auth.signInWithPopup(googleProvider)
      .then(function (result) {
        console.log("Google sign-in success:", result.user);
        window.location.href = "dashboard.html";
      })
      .catch(function (error) {
        console.error("Google Auth Error:", error);
        if (error.code === 'auth/popup-closed-by-user') {
          showError("Sign-in popup was closed. Please try again.");
        } else if (error.code === 'auth/popup-blocked') {
          showError("Popup was blocked by your browser. Please allow popups for this site.");
        } else {
          showError(error.message);
        }
      });
  });
});

// ========== LOGOUT ==========
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
  logoutBtn.addEventListener('click', function (e) {
    e.preventDefault();
    auth.signOut()
      .then(function () {
        window.location.href = "login.html";
      })
      .catch(function (error) {
        console.error("Logout error:", error);
      });
  });
}

// ========== AUTH STATE: REDIRECT & NAV UPDATE ==========
var currentPage = window.location.pathname;

auth.onAuthStateChanged(function (user) {
  // If user IS logged in
  if (user) {
    // Redirect away from auth pages (no need to see login/signup if already signed in)
    if (currentPage.includes('login.html') ||
      currentPage.includes('start-free-trial.html') ||
      currentPage.includes('forgot-password.html')) {
      window.location.href = "dashboard.html";
      return;
    }

    // Update nav on dashboard
    if (currentPage.includes('dashboard')) {
      var userEmailDisplay = document.getElementById('user-email');
      if (userEmailDisplay) {
        userEmailDisplay.textContent = user.email || user.displayName || "User";
      }
    }

    // Update nav buttons on any page: replace "Sign in" / "Get early access" with person icon
    var navRight = document.querySelector('.nav-right');
    if (navRight) {
      navRight.innerHTML = '<a href="dashboard.html" class="nav-avatar" title="My Account" style="display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;background:#4361EE;color:white;text-decoration:none;transition:opacity 0.2s,transform 0.2s;box-shadow:0 4px 12px rgba(67, 97, 238, 0.4);"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg></a>';
    }

  } else {
    // If user is NOT logged in, kick them out of dashboard
    if (currentPage.includes('dashboard')) {
      window.location.href = "login.html";
    }
  }
  
  // Remove the anti-FOUC class once auth state is confirmed and resolved
  document.documentElement.classList.remove('auth-loading');
});

// ========== PASSWORD TOGGLE FUNCTION ==========
window.togglePass = function(btn) {
  const input = btn.previousElementSibling;
  if (!input) return;
  if (input.type === "password") {
    input.type = "text";
    btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';
  } else {
    input.type = "password";
    btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
  }
};