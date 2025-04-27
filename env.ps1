# setup_env.ps1
Write-Host "Removing old environment..."
conda env remove -n py311env

Write-Host "Creating new environment..."
conda create -n py311env python=3.11 -y

Write-Host "Activating new environment..."
conda activate py311env

Write-Host "Adding conda-forge channel..."
conda config --add channels conda-forge
conda config --set channel_priority flexible

Write-Host "Installing conda packages..."
conda install -y pandas=2.0.3 numpy=1.24.4
conda install -y -c conda-forge openpyxl
conda install -y -c conda-forge networkx sympy pillow
conda install -y pip

Write-Host "Installing PyTorch CPU version (more stable on Windows)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

Write-Host "Installing transformers with Phi model support..."
# Using a version that definitely supports Phi models
pip install transformers==4.35.2 

Write-Host "Installing pip requirements..."
pip install flask==2.3.3
pip install Werkzeug==2.3.7
pip install PyPDF2==3.0.1
pip install accelerate
pip install pdfminer.six==20221105
pip install pdfplumber==0.10.2
pip install python-dotenv==1.0.0
pip install cryptography==41.0.3
pip install optimum==1.12.0
pip install bitsandbytes==0.41.1
pip install python-magic-bin==0.4.14
pip install jsonschema==4.19.0
pip install tqdm==4.66.1
pip install pytest==7.4.2
pip install pytest-cov==4.1.0

Write-Host "Environment setup complete!"