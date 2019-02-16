from django.forms import widgets

class RangeInput(widgets.NumberInput):
    input_type = 'range'
