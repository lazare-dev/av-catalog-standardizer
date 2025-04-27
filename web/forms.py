"""
AV Catalog Standardizer - Web Forms
---------------------------------
Form definitions for the web interface.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired

from config.settings import ALLOWED_EXTENSIONS

class UploadForm(FlaskForm):
    """Form for uploading a catalog file."""
    file = FileField(
        'Catalog File',
        validators=[
            FileRequired(),
            FileAllowed(list(ALLOWED_EXTENSIONS), 'Only supported file formats allowed')
        ]
    )
    submit = SubmitField('Upload')

class ExportForm(FlaskForm):
    """Form for exporting processed data."""
    format = SelectField(
        'Export Format',
        choices=[
            ('csv', 'CSV'),
            ('xlsx', 'Excel'),
            ('json', 'JSON')
        ],
        validators=[DataRequired()]
    )
    include_all = BooleanField('Include All Fields', default=True)
    submit = SubmitField('Export')

class MappingForm(FlaskForm):
    """Form for updating field mappings."""
    original_field = StringField('Original Field', validators=[DataRequired()])
    standard_field = SelectField(
        'Standard Field',
        choices=[
            ('', '-- Not Mapped --'),
            ('SKU', 'SKU'),
            ('Short_Description', 'Short_Description'),
            ('Long_Description', 'Long_Description'),
            ('Model', 'Model'),
            ('Category_Group', 'Category_Group'),
            ('Category', 'Category'),
            ('Manufacturer', 'Manufacturer'),
            ('Manufacturer_SKU', 'Manufacturer_SKU'),
            ('Image_URL', 'Image_URL'),
            ('Document_Name', 'Document_Name'),
            ('Document_URL', 'Document_URL'),
            ('Unit_Of_Measure', 'Unit_Of_Measure'),
            ('Buy_Cost', 'Buy_Cost'),
            ('Trade_Price', 'Trade_Price'),
            ('MSRP_GBP', 'MSRP_GBP'),
            ('MSRP_USD', 'MSRP_USD'),
            ('MSRP_EUR', 'MSRP_EUR'),
            ('Discontinued', 'Discontinued')
        ]
    )
    submit = SubmitField('Update')