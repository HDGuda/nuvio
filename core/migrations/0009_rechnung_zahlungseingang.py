from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_einstellungen_email_gutschrift_anhang1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rechnung',
            name='bezahlt_am',
            field=models.DateField(blank=True, null=True, verbose_name='Bezahlt am'),
        ),
        migrations.AddField(
            model_name='rechnung',
            name='bezahlt_betrag',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Bezahlter Betrag'),
        ),
        migrations.AlterField(
            model_name='rechnung',
            name='status',
            field=models.CharField(
                choices=[
                    ('entwurf',            'Entwurf'),
                    ('gesendet',           'Gesendet'),
                    ('bezahlt',            'Bezahlt'),
                    ('teilbezahlt',        'Teilbezahlt'),
                    ('ueberfaellig',       'Überfällig'),
                    ('storniert',          'Storniert'),
                    ('teilgutgeschrieben', 'Teilgutgeschrieben'),
                ],
                default='entwurf',
                max_length=20,
                verbose_name='Status',
            ),
        ),
    ]
