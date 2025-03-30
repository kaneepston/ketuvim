document.addEventListener('DOMContentLoaded', function() {

    const contributeButton = document.getElementById('contribute-btn');

    if (contributeButton) {
        const statusDiv = document.getElementById('status-message');
        const correctedTextArea = document.getElementById('corrected_text');
        const imageNameInput = document.getElementById('image_name');
        const inputTextHidden = document.getElementById('input_text_hidden');
        const saveUrl = contributeButton.dataset.saveUrl;

        contributeButton.addEventListener('click', function() {
            statusDiv.textContent = 'Saving...';
            statusDiv.className = 'message-box';

            const correctedText = correctedTextArea.value;
            const imageName = imageNameInput.value;
            const inputText = inputTextHidden.value;
            const filenameBase = imageName.split('.').slice(0, -1).join('.') || imageName;
            const txtFilename = filenameBase + '_corrected.txt';
            const formData = new FormData();
            formData.append('image_name', imageName);
            formData.append('input_text', inputText);
            formData.append('corrected_text', correctedText);

            fetch(saveUrl, { 
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.message || `Save failed with status ${response.status}`);
                    }).catch(() => {
                        throw new Error(`Save failed with status ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    try {
                        const blob = new Blob([correctedText], { type: 'text/plain;charset=utf-8' });
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = txtFilename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(link.href);
                    } catch (downloadError) {
                        console.error('Download failed:', downloadError);
                        statusDiv.textContent = 'Save successful, but download failed. Please copy text manually.';
                        statusDiv.className = 'message-box error-message';
                        return;
                    }

                    statusDiv.textContent = 'Thank you for your contribution. Your text has been saved for model improvement and downloaded.';
                    statusDiv.className = 'message-box success-message';

                } else {
                    throw new Error(data.message || 'Save operation failed.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                statusDiv.textContent = 'Error: ' + error.message;
                statusDiv.className = 'message-box error-message';
            });
        });
    } else {
    }
});