# AV Catalog Standardizer

A comprehensive system to convert diverse audio-visual product catalogs into a standardized 18-field format using Microsoft Phi, a lightweight LLM.

## 🌟 Key Features

- **Intelligent Field Mapping**: Uses Microsoft Phi LLM to understand and map fields based on content patterns, not just header names
- **Category Extraction**: Automatically identifies and extracts product categories from various catalog formats
- **Value Normalization**: Standardizes prices, units, and other values across catalogs
- **Multi-Format Support**: Handles Excel, CSV, and PDF catalog formats
- **Web Interface**: User-friendly web interface for uploading, reviewing, and exporting catalogs

## 🧠 LLM-Powered Approach

Unlike traditional ML approaches, our Microsoft Phi-based system leverages content understanding:

- **Content-based field identification**: Analyzes patterns in the data to determine field meanings
- **Contextual understanding**: Uses relationships between fields and content to strengthen mapping
- **Flexible structure recognition**: Identifies sections and categories based on format and content
- **Dynamic adaptation**: Processes new manufacturers without explicit training or templates

## 🛠️ Technical Overview

- **Microsoft Phi**: Leverages the Phi-2 (2.7B parameters) or Phi-1.5 (1.3B parameters) models
- **Modular Design**: Well-organized codebase with clear separation of concerns
- **Memory Efficient**: Processes catalogs in chunks to handle large files
- **Caching System**: Caches processed data and LLM responses for improved performance
- **Deployment Ready**: Optimized for deployment on Render's affordable hosting tier

## 📊 Standardized Output Schema

The system standardizes catalogs to the following 18-field format:

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| SKU | String | Primary product identifier | Yes |
| Short_Description | String | Brief product name/title | Yes |
| Long_Description | String | Detailed product description | No |
| Model | String | Model number or variant information | No |
| Category_Group | String | General product category group | No |
| Category | String | Specific product category | No |
| Manufacturer | String | Brand name | Yes |
| Manufacturer_SKU | String | Manufacturer's own product code | No |
| Image_URL | String | Link to product image | No |
| Document_Name | String | Associated document name | No |
| Document_URL | String | Link to product documentation | No |
| Unit_Of_Measure | String | Unit type (PAIR, EA, PIECE) | Yes |
| Buy_Cost | Decimal | Purchasing cost | No |
| Trade_Price | Decimal | Wholesale/dealer price | No |
| MSRP_GBP | Decimal | Retail price in British Pounds | No |
| MSRP_USD | Decimal | Retail price in US Dollars | No |
| MSRP_EUR | Decimal | Retail price in Euros | No |
| Discontinued | Boolean | Flag for discontinued products | No |

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/av-catalog-standardizer.git
cd av-catalog-standardizer
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Usage

#### Running the Web Interface

1. Start the web server
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:8080`

3. Follow the web interface to:
   - Upload a catalog file
   - Review field mappings
   - Preview standardized data
   - Export to your preferred format

#### Using as a Library

You can also use the core functionality in your own Python code:

```python
from core.data_processor import process_catalog

# Process a catalog file
transformed_data, validation_results, field_mappings = process_catalog("path/to/catalog.xlsx")

# Export to CSV
import pandas as pd
df = pd.DataFrame(transformed_data)
df.to_csv("standardized_catalog.csv", index=False)
```

## 🧪 Testing

Run the test suite:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=.
```

## 🏗️ Project Structure

```
av-catalog-standardizer/
├── app.py                      # Main application entry point
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
├── config/                     # Configuration files
├── core/                       # Core processing modules
├── prompts/                    # LLM prompt templates
├── services/                   # Business logic services
├── utils/                      # Utility functions
├── web/                        # Web interface
└── tests/                      # Test suite
```

## 💻 Web Interface

The web interface provides:

1. **Upload Screen**: File selection and format options
2. **Mapping Review**: LLM-generated mappings with confidence scores
3. **Preview Grid**: Sample of transformed data
4. **Export Options**: Download standardized catalog

## 🧩 Supported Manufacturers

The system is designed to work with catalogs from various manufacturers, including:

- KEF (Excel format with "#VALUE!" rows as category changes)
- Audio-Technica (Tabular with "Brand: Audio-Technica" and "AT - Network Series" as category indicators)
- Glensound (Multi-level section headers like "DANTE/RAVENNA/MILAN NETWORK AUDIO UNITS")
- And many more without explicit configuration

## 🔄 Extending for New Manufacturers

The system automatically adapts to new manufacturer formats without requiring code changes. The LLM-based approach analyzes content patterns rather than relying on rigid templates.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Microsoft for the Phi model
- All manufacturers whose catalog formats informed this project's design