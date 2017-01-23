import django
django.setup()

from prices import Price
from decimal import Decimal
import pytest

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command

from django_prices_vatlayer import utils
from django_prices_vatlayer.models import VAT


@pytest.fixture
def vat_country(db, json_success):
    data = json_success['rates']['AT']
    return VAT.objects.create(country_code='AT', data=data)


@pytest.fixture
def vat_without_rates(db):
    return VAT.objects.create(country_code='AU', data={})


@pytest.fixture
def fetch_vat_rates_success(monkeypatch, json_success):
    monkeypatch.setattr(utils, 'fetch_vat_rates',
                        lambda: json_success)


@pytest.fixture
def fetch_vat_rates_error(monkeypatch, json_error):
    monkeypatch.setattr(utils, 'fetch_vat_rates',
                        lambda: json_error)


def test_validate_data_invalid(json_error):
    with pytest.raises(ImproperlyConfigured):
        utils.validate_data(json_error)


def test_validate_data_valid(json_success):
    assert utils.validate_data(json_success) is None


@pytest.mark.django_db
def test_create_objects_from_json(json_error, json_success):

    vat_counts = VAT.objects.count()

    with pytest.raises(ImproperlyConfigured):
        utils.create_objects_from_json(json_error)

    utils.create_objects_from_json(json_success)
    assert vat_counts + 1 == VAT.objects.count()


@pytest.mark.parametrize('rate_name,expected',
                         [('medicine', Decimal(20)), ('books', Decimal(10)),
                          (None, Decimal(20))])
def test_get_tax_for_country(vat_country, rate_name, expected):
    country_code = vat_country.country_code
    rate = utils.get_tax_for_country(country_code, rate_name)
    assert rate == expected


@pytest.mark.django_db
def test_get_tax_for_country_error():
    rate = utils.get_tax_for_country('XX', 'rate name')
    assert rate is None


@pytest.mark.django_db
def test_get_vat_rates_command(monkeypatch, fetch_vat_rates_success):

    call_command('get_vat_rates')
    assert 1 == VAT.objects.count()


@pytest.mark.django_db
def test_get_vat_rates_command(monkeypatch, fetch_vat_rates_error):

    with pytest.raises(ImproperlyConfigured):
        call_command('get_vat_rates')
