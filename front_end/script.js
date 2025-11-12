const BACKEND_URL = "http://127.0.0.1:8000";  // update if using different port

// 🌟 LOGIN FUNCTION
async function login() {
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const message = document.getElementById("message");

  if (!email || !password) {
    message.textContent = "⚠️ Please fill in all fields.";
    return;
  }

  try {
    const response = await fetch(`${BACKEND_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (response.ok) {
      // ✅ Store user details locally
      localStorage.setItem("userEmail", data.email);
      localStorage.setItem("userName", data.name || "User");

      message.textContent = "✅ Login successful! Redirecting...";
      
      // ✅ Redirect to dashboard page after 1 second
      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 1000);
    } else {
      message.textContent = `❌ ${data.message || "Invalid credentials"}`;
    }
  } catch (error) {
    console.error("Login error:", error);
    message.textContent = "⚠️ Server error. Please try again.";
  }
}

// 🌟 SIGNUP FUNCTION
async function signup() {
  const name = document.getElementById("signup-name").value;
  const email = document.getElementById("signup-email").value;
  const password = document.getElementById("signup-password").value;
  const message = document.getElementById("message");

  if (!name || !email || !password) {
    message.textContent = "⚠️ Please fill in all fields.";
    return;
  }

  try {
    const response = await fetch(`${BACKEND_URL}/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await response.json();

    if (response.ok) {
      message.textContent = "✅ Signup successful! Please log in now.";
      showLogin(); // switch back to login form
    } else {
      message.textContent = `❌ ${data.message || "Signup failed"}`;
    }
  } catch (error) {
    console.error("Signup error:", error);
    message.textContent = "⚠️ Server error. Please try again.";
  }
}

// 🌟 SWITCH FORMS
function showSignup() {
  document.getElementById("login-form").classList.add("hidden");
  document.getElementById("signup-form").classList.remove("hidden");
}

function showLogin() {
  document.getElementById("signup-form").classList.add("hidden");
  document.getElementById("login-form").classList.remove("hidden");
}
