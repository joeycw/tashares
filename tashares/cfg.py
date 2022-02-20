from pathlib import Path
from configparser import ConfigParser, ExtendedInterpolation

config_dir = Path(__file__).parent
config_path = config_dir / 'cfg.ini'
config = ConfigParser(
    allow_no_value=False,     # don't allow "key" without "="
    delimiters=('=',),        # inifile "=" between key and value
    interpolation=ExtendedInterpolation(),)
config.read(config_path)
