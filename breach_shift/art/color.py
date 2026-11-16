"""Match flat atmosphere colors to simplepbr's filmic output."""
from math import sqrt


def atmosphere_input(rgb):
    """Invert the pipeline's filmic curve for a desired display RGB color."""
    result = []
    for value in rgb:
        value = max(0.0, min(.999, value))
        a, b = 6.2 * (1 - value), .5 - 1.7 * value
        linear = (-b + sqrt(b * b + 4 * a * .06 * value)) / (2 * a)
        result.append(linear + .004)
    return tuple(result)
