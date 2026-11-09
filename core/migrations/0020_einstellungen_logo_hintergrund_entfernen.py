from django.db import migrations


class Migration(migrations.Migration):
    """
    Logo und Briefpapier werden pro Absenderprofil gepflegt (seit 0015). Die ungenutzten
    Felder am Modell Einstellungen entfallen. Die hochgeladenen Dateien im Media-Ordner
    bleiben unberührt; nur die Verweise in der Tabelle Einstellungen werden entfernt.
    """

    dependencies = [
        ('core', '0019_gutschrift_sperre'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='einstellungen',
            name='hintergrund_pdf',
        ),
        migrations.RemoveField(
            model_name='einstellungen',
            name='logo',
        ),
    ]
