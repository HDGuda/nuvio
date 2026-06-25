from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_kunde_nachname_vorname'),
    ]

    operations = [
        migrations.AddField(
            model_name='artikel',
            name='is_bundle',
            field=models.BooleanField(
                default=False,
                verbose_name='Bundle (Paketartikel)',
                help_text='Wenn aktiv, werden beim Einfügen in ein Angebot automatisch '
                          'alle Einzelartikel dieses Bundles eingefügt.'
            ),
        ),
        migrations.CreateModel(
            name='ArtikelBundlePosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('menge', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Menge')),
                ('reihenfolge', models.PositiveIntegerField(default=0, verbose_name='Reihenfolge')),
                ('artikel', models.ForeignKey(
                    limit_choices_to={'aktiv': True, 'is_bundle': False},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='in_bundles',
                    to='core.artikel',
                    verbose_name='Einzelartikel',
                )),
                ('bundle', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bundle_positionen',
                    to='core.artikel',
                    verbose_name='Bundle-Artikel',
                )),
            ],
            options={
                'verbose_name': 'Bundle-Position',
                'verbose_name_plural': 'Bundle-Positionen',
                'ordering': ['reihenfolge'],
            },
        ),
    ]
