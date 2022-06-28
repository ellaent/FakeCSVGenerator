import os

import boto3
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.forms import inlineformset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)
from django.views.generic.edit import FormMixin

from .forms import ColumnInlineFormSet, DataSetForm, SchemaForm, SchemaUpdateForm
from .models import Column, DataSet, Schema
from .tasks import generate_fake_csv
from decouple import config

SchemaInlineFormSet = inlineformset_factory(
    Schema,
    Column,
    fields=("name", "type", "order", "from_range", "to_range"),
    labels={
        "name": "Column name",
        "type": "Type",
        "order": "Order",
        "from_range": "From",
        "to_range": "To",
    },
    can_order=False,
    can_delete=True,
    formset=ColumnInlineFormSet,
)


class SchemaListView(LoginRequiredMixin, ListView):
    model = Schema
    ordering = ["schema_id"]
    template_name = "index.html"
    login_url = "/users/login/"
    redirect_field_name = "login"

    def get_queryset(self):
        self.queryset = Schema.objects.all().order_by("schema_id")
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(SchemaListView, self).get_context_data()
        context["schemas"] = Schema.objects.get_queryset()
        return context


class SchemaCreateView(CreateView, LoginRequiredMixin):
    form_class = SchemaForm
    template_name = "schema_create.html"

    def get_context_data(self, **kwargs):
        context = super(SchemaCreateView, self).get_context_data(**kwargs)
        context["schema"] = True
        context["model"] = "schema"
        if self.request.POST:
            context["form"] = SchemaForm(self.request.POST)
            context["inlines"] = SchemaInlineFormSet(self.request.POST)
        else:
            context["form"] = SchemaForm()
            context["inlines"] = SchemaInlineFormSet()
            context["inlines"].extra = 1
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        inlines = context["inlines"]
        if inlines.is_valid() and form.is_valid():
            schema = form.save()
            for i in inlines:
                if i.is_valid() and i.cleaned_data != {}:
                    if i.cleaned_data["DELETE"] == True:
                        pass
                    else:
                        column = i.save(commit=False)
                        column.schema = Schema.objects.filter(
                            schema_id=schema.schema_id
                        )[0]
                        i.save()

            return HttpResponseRedirect(reverse_lazy("home"))
        else:
            return self.render_to_response(self.get_context_data(form=form))


class SchemaOverview(DetailView, LoginRequiredMixin):
    model = Schema
    template_name = "schema_overview.html"
    pk_url_kwarg = "schema_id"
    schema = None

    def get_context_data(self, **kwargs):
        schema = Schema.objects.filter(schema_id=self.kwargs["schema_id"])[0]
        context = {"schema": schema}
        return context


class DataSetListView(FormMixin, ListView, LoginRequiredMixin):
    model = DataSet
    form_class = DataSetForm
    ordering = ["dataset_id"]
    template_name = "datasets.html"

    def get_queryset(self):
        schema_id = self.kwargs.get("schema_id")
        schema = Schema.objects.filter(schema_id=schema_id)[0]
        self.queryset = DataSet.objects.filter(schema=schema)
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(DataSetListView, self).get_context_data()
        context["datasets"] = self.get_queryset()
        if self.request.POST:
            context["form"] = DataSetForm(self.request.POST)
        else:
            context["form"] = DataSetForm()
        if "task_id" in self.request.session:
            context["task_id"] = self.request.session["task_id"]
            if "previous_task_id" in self.request.session:
                if (
                    self.request.session["previous_task_id"]
                    == self.request.session["task_id"]
                ):
                    context["task_id"] = None
            self.request.session["previous_task_id"] = context["task_id"]
        return context

    def form_valid(self, form):
        schema_id = self.kwargs.get("schema_id")
        dataset = form.save(commit=False)
        dataset.schema = Schema.objects.filter(schema_id=schema_id)[0]
        dataset.status = "Processing"
        form.save()
        status = generate_fake_csv.delay(dataset.dataset_id)
        self.request.session["task_id"] = status.task_id
        return HttpResponseRedirect(self.request.path_info)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SchemaUpdateView(UpdateView, LoginRequiredMixin):
    model = Schema
    form_class = SchemaUpdateForm
    pk_url_kwarg = "schema_id"
    template_name = "schema_edit.html"

    def get_context_data(self, **kwargs):
        context = super(SchemaUpdateView, self).get_context_data(**kwargs)
        context["model"] = "schema"
        schema = Schema.objects.filter(schema_id=self.kwargs["schema_id"]).first()
        context["schema"] = schema
        if self.request.POST:
            context["form"] = SchemaUpdateForm(self.request.POST)
            context["inlines"] = SchemaInlineFormSet(self.request.POST)
        else:
            schema_columns = Column.objects.filter(schema=schema)
            context["inlines"] = SchemaInlineFormSet(
                initial=[
                    {
                        "name": column.name,
                        "type": column.type,
                        "order": column.order,
                        "from_range": column.from_range,
                        "to_range": column.to_range,
                    }
                    for column in schema_columns
                ]
            )
            context["inlines"].extra = len(schema_columns) | 1
        return context

    def get_object(self, *args, **kwargs):
        schema = get_object_or_404(Schema, pk=self.kwargs["schema_id"])
        return schema

    def get_initial(self):
        initial = super(SchemaUpdateView, self).get_initial()
        schema_object = self.get_object()
        initial["name"] = schema_object.name
        initial["column_separator"] = schema_object.column_separator
        return initial

    def form_valid(self, form):
        context = self.get_context_data()
        schema = context["schema"]
        inlines = context["inlines"]
        if inlines.is_valid() and form.is_valid():
            new_schema_data = form.save(commit=False)
            schema.name = new_schema_data.name
            schema.column_separator = new_schema_data.column_separator
            schema.save()
            old_columns = Column.objects.filter(schema=schema)
            for column in old_columns:
                column.delete()
            for i in inlines:
                if i.is_valid() and i.cleaned_data != {}:
                    if i.cleaned_data["DELETE"] == True:
                        pass
                    else:
                        column = i.save(commit=False)
                        column.schema = Schema.objects.filter(
                            schema_id=schema.schema_id
                        )[0]
                        i.save()

            return HttpResponseRedirect(reverse_lazy("home"))
        else:
            return self.render_to_response(self.get_context_data(form=form))


class SchemaDeleteView(DeleteView):
    model = Schema
    pk_url_kwarg = "schema_id"
    success_url = reverse_lazy("home")
    template_name = "schema_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super(SchemaDeleteView, self).get_context_data(**kwargs)
        context["schema"] = kwargs["object"]
        return context


class FileDownloadView(View):
    folder_path = settings.FILE_STORAGE_PATH
    file_name = ""
    content_type_value = "application/force-download"

    def get(self, request, schema_id, dataset_id):
        self.file_name = (
            "schema_" + str(schema_id) + "dataset_" + str(dataset_id) + ".csv"
        )

        filepath = self.file_name
        with default_storage.open(filepath, "rb") as fh:
            response = HttpResponse(fh.read(), content_type=self.content_type_value)
            response[
                "Content-Disposition"
            ] = "inline; filename=" + filepath
        return response
