from flask_wtf import FlaskForm
from wtforms import RadioField, StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, InputRequired
import ConfigHandler

def GetField(pymoduleNAME:str, loadedPARAMETER:ConfigHandler.LoadedParameterBasics):
    if loadedPARAMETER.parType == 'radiofield':
        print(1)
        return   RadioField(label=loadedPARAMETER.key,
                           id='|'.join([pymoduleNAME,loadedPARAMETER.key]),
                           choices=[(opt,opt) for opt in loadedPARAMETER.options],
                           validators=[InputRequired()])
    if loadedPARAMETER.parType == 'stringfield':
        print(2)
        return  StringField('|'.join([pymoduleNAME,loadedPARAMETER.key]),
                            default='',
                            validators=[InputRequired()])
    if loadedPARAMETER.parType == 'integerfield':
        print(3)
        return IntegerField(label=loadedPARAMETER.key,
                            id='|'.join([pymoduleNAME,loadedPARAMETER.key]),
                            default=0,
                            validators=[InputRequired()])

class UserInputForm(FlaskForm):
    opt1 = RadioField('Option 1', choices=[('val1', 'val1'), ('val2', 'val2'), ('val3', 'val3')], validators=[InputRequired()])
    opt2 = StringField('Option 2', default='mesg', validators=[DataRequired()])
    opt3 = IntegerField('Option 3', default=27, validators=[DataRequired()])
    section2_opt1 = StringField('Section 2 Option 1', default='mesg', validators=[DataRequired()])
    submit = SubmitField('Submit')
def UserInputFormFactory(pymoduleNAME, loadedPARlist:list) -> dict:
    '''
    # input var
    [ LoadedparameterBasic(), LoadedParameterIntegerField(), LoadedParameterRadioField() ],
    '''
    o = []
    loaded_fields = ( GetField(pymoduleNAME,loadedPARAMETER) for loadedPARAMETER in loadedPARlist )
    class UserInputForm(FlaskForm):
        def __init__(self,loadedPARlist):
            self.my_config_names = []
            for loadedPAR in loadedPARlist:
                name = loadedPAR.kwargs['label']
                setattr(self, name, loadedPAR)
                self.my_config_names.append(name)


    return {pymoduleNAME:UserInputForm(loaded_fields)}
            
            
            
            
        

if __name__ == "__main__":
    cc = ConfigHandler.LoadedParameterIntegerField('int1', {})
    aa = ConfigHandler.LoadedParameterRadioField('opt1', {'options': [0,1,2,3]})
    #print(GetField('ctype', aa))
    ff = [cc,aa]
    print(UserInputFormFactory('testing', ff)['testing'].__dir__())



