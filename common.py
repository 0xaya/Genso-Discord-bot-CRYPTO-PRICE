import datetime
import decimal
from decimal import localcontext

def output_log(str):
    print(f'{datetime.datetime.now().strftime("%H:%M:%S")} {str}')


def get_color_from_rarity(rarity):
    if rarity == 'normal':
        color = 0xb7b7b7
    elif rarity == 'rare':
        color = 0x251bdf
    elif rarity == 'super_rare':
        color = 0xa459d3
    elif rarity == 'legend':
        color = 0xd2af3f
    else:
        color = 0x000000
    return color


def is_float(s):
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True


def is_int(s):
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True


def convert_value(number: int):
    unit_value = decimal.Decimal('1000000000000000000')

    with localcontext() as ctx:
        ctx.prec = 999
        d_number = decimal.Decimal(value=number, context=ctx)
        result_value = d_number / unit_value
    return result_value
