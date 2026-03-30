import pytest
from src.send_msg import check_templates
from pathlib import Path
import pandas as pd


def test_templates():
    assert check_templates("metamorfose_template3")