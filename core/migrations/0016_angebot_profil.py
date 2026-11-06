# Absenderprofil für Angebote (Schema von Django erzeugt) + bestehende Angebote
# erhalten das Standardprofil.
import django.db.models.deletion
from django.db import migrations, models


def profil_zuweisen(apps, schema_editor):
    Absenderprofil = apps.get_model('core', 'Absenderprofil')
    Angebot = apps.get_model('core', 'Angebot')
    profil = Absenderprofil.objects.filter(ist_standard=True).first() or Absenderprofil.objects.first()
    if profil is not None:
        Angebot.objects.filter(absenderprofil__isnull=True).update(absenderprofil=profil)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_absenderprofil_sperre'),
    ]

    operations = [
        migrations.AddField(
            model_name='angebot',
            name='absenderprofil',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='angebote', to='core.absenderprofil', verbose_name='Absenderprofil'),
        ),
        migrations.RunPython(profil_zuweisen, migrations.RunPython.noop),
    ]
