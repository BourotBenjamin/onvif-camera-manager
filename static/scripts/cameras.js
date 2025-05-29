let connectModal;
let errorToast;

function showError(message) {
    document.getElementById('errorToastBody').textContent = message;
    errorToast.show();
}

function showConnectModal(cameraIndex, ip, port) {
    document.getElementById('cameraIndex').value = cameraIndex;
    document.getElementById('connectError').classList.add('d-none');
    document.getElementById('connectSpinner').classList.add('d-none');
    document.getElementById('connectButton').disabled = false;
    connectModal.show();
}

function setCameraLoading() {
    const errorDiv = document.getElementById('connectError');
    const spinner = document.getElementById('connectSpinner');
    const connectButton = document.getElementById('connectButton');

    // Show loading state
    errorDiv.classList.add('d-none');
    spinner.classList.remove('d-none');
    connectButton.disabled = true;
}

function restartCamera(cameraIndex) {
    const errorDiv = document.getElementById('connectError');
    setCameraLoading();
    fetch(`/api/cameras/${cameraIndex}/restart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            connectModal.hide();
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
        updateCameraGrid();
    });
}
function connectToCamera() {
    const index = document.getElementById('cameraIndex').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('connectError');
    setCameraLoading()

    fetch(`/api/cameras/${index}/connect`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ index, username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            connectModal.hide();
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
        updateCameraGrid();
    });
}

function stopStream(index) {
    fetch(`/api/cameras/${index}/stop`, {
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

function updateCameraGrid() {
    fetch('/cameras/list')
        .then((response) => response.blob())
        .then((responseBlob) => responseBlob.text())
        .then((responseHtml) => {
            const grid = document.getElementById('camera-grid').parentElement;
            grid.innerHTML = responseHtml;
        })
        .catch(error => showError('Failed to update camera list: ' + error));
}