from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, TextAreaField, StringField, PasswordField, MultipleFileField, DecimalField, SelectField, HiddenField
from wtforms.validators import DataRequired, InputRequired, Length, Regexp, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget, TableWidget

class ChoiceObj(object):
    def __init__(self, name, choices):
        # this is needed so that BaseForm.process will accept the object for the named form,
        # and eventually it will end up in SelectMultipleField.process_data and get assigned
        # to .data
        setattr(self, name, choices)


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget()
    option_widget = CheckboxInput()
    # uncomment to see how the process call passes through this object
    # def process_data(self, value):
    #     return super(MultiCheckboxField, self).process_data(value)


class NFTForm(FlaskForm):
    name = StringField('NFT Name', validators=[DataRequired('What do you call this NFT?'),
                                               Length(max=256, message='NFT name cannot be longer than 256 characters.'),
                                               Regexp(r'^[a-zA-Z0-9()\s-]+$', message='NFT name must be alphanumeric and may have spaces, parentheses and dashes. Example: Time Magazine (2001) - Part 3')])
    price = DecimalField('Price (LYX)', default=0, validators=[InputRequired('How much is it worth?'),
                                                    NumberRange(min=0, max=1000000000, message='Price must be between 0 to 1000000000 LYX.')])
    description = TextAreaField('Description (optional)', render_kw={'style':'width: 100%;'}, validators=[
                                                        Optional(strip_whitespace=True),
                                                        Length(max=2048, message='Description must be less than 2048 characters long.'),
                                                        Regexp(r'^[a-zA-Z0-9,:()\s\.#\'@_-]+$', message='Description must be alphanumeric and can have spaces, commas, parentheses, colons, dashes, dots, single quotes, underlines, at signs, and number signs.')])
    # status = SelectField('Status', choices=[('ACTIVE', 'Active'), ('DEMOLISHED', 'Demolished')], default='ACTIVE')
    puzzle = HiddenField('puzzle')
    captcha = MultiCheckboxField('captcha',
                                 choices=[('1','1'),
                                          ('2', '2'),
                                          ('3', '3'),
                                          ('4', '4'),
                                          ('5', '5'),
                                          ('6', '6'),
                                          ('7', '7'),
                                          ('8', '8')])


class EditNFTForm(FlaskForm):
    name = StringField('NFT Name', validators=[DataRequired('What do you call this NFT?'),
                                               Length(max=256, message='NFT name cannot be longer than 256 characters.'),
                                               Regexp(r'^[a-zA-Z0-9()\s-]+$', message='NFT name must be alphanumeric and may have spaces, parentheses and dashes. Example: Time Magazine (2003) - Part 3')])
    price = DecimalField('Price (LYX)', default=0, validators=[InputRequired('How much is it worth?'),
                                                                NumberRange(min=0, max=1000000000, message='Price must be between 0 to 1000000000 LYX.')])
    description = TextAreaField('Description (optional)', render_kw={'style':'width: 100%;'}, validators=[
        Optional(strip_whitespace=True),
        Length(max=2048, message='Description must be less than 2048 characters long.'),
        Regexp(r'^[a-zA-Z0-9,:()\s\.#\'@_-]+$', message='Description must be alphanumeric and can have spaces, commas, parentheses, colons, dashes, dots, single quotes, underlines, at signs, and number signs.')])
    reason = TextAreaField('Edit Reason (optional)', render_kw={'style':'width: 100%;'}, validators=[
        Optional(strip_whitespace=True),
        Length(max=2048, message='Reason must be less than 2048 characters long.'),
        Regexp(r'^[a-zA-Z0-9,:()\s\.#\'@_-]+$', message='Reason must be alphanumeric and can have spaces, commas, parentheses, colons, dashes, dots, single quotes, underlines, at signs, and number signs.')])


class EditBiographyForm(FlaskForm):
    biography = TextAreaField('biography', render_kw={'style':'width: 100%;'}, validators=[
        Optional(strip_whitespace=True),
        Length(max=666, message='biography can\'t be more than 666 characters long.'),
        Regexp(r'^[a-zA-Z0-9,:()\s\.#\'@_-]+$', message='biography must be alphanumeric and can have spaces, commas, parentheses, colons, dashes, dots, single quotes, underlines, at signs, and number signs.')])


class PurchaseForm(FlaskForm):
    nft_id = HiddenField('ID')


class AddToPreviewForm(FlaskForm):
    file_id = HiddenField('File')
    nft_id = HiddenField('NFT')


class SearchForm(FlaskForm):
    raw_query = StringField('Search')
    mode = HiddenField('Mode')
    file_type = MultiCheckboxField('Only NFTs having at least one')


class UploadForm(FlaskForm):
    files = MultipleFileField('Select files (You can select multiple files at once)', validators=[InputRequired('Where are the files?')])


class FeedbackForm(FlaskForm):
    honesty = SelectField('Honesty', choices=[('NONE', 'Select...'),
                                              ('MALICIOUS', '✘✘ Malicious ✘✘'),
                                              ('MISLEADING', '✗✗ Misleading ✗✗'),
                                              ('GENUINE', '✔✔ Genuine ✔✔')], default='NONE')
    quality = SelectField('Quality', choices=[('0', 'Select...'),
                                              ('1', '★'),
                                              ('2', '★★'),
                                              ('3', '★★★'),
                                              ('4', '★★★★'),
                                              ('5', '★★★★★')], default='0')
