""""
Test custom Django Management commands.
"""""
import django
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase

@patch('core.management.commands.wait_fordb.Command.check')
class CommandTests(SimpleTestCase):
    """Test Commands"""
    def test_wait_for_db_ready(self, patched_check):

        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(database=['default'])
