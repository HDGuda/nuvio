# Absenderprofil für Gutschriften (Schema von Django erzeugt). Bestehende Gutschriften
# erhalten das Profil ihrer Rechnung, sonst das Standardprofil.
import django.db.models.deletion
from django.db import migrations, models


def profil_zuweisen(apps, schema_editor):
    Absenderprofil = apps.get_model('core', 'Absenderprofil')
    Gutschrift = apps.get_model('core', 'Gutschrift')
    standard = Absenderprofil.objects.filter(ist_standard=True).first() or Absenderprofil.objects.first()
    for g in Gutschrift.objects.filter(absenderprofil__isnull=True).select_related('rechnung'):
        profil_id = g.rechnung.absenderprofil_id if g.rechnung_id and g.rechnung.absenderprofil_id else (standard.pk if standard else None)
        if profil_id:
            Gutschrift.objects.filter(pk=g.pk).update(absenderprofil_id=profil_id)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_angebot_profil'),
    ]

    operations = [
        migrations.AddField(
            model_name='gutschrift',
            name='absenderprofil',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='gutschriften', to='core.absenderprofil', verbose_name='Absenderprofil'),
        ),
        migrations.RunPython(profil_zuweisen, migrations.RunPython.noop),
    ]
