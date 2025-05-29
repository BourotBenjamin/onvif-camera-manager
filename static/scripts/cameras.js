let connectModal;
let errorToast;

function showError(message) {
    document.getElementById('errorToastBody').textContent = message;
    errorToast.show();
}

function showConnectModal(ip, port) {
    document.getElementById('cameraIp').value = ip;
    document.getElementById('cameraPort').value = port;
    document.getElementById('connectError').classList.add('d-none');
    document.getElementById('connectSpinner').classList.add('d-none');
    document.getElementById('connectButton').disabled = false;
    connectModal.show();
}

function connectToCamera() {
    const ip = document.getElementById('cameraIp').value;
    const port = document.getElementById('cameraPort').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('connectError');
    const spinner = document.getElementById('connectSpinner');
    const connectButton = document.getElementById('connectButton');

    // Show loading state
    errorDiv.classList.add('d-none');
    spinner.classList.remove('d-none');
    connectButton.disabled = true;

    fetch('/api/connect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ip, port, username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            connectModal.hide();
            updateCameraGrid();
        } else {
            errorDiv.textContent = data.message;
            errorDiv.classList.remove('d-none');
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Connection failed: ' + error;
        errorDiv.classList.remove('d-none');
    })
    .finally(() => {
        // Reset loading state
        spinner.classList.add('d-none');
        connectButton.disabled = false;
    });
}

function stopStream(ip) {
    fetch(`/api/stop_stream/${ip}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        // Check if the response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new TypeError("Expected JSON response but got " + contentType);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            updateCameraGrid();
        } else {
            showError('Failed to stop stream: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to stop stream. Please try again.');
        // Force update the camera grid to refresh the state
        updateCameraGrid();
    });
}