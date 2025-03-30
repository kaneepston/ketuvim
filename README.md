# Ketuvim - Machine learning for the Jewish records from the Russian Empire

---

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python:** Version 3.8 or higher recommended.
* **pip:** Python package installer (usually comes with Python).
* **Git:** Version control system.
* **Git LFS:** Git Large File Storage. Install from [https://git-lfs.github.com/](https://git-lfs.github.com/). Verify installation with `git lfs version`.
* **eScriptorium:** Required if you intend to use the Segmentation (`ketuvim_segmenter`) or Recognition (`ketuvim_recognizer`) models. Follow the official installation guide: [https://escriptorium.readthedocs.io/en/latest/](https://escriptorium.readthedocs.io/en/latest/)

---

## Setup

1.  **Install eScriptorium:**
    If you need to run the `ketuvim_segmenter` or `ketuvim_recognizer` models, make sure your local eScriptorium installation is complete and working by following their official documentation linked in the Prerequisites section.


2.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/kaneepston/ketuvim.git](https://github.com/kaneepston/ketuvim.git)
    cd ketuvim
    ```

3.  **Initialize Git LFS:**
    This ensures large model files tracked by LFS are downloaded correctly.
    ```bash
    git lfs install
    # If LFS files don't download automatically on clone/pull, run:
    # git lfs pull
    ```

4.  **Install Python Dependencies (for the Web App):**
    It's highly recommended to use a Python virtual environment.
    ```bash
    # Create a virtual environment (optional but recommended)
    # python -m venv venv # Or use conda, etc.
    # Activate the environment (e.g., source venv/bin/activate on Linux/macOS)
    # source venv/bin/activate

    # Install required packages
    pip install -r web/requirements.txt
    ```


---

## Running the Models

This project provides different models with distinct execution methods:

### 1. Segmentation & Recognition Models (`ketuvim_segmenter`, `ketuvim_recognizer`)

These models are designed for use within a separate, locally installed **eScriptorium** application instance.

1.  Ensure you have installed and can run eScriptorium locally (see Setup step 4).
2.  The model files (e.g., `ketuvim_segmenter.*`, `ketuvim_recognizer.*`) are located in the `eScriptorium models/` directory within this repository. **[Optional: Add a note here if these files are large and tracked by LFS, e.g., "These files may be tracked by Git LFS."]**
3.  Launch your local eScriptorium instance.
4.  Use the eScriptorium interface to **manually upload** the models from the `eScriptorium models/` directory according to their documentation.

### 2. Ketuvim Correction Model (`ketuvim_nert`)

This Named Entity Recognition model is accessed via the built-in web application.

1.  Navigate to the web application directory:
    ```bash
    cd web
    ```
2.  Run the Flask application:
    ```bash
    python app.py
    ```
3.  Open your web browser and go to `http://127.0.0.1:5000` (or the address shown in the terminal output).

*The model files for `ketuvim_nert` are located within `web/models/ketuvim_nert/` and are managed using Git LFS.*