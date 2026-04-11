from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_angebot_gesendet_am_rechnung_gesendet_am'),
    ]

    operations = [
        migrations.CreateModel(
            name='Zahlung',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.DateField(verbose_name='Zahlungsdatum')),
                ('betrag', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Betrag (€)')),
                ('erstellt_am', models.DateTimeField(auto_now_add=True)),
                ('rechnung', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zahlungen',
                    to='core.rechnung',
                    verbose_name='Rechnung',
                )),
            ],
            options={
                'verbose_name': 'Zahlung',
                'verbose_name_plural': 'Zahlungen',
                'ordering': ['datum', 'erstellt_am'],
            },
        ),
    ]
