import csv

from celery import shared_task
from celery.utils.log import get_task_logger
from celery_progress.backend import ProgressRecorder
from django.conf import settings
from django.core.files.storage import default_storage
from faker import Faker

from FakeCSV.celery import app

from .models import Column, DataSet

logger = get_task_logger(__name__)


@shared_task(bind=True)
def generate_fake_csv(self, dataset_id):
    fake = Faker()
    progress_recorder = ProgressRecorder(self)
    logger.info(f"Task started")
    dataset = DataSet.objects.filter(dataset_id=dataset_id).first()
    if not dataset:
        return

    schema = dataset.schema
    columns = Column.objects.filter(schema=schema).order_by("order").values()

    if schema.column_separator == "Comma":
        delimeter = ","
    elif schema.column_separator == "Semicolon":
        delimeter = ";"
    elif schema.column_separator == "Tab":
        delimeter = "\t"
    elif schema.column_separator == "Space":
        delimeter = " "
    elif schema.column_separator == "Pipe":
        delimeter = "|"
    else:
        delimeter = None

    row_number = dataset.rows
    header = []
    all_rows = []
    for column in columns:
        header.append(column["name"])
    i = 0
    for row in range(row_number):
        raw_row = []
        i += 1
        progress_recorder.set_progress(i, row_number + 1)
        for column in columns:
            column_type = column["type"]
            if column_type == "Full Name":
                data = fake.name()
            elif column_type == "Job":
                data = fake.job()
            elif column_type == "Email":
                data = fake.email()
            elif column_type == "Domain name":
                data = fake.domain_name()
            elif column_type == "Phone number":
                data = fake.phone_number()
            elif column_type == "Company name":
                data = fake.company()
            elif column_type == "Text":
                data = fake.sentences(
                    nb=fake.random_int(
                        min=column["from_range"] or 1, max=column["to_range"] or 20
                    )
                )
                data = " ".join(data)

            elif column_type == "Integer":
                data = fake.random_int(
                    min=column["from_range"] or 0, max=column["to_range"] or 99999
                )
            elif column_type == "Address":
                data = fake.address()
            elif column_type == "Date":
                data = fake.date()
            else:
                data = None
            raw_row.append(data)
        all_rows.append(raw_row)

    with default_storage.open(
        f"schema_{schema.schema_id}dataset_{dataset_id}.csv", "w"
    ) as csvfile:
        writer = csv.writer(
            csvfile, delimiter=delimeter, quotechar='"', quoting=csv.QUOTE_ALL
        )
        writer.writerow(header)
        writer.writerows(all_rows)

    dataset.status = "Ready"
    dataset.save()
    progress_recorder.set_progress(row_number + 1, row_number + 1)
