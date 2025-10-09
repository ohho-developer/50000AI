# Manual migration to install pgvector extension

from django.db import migrations


def install_vector_extension(apps, schema_editor):
    """pgvector 확장 설치"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")


def uninstall_vector_extension(apps, schema_editor):
    """pgvector 확장 제거 (롤백용)"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP EXTENSION IF EXISTS vector")


class Migration(migrations.Migration):
    atomic = False  # DDL 명령어는 atomic하지 않게

    dependencies = [
        ('nutrients_codi', '0008_delete_dailyreport'),
    ]

    operations = [
        migrations.RunPython(install_vector_extension, uninstall_vector_extension),
    ]

