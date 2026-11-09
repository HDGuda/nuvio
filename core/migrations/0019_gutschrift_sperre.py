from django.db import migrations, models
from django.utils import timezone


def bestehende_dokumente_sperren(apps, schema_editor):
    """GoBD: alles, was nicht mehr Entwurf ist, gilt als versendet und wird gesperrt."""
    jetzt = timezone.now()
    for name in ('Rechnung', 'Gutschrift'):
        Modell = apps.get_model('core', name)
        Modell.objects.exclude(status='entwurf').filter(gesperrt_am__isnull=True).update(gesperrt_am=jetzt)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_thunderbird_identitaet'),
    ]

    operations = [
        migrations.AddField(
            model_name='gutschrift',
            name='gesperrt_am',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Gesperrt am'),
        ),
        migrations.AddField(
            model_name='gutschrift',
            name='pdf_archiv',
            field=models.FileField(blank=True, editable=False, null=True, upload_to='gutschriften_archiv/', verbose_name='Archiviertes PDF'),
        ),
        migrations.RunPython(bestehende_dokumente_sperren, migrations.RunPython.noop),
    ]
