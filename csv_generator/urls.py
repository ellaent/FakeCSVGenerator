from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    DataSetListView,
    FileDownloadView,
    SchemaCreateView,
    SchemaDeleteView,
    SchemaListView,
    SchemaUpdateView,
)

urlpatterns = [
    path("", SchemaListView.as_view(), name="home"),
    path("schemas/create/", SchemaCreateView.as_view(), name="schema_create"),
    path("schemas/<int:schema_id>/$", DataSetListView.as_view(), name="schema_detail"),
    path(
        "schemas/<int:schema_id>/edit/$", SchemaUpdateView.as_view(), name="schema_edit"
    ),
    path(
        "schemas/<int:schema_id>/delete/$",
        SchemaDeleteView.as_view(),
        name="schema_delete",
    ),
    path(
        "datasets/schema_<int:schema_id>dataset_<int:dataset_id>/download/$",
        FileDownloadView.as_view(),
        name="dataset_download",
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
