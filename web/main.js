document.getElementById('sidebar-hide').addEventListener("click", hideSidebar);

function hideSidebar() {
  document.getElementById('sidebar').style.display = 'none';
}

document.getElementById('sidebar-show').addEventListener("click", showSidebar);

function showSidebar() {
  document.getElementById('sidebar').style.display = 'block';
}


eel.get_user_details()(showUserDetails);
function showUserDetails (userName) {
  document.getElementById('admin-name').innerText = userName;
}

eel.expose(logout);
function logout() {
  alert("Logout Successfully");
  window.location.href = 'login.html';
}

function show_image() {
	eel.show_image()(setImage);
}

function setImage(base64) {
	document.getElementById("qr").src = base64;
}
