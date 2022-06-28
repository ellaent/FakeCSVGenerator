from django import forms
from django.forms import BaseInlineFormSet

from .models import DataSet, Schema


class SchemaForm(forms.ModelForm):
    SEPARATOR_CHOICES = (
        ("Comma", "Comma(,)"),
        ("Semicolon", "Semicolon(;)"),
        ("Tab", "Tab(/t)"),
        ("Space", "Space( )"),
        ("Pipe", "Pipe (|)"),
    )

    name = forms.CharField(label="Name")
    column_separator = forms.ChoiceField(
        choices=SEPARATOR_CHOICES, label="Column Separator"
    )

    class Meta:
        model = Schema
        fields = ("name", "column_separator")


class DataSetForm(forms.ModelForm):
    rows = forms.IntegerField(label="Rows")

    class Meta:
        model = DataSet
        fields = ["rows"]


class SchemaUpdateForm(forms.ModelForm):
    SEPARATOR_CHOICES = (
        ("Comma", "Comma(,)"),
        ("Semicolon", "Semicolon(;)"),
        ("Tab", "Tab(/t)"),
        ("Space", "Space( )"),
        ("Pipe", "Pipe (|)"),
    )

    name = forms.CharField(label="Name")
    column_separator = forms.ChoiceField(
        choices=SEPARATOR_CHOICES, label="Column Separator"
    )

    class Meta:
        model = Schema
        fields = ("name", "column_separator")


class ColumnInlineFormSet(BaseInlineFormSet):
    def clean(self):
        count = 0
        orders = []
        for form in self.forms:
            try:
                if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                    if form.cleaned_data["name"]:
                        pass
                    else:
                        raise forms.ValidationError("Name is empty.")
                    if form.cleaned_data["type"]:
                        pass
                    else:
                        raise forms.ValidationError("Type is empty.")
                    if form.cleaned_data["order"]:
                        pass
                    else:
                        raise forms.ValidationError("Order is empty.")
                    if (
                        form.cleaned_data["from_range"]
                        and form.cleaned_data["to_range"]
                    ):
                        if form.cleaned_data["type"] == 'Text':
                            if (
                                form.cleaned_data["from_range"] < 0
                                or form.cleaned_data["to_range"] < 0
                                or form.cleaned_data["from_range"]
                                >= form.cleaned_data["to_range"]
                            ):
                                raise forms.ValidationError("Incorrect column range.")
                        if form.cleaned_data["type"] == 'Integer':
                            if form.cleaned_data["from_range"] >= form.cleaned_data["to_range"]:
                                raise forms.ValidationError("Incorrect column range.")
                    count += 1
                    orders.append(form.cleaned_data["order"])
            except AttributeError:
                pass
            except KeyError:
                raise forms.ValidationError("Required fields are empty.")

        if len(orders) > 0:
            orders.sort()
            if orders[0] == 1:
                if len(orders) > 1:
                    for i in range(1, len(orders)):
                        if orders[i] - orders[i - 1] == 1:
                            pass
                        else:
                            raise forms.ValidationError(
                                "Please check the order of columns. It contains a mistake."
                            )
                else:
                    pass
            else:
                raise forms.ValidationError(
                    "Please check the order of columns. It contains a mistake."
                )
        return self.cleaned_data
