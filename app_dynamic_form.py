from flask_wtf import FlaskForm
from wtforms import RadioField, StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, InputRequired
import ConfigHandler
from DebugManager import BUG

def GetID(pymoduleNAME, loadedPARAMETER) -> str:
    return '|'.join([pymoduleNAME, loadedPARAMETER.key])

## how to add default from previous session? Is there any method to retrieve configured data?
def GetField(pymoduleNAME: str, loadedPARAMETER: ConfigHandler.LoadedParameterBasics):
    if loadedPARAMETER.parType == 'radiofield':
        return RadioField(
            label=loadedPARAMETER.key,
            id=GetID(pymoduleNAME, loadedPARAMETER),
            choices=[(opt, opt) for opt in loadedPARAMETER.options],
            validators=[InputRequired()]
        )
    if loadedPARAMETER.parType == 'stringfield':
        return StringField(
            label=loadedPARAMETER.key,
            id=GetID(pymoduleNAME, loadedPARAMETER),
            default='',
            validators=[InputRequired()] # asdf what is the reason that this only accept numbers
        )
    if loadedPARAMETER.parType == 'integerfield':
        return IntegerField(
            label=loadedPARAMETER.key,
            id=GetID(pymoduleNAME, loadedPARAMETER),
            default=0,
            validators=[InputRequired()]
        )

class UserInputForm(FlaskForm):
    pass
    #submit = SubmitField('Submit')

def UserInputFormFactory(pymoduleNAME, loadedPARlist: list) -> UserInputForm:
    class DynamicUserInputForm(UserInputForm):
        pass

    for loadedPARAMETER in loadedPARlist:
        field = GetField(pymoduleNAME, loadedPARAMETER)

        setattr(DynamicUserInputForm, loadedPARAMETER.key, field)

    return DynamicUserInputForm

if __name__ == "__main__":
    # valid code in app.py but not work directly execution
    parameters = [
        ConfigHandler.LoadedParameterIntegerField('int1', {}),
        ConfigHandler.LoadedParameterRadioField('opt1', {'options': [0, 1, 2, 3]})
    ]
    dynamic_form = UserInputFormFactory('aa', parameters)
    dyform = dynamic_form()

