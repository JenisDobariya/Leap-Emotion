// Services are now provided by the centralized /static/firebase-service.js
const auth = window.auth || firebase.auth();
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

// ========== GOOGLE SIGN-IN ==========
var googleBtns = document.querySelectorAll('.btn-google');
googleBtns.forEach(function (btn) {
  btn.addEventListener('click', function (e) {
    e.preventDefault();
    const googleProvider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(googleProvider)
      .then(function (result) {
        // Send the ID token to the server to start a session
        return result.user.getIdToken().then(idToken => {
            return fetch('/auth/google', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idToken: idToken, email: result.user.email })
            });
        });
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
            window.location.href = "/trial-dashboard";
        } else {
            alert("External auth failed. Please try standard login.");
        }
      })
      .catch(function (error) {
        console.error("Google Auth Error:", error);
        alert(error.message);
      });
  });
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

// ========== LOGOUT ==========
document.addEventListener('DOMContentLoaded', function() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
      e.preventDefault();
      window.location.href = '/logout';
    });
  }
});