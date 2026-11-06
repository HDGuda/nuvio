# Absenderprofil, GoBD-Sperre und Archiv-PDF für Rechnungen.
# Schema (von Django erzeugt) + Datenübernahme in einer Datei.
# Die Abhängigkeit ist die jeweils vorherige Migration (höchste Nummer unter 0016).
import os
import re

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone

_ordner = os.path.dirname(os.path.abspath(__file__))
_eigene = os.path.splitext(os.path.basename(__file__))[0]
_vorherige = sorted(
    f[:-3] for f in os.listdir(_ordner)
    if re.fullmatch(r'\d{4}_\w+\.py', f) and f[:-3] < _eigene
)


def daten_uebernehmen(apps, schema_editor):
    Einstellungen = apps.get_model('core', 'Einstellungen')
    Absenderprofil = apps.get_model('core', 'Absenderprofil')
    Rechnung = apps.get_model('core', 'Rechnung')

    e = Einstellungen.objects.filter(pk=1).first()
    if e is None:
        return
    profil = Absenderprofil.objects.filter(ist_standard=True).first()
    if profil is None:
        ort_zeile = f'{e.plz} {e.ort}'.strip()
        profil = Absenderprofil.objects.create(
            name='Standard', ist_standard=True, firmenname=e.firma_name,
            logo=e.logo.name if e.logo else '', logo_position='rechts',
            kopf_links='\n'.join(z for z in [e.firma_zusatz, e.firma_zusatz2, e.strasse, ort_zeile, e.email] if z),
            absenderzeile=' · '.join(t for t in [e.firma_name, e.strasse, ort_zeile] if t),
            hintergrund_pdf=e.hintergrund_pdf.name if e.hintergrund_pdf else None,
            email=e.email,
        )
    # alle bisherigen Rechnungen bekommen das Standardprofil
    Rechnung.objects.filter(absenderprofil__isnull=True).update(absenderprofil=profil)
    # bereits bezahlte Rechnungen werden gesperrt
    Rechnung.objects.filter(status='bezahlt', gesperrt_am__isnull=True).update(gesperrt_am=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('core', _vorherige[-1]),
    ]

    operations = [
        migrations.CreateModel(
            name='Absenderprofil',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Bezeichnung (intern)')),
                ('ist_standard', models.BooleanField(default=False, help_text='Wird bei neuen Rechnungen vorausgewählt. Es gibt genau ein Standardprofil.', verbose_name='Standardprofil')),
                ('firmenname', models.CharField(blank=True, help_text='Fettgedruckt im Briefkopf und Platzhalter {{firma}} in E-Mails. Leer = Firmenname aus den Einstellungen.', max_length=200, verbose_name='Firmenname im Dokument')),
                ('logo', models.ImageField(blank=True, upload_to='logo/', verbose_name='Logo')),
                ('logo_position', models.CharField(choices=[('links', 'Links'), ('rechts', 'Rechts')], default='rechts', max_length=10, verbose_name='Logo-Position')),
                ('kopf_links', models.TextField(blank=True, help_text='Mehrzeilig, z. B. Zusatzzeilen, Straße, Ort, E-Mail.', verbose_name='Briefkopf links')),
                ('kopf_rechts', models.TextField(blank=True, help_text='Mehrzeilig, rechtsbündig. Darf leer sein.', verbose_name='Briefkopf rechts')),
                ('absenderzeile', models.CharField(blank=True, help_text='Kleine Zeile im Adressfenster, z. B. "Name · Straße · PLZ Ort".', max_length=200, verbose_name='Absenderzeile über der Empfängeradresse')),
                ('hintergrund_pdf', models.FileField(blank=True, null=True, upload_to='hintergrund/', verbose_name='Hintergrund-PDF (Briefpapier)')),
                ('unterer_rand_mm', models.PositiveSmallIntegerField(default=28, help_text='Muss zur Fußzeile des Briefpapiers passen.', verbose_name='Unterer Seitenrand mit Briefpapier (mm)')),
                ('email', models.EmailField(blank=True, help_text='Leer = E-Mail-Adresse aus den Einstellungen.', max_length=254, verbose_name='Absender-E-Mail (Outlook-Konto)')),
            ],
            options={
                'verbose_name': 'Absenderprofil',
                'verbose_name_plural': 'Absenderprofile',
                'ordering': ['-ist_standard', 'name'],
            },
        ),
        migrations.AddField(
            model_name='rechnung',
            name='gesperrt_am',
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Gesperrt am'),
        ),
        migrations.AddField(
            model_name='rechnung',
            name='pdf_archiv',
            field=models.FileField(blank=True, editable=False, null=True, upload_to='rechnungen_archiv/', verbose_name='Archiviertes PDF'),
        ),
        migrations.AddField(
            model_name='rechnung',
            name='absenderprofil',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rechnungen', to='core.absenderprofil', verbose_name='Absenderprofil'),
        ),
        migrations.RunPython(daten_uebernehmen, migrations.RunPython.noop),
    ]
