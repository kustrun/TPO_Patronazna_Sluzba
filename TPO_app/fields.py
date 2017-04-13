from django.forms import ModelChoiceField

class TipObiskaModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.tip

class VrstaObiskaModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.naziv