'''
Utilities useful for defining models.
'''
from enum import Enum


class AutoNamedEnum(str, Enum):
    ''' An enum that automatically uses the enum name for as its value '''
    # pylint:disable=unused-argument,no-self-argument
    def _generate_next_value_(name, start, count, last_values):
        ''' The value of the enum is always its name '''
        return name
    # pylint:enable=unused-argument,no-self-argument
