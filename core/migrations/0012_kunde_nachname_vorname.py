# Migration: core/migrations/XXXX_kunde_nachname_vorname.py
#
# Diese Datei als nächste Migration in core/migrations/ ablegen.
# Dateiname anpassen: z.B. 0002_kunde_nachname_vorname.py
# (vorherige Nummer ermitteln mit: python manage.py showmigrations core)

from django.db import migrations, models


class Migration(migrations.Migration):

    # Abhängigkeit anpassen – z.B. '0001_initial' durch die tatsächlich
    # letzte vorhandene Migration ersetzen.
    dependencies = [
        ('core', '0011_zahlung'),
    ]

    operations = [
        # 1. Neue Felder hinzufügen (noch nullable, damit bestehende Zeilen passen)
        migrations.AddField(
            model_name='kunde',
            name='nachname',
            field=models.CharField(max_length=100, verbose_name='Nachname', default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kunde',
            name='vorname',
            field=models.CharField(max_length=100, verbose_name='Vorname', blank=True, default=''),
            preserve_default=False,
        ),

        # 2. Bestehende Daten übertragen:
        #    Der bisherige „ansprechpartner"-Wert wird komplett in „nachname" geschrieben.
        #    Wer Vor- und Nachname trennen möchte, kann das danach manuell im Admin tun.
        migrations.RunSQL(
            sql="UPDATE core_kunde SET nachname = ansprechpartner WHERE nachname = ''",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 3. Altes Feld entfernen
        migrations.RemoveField(
            model_name='kunde',
            name='ansprechpartner',
        ),

        # 4. Sortierung aktualisieren
        migrations.AlterModelOptions(
            name='kunde',
            options={
                'ordering': ['firma', 'nachname', 'vorname'],
                'verbose_name': 'Kunde',
                'verbose_name_plural': 'Kunden',
            },
        ),
    ]
